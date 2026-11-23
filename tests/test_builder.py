"""Testes unitários para a compilação e execução do grafo mínimo."""

import asyncio

import pytest

from src.graph import builder
from src.graph.builder import criar_grafo
from src.graph.nodes.recusar import MENSAGEM_PEDIDO_INDISPONIVEL


def test_grafo_compila() -> None:
    """Verifica se o grafo mínimo compila com sucesso e possui os nós esperados."""
    grafo = criar_grafo()
    assert grafo is not None

    nos_esperados = {"classify", "atendimento", "recusar"}
    assert nos_esperados.issubset(set(grafo.nodes.keys()))


def test_fluxo_atendimento(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida se o fluxo direciona mensagem de atendimento para o nó de atendimento."""
    monkeypatch.setattr(builder, "classify", lambda state: {"intencao": "atendimento"})
    monkeypatch.setattr(
        builder,
        "atendimento",
        lambda state: {"resposta": "Temos café expresso e cappuccino."},
    )

    grafo = criar_grafo()
    resultado = grafo.invoke({"mensagem": "Quais bebidas vocês têm?"})

    assert resultado.get("intencao") == "atendimento"
    assert resultado.get("resposta") == "Temos café expresso e cappuccino."


def test_fluxo_fora_escopo_recusa(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida se o fluxo direciona mensagem fora de escopo para o nó de recusa."""
    monkeypatch.setattr(builder, "classify", lambda state: {"intencao": "fora_escopo"})

    grafo = criar_grafo()
    resultado = grafo.invoke({"mensagem": "Qual é a previsão do tempo para hoje?"})

    assert resultado.get("intencao") == "fora_escopo"
    assert "cafeteria" in resultado.get("resposta", "").lower()


def test_atendimento_assincrono_roda_com_ainvoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """O nó atendimento real é async: o grafo precisa rodar com ainvoke."""

    async def atendimento_falso(state):
        return {"resposta": f"Recebi: {state['mensagem']}"}

    monkeypatch.setattr(builder, "classify", lambda state: {"intencao": "atendimento"})
    monkeypatch.setattr(builder, "atendimento", atendimento_falso)

    grafo = criar_grafo()
    resultado = asyncio.run(grafo.ainvoke({"mensagem": "algo gelado"}))

    assert resultado["resposta"] == "Recebi: algo gelado"


def test_fluxo_pedido_avisa_que_ainda_nao_esta_disponivel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enquanto o fluxo de pedido não está ligado, a intenção pedido recebe um aviso próprio."""
    monkeypatch.setattr(builder, "classify", lambda state: {"intencao": "pedido"})

    grafo = criar_grafo()
    resultado = grafo.invoke({"mensagem": "Quero um cappuccino"})

    assert resultado["resposta"] == MENSAGEM_PEDIDO_INDISPONIVEL
