"""Testes da recomendação e do nó de atendimento completo (etapa 2.6).

LLM e cliente MCP são falsos: nada sai da máquina. Os produtos vêm do cardápio real
(dados/cardapio.json), para a formatação bater com o que o cliente vai ver.
"""

import asyncio
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from src.graph.nodes import atendimento
from src.graph.prompts.atendimento_prompt import ATENDIMENTO_PROMPT
from src.schemas.filtro_cardapio import FiltroCardapio

CARDAPIO = json.loads(
    (Path(__file__).resolve().parent.parent / "dados" / "cardapio.json").read_text("utf-8")
)["produtos"]
PRODUTOS = {produto["id"]: produto for produto in CARDAPIO}


class LlmFalso:
    """Faz as duas chamadas do atendimento: filtro estruturado e texto da recomendação."""

    def __init__(self, filtro=None, texto="Recomendo o cappuccino!", falhar_texto=False):
        self.filtro = filtro or FiltroCardapio()
        self.texto = texto
        self.falhar_texto = falhar_texto
        self.mensagens_texto = []

    def with_structured_output(self, schema):
        filtro = self.filtro

        class Estruturado:
            async def ainvoke(self, mensagens):
                return filtro

        return Estruturado()

    async def ainvoke(self, mensagens):
        self.mensagens_texto.append(mensagens)
        if self.falhar_texto:
            raise RuntimeError("modelo fora do ar")
        return SimpleNamespace(content=self.texto)


class ClienteMcpFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.chamadas = []

    async def __call__(self, nome, argumentos):
        self.chamadas.append((nome, argumentos))
        return self.resposta


def mcp_com(*ids):
    return ClienteMcpFalso({"ok": True, "dados": {"produtos": [PRODUTOS[i] for i in ids]}})


# --- formatação da lista de produtos enviada ao LLM ---


def test_produto_mostra_nome_descricao_e_preco_em_reais():
    texto = atendimento.formatar_produto(PRODUTOS["cappuccino"])

    assert "Cappuccino" in texto
    assert PRODUTOS["cappuccino"]["descricao"] in texto
    assert "R$ 14,00" in texto
    assert "1400" not in texto  # o LLM nunca vê centavos: ele não deve converter nada


def test_personalizacao_que_tira_a_lactose_e_sinalizada():
    texto = atendimento.formatar_produto(PRODUTOS["cappuccino"])

    assert "Leite de aveia (+ R$ 3,00, deixa sem lactose)" in texto
    assert "Shot extra de espresso (+ R$ 4,00)" in texto


def test_produto_sem_lactose_e_alergenos_aparecem():
    assert "sem lactose" in atendimento.formatar_produto(PRODUTOS["espresso"])
    assert "Alérgenos: leite" in atendimento.formatar_produto(PRODUTOS["cappuccino"])
    assert "Alérgenos: nenhum informado" in atendimento.formatar_produto(PRODUTOS["espresso"])


def test_lista_vazia_e_escrita_como_lista_vazia():
    assert "lista vazia" in atendimento.formatar_lista_de_produtos([])


def test_lista_tem_uma_linha_por_produto():
    texto = atendimento.formatar_lista_de_produtos([PRODUTOS["espresso"], PRODUTOS["latte"]])

    assert texto.count("\n") == 1
    assert texto.startswith("- Espresso")


# --- escrita da recomendação (segunda chamada ao LLM) ---


def test_recomendacao_envia_o_prompt_do_atendente_a_mensagem_e_a_lista():
    llm = LlmFalso()

    asyncio.run(atendimento.escrever_recomendacao("algo quente", [PRODUTOS["latte"]], llm))

    sistema, humano = llm.mensagens_texto[0]
    assert sistema == ("system", ATENDIMENTO_PROMPT)
    assert humano[0] == "human"
    assert "algo quente" in humano[1]
    assert atendimento.formatar_produto(PRODUTOS["latte"]) in humano[1]


def test_recomendacao_devolve_o_texto_do_llm():
    llm = LlmFalso(texto="O latte é uma ótima escolha!")

    resposta = asyncio.run(atendimento.escrever_recomendacao("oi", [PRODUTOS["latte"]], llm))

    assert resposta == "O latte é uma ótima escolha!"


def test_llm_fora_do_ar_responde_com_a_lista_sem_inventar_nada():
    llm = LlmFalso(falhar_texto=True)
    produtos = [PRODUTOS["espresso"], PRODUTOS["latte"]]

    resposta = asyncio.run(atendimento.escrever_recomendacao("oi", produtos, llm))

    assert "Espresso (R$ 7,00)" in resposta
    assert "Latte (R$ 15,00" in resposta


def test_llm_fora_do_ar_diz_qual_personalizacao_tira_a_lactose():
    # Regra do contrato (seção 3.1): o chocolate gelado só é sem lactose com leite de aveia.
    llm = LlmFalso(falhar_texto=True)

    resposta = asyncio.run(
        atendimento.escrever_recomendacao("oi", [PRODUTOS["chocolate_gelado"]], llm)
    )

    assert "Chocolate gelado (R$ 15,00; sem lactose com Leite de aveia)" in resposta


def test_llm_fora_do_ar_e_lista_vazia_pede_para_mudar_criterio():
    llm = LlmFalso(falhar_texto=True)

    resposta = asyncio.run(atendimento.escrever_recomendacao("oi", [], llm))

    assert resposta == atendimento.MENSAGEM_NADA_ENCONTRADO


# --- nó completo: interpretar, consultar, recomendar ---


def test_atender_faz_o_caminho_completo():
    filtro = FiltroCardapio(temperatura="gelado", doce=True)
    llm = LlmFalso(filtro=filtro, texto="Que tal um chocolate gelado?")
    mcp = mcp_com("chocolate_gelado")

    resultado = asyncio.run(atendimento.atender("algo gelado e doce", llm, mcp))

    assert mcp.chamadas == [("consultar_cardapio", {"temperatura": "gelado", "doce": True})]
    assert resultado == {
        "filtros_cardapio": {"temperatura": "gelado", "doce": True},
        "resposta": "Que tal um chocolate gelado?",
    }


def test_atender_com_servidor_fora_do_ar_avisa_e_nao_chama_o_llm_de_novo():
    llm = LlmFalso()
    erro = {"codigo": "MCP_INDISPONIVEL", "mensagem": "Connection refused"}
    mcp = ClienteMcpFalso({"ok": False, "erro": erro})

    resultado = asyncio.run(atendimento.atender("quero um café", llm, mcp))

    assert resultado["resposta"] == atendimento.MENSAGEM_SERVICO_FORA_DO_AR
    assert llm.mensagens_texto == []  # economiza uma requisição do limite diário


def test_no_atendimento_le_a_mensagem_do_estado(monkeypatch):
    llm = LlmFalso(texto="Temos pão de queijo!")
    mcp = mcp_com("pao_de_queijo")
    adaptador = types.ModuleType("src.utils.llm_adapter")
    adaptador.get_llm = lambda: llm
    cliente = types.ModuleType("src.utils.mcp_client")
    cliente.chamar_ferramenta = mcp
    monkeypatch.setitem(sys.modules, "src.utils.llm_adapter", adaptador)
    monkeypatch.setitem(sys.modules, "src.utils.mcp_client", cliente)

    resultado = asyncio.run(atendimento.atendimento({"mensagem": "algo para comer"}))

    assert resultado["resposta"] == "Temos pão de queijo!"
    assert "algo para comer" in llm.mensagens_texto[0][1][1]
