import pytest
from pydantic import ValidationError

from src.schemas.pedido import ItemPedido, Pedido


def test_criar_item_pedido_valido():
    item = ItemPedido(
        produto_id="cappuccino",
        quantidade=2,
        personalizacoes=["leite_aveia"],
    )

    assert item.produto_id == "cappuccino"
    assert item.quantidade == 2
    assert item.personalizacoes == ["leite_aveia"]


def test_personalizacoes_vazias_por_padrao():
    item = ItemPedido(
        produto_id="espresso",
        quantidade=1,
    )

    assert item.personalizacoes == []


def test_rejeitar_quantidade_zero():
    with pytest.raises(ValidationError):
        ItemPedido(
            produto_id="cappuccino",
            quantidade=0,
        )


def test_rejeitar_quantidade_negativa():
    with pytest.raises(ValidationError):
        ItemPedido(
            produto_id="cappuccino",
            quantidade=-1,
        )


def test_rejeitar_quantidade_fracionada():
    with pytest.raises(ValidationError):
        ItemPedido(
            produto_id="cappuccino",
            quantidade=2.5,
        )


def test_criar_pedido_com_itens():
    item = ItemPedido(
        produto_id="cappuccino",
        quantidade=2,
    )

    pedido = Pedido(itens=[item])

    assert len(pedido.itens) == 1
    assert pedido.total_centavos == 0


def test_rejeitar_pedido_sem_itens():
    with pytest.raises(ValidationError):
        Pedido(itens=[])
