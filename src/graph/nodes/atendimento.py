"""Agente de Atendimento: dúvidas e recomendações do cardápio (Pessoa 2).

Etapas: 2.4 interpretar as preferências (FiltroCardapio); 2.5 consultar o cardápio no MCP.

As dependências externas (LLM e cliente MCP) podem ser passadas por parâmetro. Assim os
testes usam falsos e nunca chamam o modelo nem o servidor de verdade.
"""

import logging

from pydantic import ValidationError

from src.graph.prompts.interpretar_preferencias_prompt import INTERPRETAR_PREFERENCIAS_PROMPT
from src.schemas.filtro_cardapio import FiltroCardapio

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
