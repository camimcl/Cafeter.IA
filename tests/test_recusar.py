"""Testes do nó recusar."""

from src.graph.nodes.recusar import (
    MENSAGEM_FORA_ESCOPO,
    MENSAGEM_PEDIDO_INDISPONIVEL,
    recusar,
)


def test_fora_do_escopo_explica_o_que_a_cafeteria_atende():
    resultado = recusar({"intencao": "fora_escopo"})

    assert resultado == {"resposta": MENSAGEM_FORA_ESCOPO}
    assert "cafeteria" in MENSAGEM_FORA_ESCOPO.lower()


def test_pedido_avisa_que_pedidos_ainda_nao_estao_disponiveis():
    resultado = recusar({"intencao": "pedido"})

    assert resultado == {"resposta": MENSAGEM_PEDIDO_INDISPONIVEL}
    assert "card" in MENSAGEM_PEDIDO_INDISPONIVEL.lower()  # oferece ajuda com o cardápio


def test_sem_intencao_usa_a_mensagem_de_fora_do_escopo():
    assert recusar({}) == {"resposta": MENSAGEM_FORA_ESCOPO}
