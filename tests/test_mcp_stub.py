"""Testes do stub do cliente MCP (sem rede, com os dados reais de dados/)."""

import pytest

from mcp_server.repositorio import ler_cardapio
from src.utils import mcp_stub
from src.utils.mcp_stub import chamar_ferramenta


def ids(resposta: dict) -> list[str]:
    """Extrai os ids dos produtos de uma resposta de consultar_cardapio."""
    return [p["id"] for p in resposta["dados"]["produtos"]]


# --- consultar_cardapio: as frases do teste do dia ---


async def test_sem_filtros_devolve_o_cardapio_real() -> None:
    resposta = await chamar_ferramenta("consultar_cardapio", {})
    assert resposta["ok"] is True
    assert ids(resposta) == [p["id"] for p in ler_cardapio()]


async def test_gelado_doce_sem_lactose_traz_so_produtos_reais() -> None:
    filtros = {"temperatura": "gelado", "doce": True, "sem_lactose": True}
    resposta = await chamar_ferramenta("consultar_cardapio", filtros)
    assert ids(resposta) == ["cafe_gelado_caramelo", "chocolate_gelado", "cha_gelado_pessego"]


async def test_resposta_diz_qual_personalizacao_tira_a_lactose() -> None:
    filtros = {"temperatura": "gelado", "doce": True, "sem_lactose": True}
    resposta = await chamar_ferramenta("consultar_cardapio", filtros)
    chocolate = next(p for p in resposta["dados"]["produtos"] if p["id"] == "chocolate_gelado")
    assert chocolate["sem_lactose"] is False
    assert chocolate["personalizacoes"][0]["torna_sem_lactose"] is True


async def test_algo_de_5_reais_devolve_lista_vazia() -> None:
    resposta = await chamar_ferramenta("consultar_cardapio", {"preco_maximo_centavos": 500})
    assert resposta == {"ok": True, "dados": {"produtos": []}}


async def test_argumentos_none_equivale_a_sem_filtros() -> None:
    resposta = await chamar_ferramenta("consultar_cardapio", None)
    assert len(ids(resposta)) == len(ler_cardapio())


# --- verificar_estoque ---


async def test_verificar_estoque_cenario_3() -> None:
    itens = [{"produto_id": "cappuccino", "quantidade": 3, "personalizacoes": ["leite_aveia"]}]
    resposta = await chamar_ferramenta("verificar_estoque", {"itens": itens})
    faltas = resposta["dados"]["faltas"]
    assert faltas == [{"ingrediente": "leite_aveia", "faltam": 50, "unidade": "ml"}]


# --- erros: sempre {"ok": false}, nunca exceção ---


async def test_ferramenta_inexistente_da_erro_interno() -> None:
    resposta = await chamar_ferramenta("pedir_pizza", {})
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "ERRO_INTERNO"


async def test_argumento_desconhecido_da_erro_interno() -> None:
    resposta = await chamar_ferramenta("consultar_cardapio", {"vegano": True})
    assert resposta["erro"]["codigo"] == "ERRO_INTERNO"


async def test_falha_nos_dados_vira_erro_interno(monkeypatch: pytest.MonkeyPatch) -> None:
    def ler_com_falha() -> list[dict]:
        raise FileNotFoundError("cardapio.json sumiu")

    monkeypatch.setattr(mcp_stub, "ler_cardapio", ler_com_falha)
    resposta = await chamar_ferramenta("consultar_cardapio", {})
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "ERRO_INTERNO"
