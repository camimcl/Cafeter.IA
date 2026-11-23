"""Agente de Atendimento: dúvidas e recomendações do cardápio (Pessoa 2).

Etapas: 2.4 interpretar as preferências (FiltroCardapio); 2.5 consultar o cardápio no MCP;
2.6 escrever a recomendação só com os produtos devolvidos. O nó do grafo é `atendimento`.

As dependências externas (LLM e cliente MCP) podem ser passadas por parâmetro. Assim os
testes usam falsos e nunca chamam o modelo nem o servidor de verdade.
"""

import logging

from pydantic import ValidationError

from src.graph.prompts.atendimento_prompt import ATENDIMENTO_PROMPT
from src.graph.prompts.interpretar_preferencias_prompt import INTERPRETAR_PREFERENCIAS_PROMPT
from src.graph.state import State
from src.schemas.filtro_cardapio import FiltroCardapio
from src.utils.valores import formatar_valor

logger = logging.getLogger(__name__)


def _obter_llm():
    """Busca o LLM do adaptador só na hora do uso (o adaptador carrega o langchain)."""
    from src.utils.llm_adapter import get_llm

    return get_llm()


async def interpretar_preferencias(mensagem: str, llm=None) -> FiltroCardapio:
    """Transforma a frase do cliente em filtros do cardápio, com saída estruturada do LLM.

    Se o LLM falhar ou devolver algo fora do contrato, segue sem filtros: o cliente vê o
    cardápio e pode refinar a pergunta, em vez de a conversa quebrar.
    """
    if llm is None:
        llm = _obter_llm()

    estruturado = llm.with_structured_output(FiltroCardapio)
    mensagens = [("system", INTERPRETAR_PREFERENCIAS_PROMPT), ("human", mensagem)]

    try:
        resultado = await estruturado.ainvoke(mensagens)
        if isinstance(resultado, FiltroCardapio):
            return resultado
        return FiltroCardapio.model_validate(resultado)
    except ValidationError:
        logger.warning("Resposta do LLM fora do FiltroCardapio; seguindo sem filtros.")
    except Exception:
        logger.warning("Falha ao interpretar preferências; seguindo sem filtros.", exc_info=True)

    return FiltroCardapio()


# --- etapa 2.5: consultar o cardápio pelo MCP ---

MENSAGEM_SERVICO_FORA_DO_AR = (
    "Nosso cardápio está fora do ar no momento. Tente de novo em alguns instantes, por favor."
)
MENSAGEM_ERRO_NA_CONSULTA = (
    "Tive um problema para consultar o cardápio agora. Pode tentar de novo, por favor?"
)


def _obter_chamar_ferramenta():
    """Busca o cliente MCP só na hora do uso (dono: Pessoa 4)."""
    from src.utils.mcp_client import chamar_ferramenta

    return chamar_ferramenta


async def consultar_produtos(filtro: FiltroCardapio, chamar_ferramenta=None) -> dict:
    """Consulta o cardápio no MCP com os filtros preenchidos. Devolve a resposta do contrato.

    Campos vazios não são enviados: para o servidor, "ausente" já significa "não filtre".
    """
    if chamar_ferramenta is None:
        chamar_ferramenta = _obter_chamar_ferramenta()

    return await chamar_ferramenta("consultar_cardapio", filtro.model_dump(exclude_none=True))


def mensagem_de_erro(resposta: dict) -> str:
    """Traduz um erro do MCP em mensagem amigável; o detalhe técnico vai só para o log."""
    erro = resposta.get("erro", {})
    logger.warning("consultar_cardapio falhou: %s - %s", erro.get("codigo"), erro.get("mensagem"))

    if erro.get("codigo") == "MCP_INDISPONIVEL":
        return MENSAGEM_SERVICO_FORA_DO_AR
    return MENSAGEM_ERRO_NA_CONSULTA


# --- etapa 2.6: escrever a recomendação ---

MENSAGEM_NADA_ENCONTRADO = (
    "Não encontrei nenhum produto com essas características. "
    "Quer mudar algum critério, como a temperatura ou o preço?"
)
LISTA_VAZIA = "(lista vazia: nenhum produto do cardápio combina com o pedido)"


def formatar_produto(produto: dict) -> str:
    """Descreve um produto em uma linha, com preços já em reais (o LLM não faz conta)."""
    caracteristicas = [produto["temperatura"], "doce" if produto["doce"] else "não doce"]
    if produto["sem_lactose"]:
        caracteristicas.append("sem lactose")

    alergenos = ", ".join(produto["alergenos"]) or "nenhum informado"
    linha = (
        f"- {produto['nome']}: {produto['descricao']} "
        f"Preço: {formatar_valor(produto['preco_centavos'])}. "
        f"Características: {', '.join(caracteristicas)}. Alérgenos: {alergenos}."
    )

    personalizacoes = []
    for personalizacao in produto["personalizacoes"]:
        detalhe = f"+ {formatar_valor(personalizacao['acrescimo_centavos'])}"
        if personalizacao.get("torna_sem_lactose"):
            detalhe += ", deixa sem lactose"
        personalizacoes.append(f"{personalizacao['nome']} ({detalhe})")
    if personalizacoes:
        linha += f" Personalizações: {'; '.join(personalizacoes)}."

    return linha


def formatar_lista_de_produtos(produtos: list[dict]) -> str:
    """Monta a lista de produtos enviada ao LLM, uma linha por produto."""
    if not produtos:
        return LISTA_VAZIA
    return "\n".join(formatar_produto(produto) for produto in produtos)


def _opcao_resumida(produto: dict) -> str:
    """Nome e preço; se só fica sem lactose com personalização, diz qual (contrato 3.1)."""
    texto = f"{produto['nome']} ({formatar_valor(produto['preco_centavos'])}"
    if not produto["sem_lactose"]:
        sem_lactose = [p["nome"] for p in produto["personalizacoes"] if p.get("torna_sem_lactose")]
        if sem_lactose:
            texto += f"; sem lactose com {' ou '.join(sem_lactose)}"
    return texto + ")"


def _resposta_sem_llm(produtos: list[dict]) -> str:
    """Resposta simples, montada em Python, para quando o LLM não responde."""
    if not produtos:
        return MENSAGEM_NADA_ENCONTRADO
    opcoes = ", ".join(_opcao_resumida(produto) for produto in produtos)
    return f"Encontrei estas opções no cardápio: {opcoes}."


async def escrever_recomendacao(mensagem: str, produtos: list[dict], llm=None) -> str:
    """Pede ao LLM a resposta ao cliente, usando só os produtos que vieram do MCP."""
    if llm is None:
        llm = _obter_llm()

    conteudo = (
        f"Mensagem do cliente: {mensagem}\n\n"
        f"Lista de produtos:\n{formatar_lista_de_produtos(produtos)}"
    )
    mensagens = [("system", ATENDIMENTO_PROMPT), ("human", conteudo)]

    try:
        resposta = await llm.ainvoke(mensagens)
        return resposta.content
    except Exception:
        logger.warning("Falha ao escrever a recomendação; respondendo sem o LLM.", exc_info=True)
        return _resposta_sem_llm(produtos)


async def atender(mensagem: str, llm=None, chamar_ferramenta=None) -> dict:
    """Caminho completo do atendimento: interpretar, consultar o cardápio e recomendar."""
    if llm is None:
        llm = _obter_llm()

    filtro = await interpretar_preferencias(mensagem, llm)
    filtros_cardapio = filtro.model_dump(exclude_none=True)

    resposta_mcp = await consultar_produtos(filtro, chamar_ferramenta)
    if not resposta_mcp.get("ok"):
        return {"filtros_cardapio": filtros_cardapio, "resposta": mensagem_de_erro(resposta_mcp)}

    produtos = resposta_mcp["dados"]["produtos"]
    texto = await escrever_recomendacao(mensagem, produtos, llm)
    return {"filtros_cardapio": filtros_cardapio, "resposta": texto}


async def atendimento(state: State) -> dict:
    """Nó do grafo: responde dúvidas e recomendações. Devolve só os campos que mudaram."""
    return await atender(state["mensagem"])
