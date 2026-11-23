"""Testes do roteamento por intenção (routing.py)."""

import pytest

from src.graph.routing import route_by_intent


def test_atendimento_vai_para_o_atendimento():
    assert route_by_intent({"intencao": "atendimento"}) == "atendimento"


@pytest.mark.parametrize("intencao", ["fora_escopo", "pedido"])
def test_fora_do_escopo_e_pedido_vao_para_a_recusa(intencao):
    # O fluxo de pedido ainda não está ligado: por enquanto, a recusa avisa o cliente.
    assert route_by_intent({"intencao": intencao}) == "recusar"


def test_sem_intencao_vai_para_a_recusa():
    assert route_by_intent({}) == "recusar"
