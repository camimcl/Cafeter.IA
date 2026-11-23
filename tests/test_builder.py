"""Testes unitários para a compilação e execução do grafo mínimo."""

import pytest

from src.graph import builder
from src.graph.builder import criar_grafo


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
