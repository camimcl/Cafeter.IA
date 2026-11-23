"""Testes da interpretação de preferências (etapa 2.4).

O LLM é substituído por um falso: os testes conferem o que enviamos a ele e o que fazemos
com a resposta, sem nenhuma chamada real (testes do projeto são offline).
"""

import asyncio
import logging
import sys
import types

from src.graph.nodes import atendimento
from src.graph.prompts.interpretar_preferencias_prompt import INTERPRETAR_PREFERENCIAS_PROMPT
from src.schemas.filtro_cardapio import FiltroCardapio


class LlmFalso:
    """Imita o pedaço do LLM que usamos: with_structured_output(...).ainvoke(...)."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.schema = None
        self.mensagens = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    async def ainvoke(self, mensagens):
        self.mensagens = mensagens
        if isinstance(self.resposta, Exception):
            raise self.resposta
        return self.resposta


def interpretar(mensagem, llm):
    return asyncio.run(atendimento.interpretar_preferencias(mensagem, llm=llm))


def test_pede_saida_estruturada_no_formato_do_filtro():
    llm = LlmFalso(FiltroCardapio())

    interpretar("quero um café", llm)

    assert llm.schema is FiltroCardapio


def test_envia_o_prompt_de_sistema_e_a_frase_do_cliente():
    llm = LlmFalso(FiltroCardapio())

    interpretar("algo gelado e doce", llm)

    assert llm.mensagens == [
        ("system", INTERPRETAR_PREFERENCIAS_PROMPT),
        ("human", "algo gelado e doce"),
    ]


def test_devolve_o_filtro_gerado_pelo_llm():
    esperado = FiltroCardapio(temperatura="gelado", doce=True, sem_lactose=True)
    llm = LlmFalso(esperado)

    assert interpretar("gelada, doce e sem lactose", llm) == esperado


def test_aceita_resposta_em_dicionario():
    llm = LlmFalso({"categoria": "comida", "preco_maximo_centavos": 1000})

    resultado = interpretar("algo para comer até 10 reais", llm)

    assert resultado == FiltroCardapio(categoria="comida", preco_maximo_centavos=1000)


def test_resposta_invalida_do_llm_vira_filtro_vazio_com_aviso(caplog):
    # "morno" não existe: o FiltroCardapio recusa, e a conversa segue sem filtros.
    llm = LlmFalso({"temperatura": "morno"})

    with caplog.at_level(logging.WARNING):
        resultado = interpretar("quero algo morno", llm)

    assert resultado == FiltroCardapio()
    assert "sem filtros" in caplog.text


def test_falha_do_llm_vira_filtro_vazio_com_aviso(caplog):
    llm = LlmFalso(RuntimeError("modelo fora do ar"))

    with caplog.at_level(logging.WARNING):
        resultado = interpretar("quero um café", llm)

    assert resultado == FiltroCardapio()
    assert "sem filtros" in caplog.text


def test_sem_llm_informado_usa_o_get_llm_do_adaptador(monkeypatch):
    llm = LlmFalso(FiltroCardapio(doce=True))
    adaptador_falso = types.ModuleType("src.utils.llm_adapter")
    adaptador_falso.get_llm = lambda: llm
    monkeypatch.setitem(sys.modules, "src.utils.llm_adapter", adaptador_falso)

    resultado = asyncio.run(atendimento.interpretar_preferencias("algo doce"))

    assert resultado == FiltroCardapio(doce=True)


# --- regras escritas no prompt de interpretação ---

TEXTO = INTERPRETAR_PREFERENCIAS_PROMPT.lower()


def test_prompt_cita_todos_os_campos_do_filtro():
    for campo in FiltroCardapio.model_fields:
        assert campo in TEXTO


def test_prompt_manda_converter_reais_em_centavos():
    assert "1500" in TEXTO


def test_prompt_proibe_sem_lactose_falso():
    assert "nunca use false" in TEXTO


def test_prompt_manda_preencher_so_o_que_o_cliente_disse():
    assert "não adivinhe" in TEXTO
