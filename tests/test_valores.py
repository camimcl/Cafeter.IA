import pytest

from src.schemas.pedido import Pedido
from src.utils.valores import calcular_total, formatar_valor

# --------------------------------------------------
# Testes do cálculo do total do pedido
# --------------------------------------------------


def test_calcular_total_com_personalizacoes():
    """Calcula o total considerando os acréscimos das personalizações."""
    produtos = [
        {
            "id": "cappuccino",
            "preco_centavos": 1400,
            "personalizacoes": [
                {"id": "leite_aveia", "acrescimo_centavos": 300},
                {"id": "extra_shot", "acrescimo_centavos": 400},
            ],
        }
    ]

    pedido = Pedido(
        itens=[
            {
                "produto_id": "cappuccino",
                "quantidade": 2,
                "personalizacoes": ["leite_aveia", "extra_shot"],
            }
        ]
    )

    # Cada cappuccino custa 2.100 centavos; duas unidades custam 4.200.
    assert calcular_total(pedido, produtos) == 4200


def test_calcular_total_sem_personalizacoes():
    """Calcula o total de um produto sem personalizações."""
    produtos = [
        {
            "id": "espresso",
            "preco_centavos": 700,
            "personalizacoes": [],
        }
    ]

    pedido = Pedido(
        itens=[
            {
                "produto_id": "espresso",
                "quantidade": 2,
            }
        ]
    )

    assert calcular_total(pedido, produtos) == 1400


def test_calcular_total_com_varios_produtos():
    """Soma corretamente os valores de diferentes produtos."""
    produtos = [
        {
            "id": "espresso",
            "preco_centavos": 700,
            "personalizacoes": [],
        },
        {
            "id": "brownie",
            "preco_centavos": 1100,
            "personalizacoes": [],
        },
    ]

    pedido = Pedido(
        itens=[
            {"produto_id": "espresso", "quantidade": 2},
            {"produto_id": "brownie", "quantidade": 1},
        ]
    )

    # Dois espressos (1.400) + um brownie (1.100) = 2.500.
    assert calcular_total(pedido, produtos) == 2500


def test_calcular_total_com_personalizacoes_diferentes():
    """Calcula unidades do mesmo produto com personalizações distintas."""
    produtos = [
        {
            "id": "cappuccino",
            "preco_centavos": 1400,
            "personalizacoes": [
                {"id": "leite_aveia", "acrescimo_centavos": 300},
                {"id": "extra_shot", "acrescimo_centavos": 400},
            ],
        }
    ]

    pedido = Pedido(
        itens=[
            {
                "produto_id": "cappuccino",
                "quantidade": 1,
                "personalizacoes": ["leite_aveia", "extra_shot"],
            },
            {
                "produto_id": "cappuccino",
                "quantidade": 1,
                "personalizacoes": ["leite_aveia"],
            },
        ]
    )

    # Primeira unidade: 2.100; segunda unidade: 1.700.
    assert calcular_total(pedido, produtos) == 3800


# --------------------------------------------------
# Testes de validação do cálculo
# --------------------------------------------------


def test_calcular_total_produto_inexistente():
    """Gera erro quando o produto não está disponível no cardápio."""
    pedido = Pedido(itens=[{"produto_id": "produto_inexistente", "quantidade": 1}])

    with pytest.raises(ValueError):
        calcular_total(pedido, [])


def test_calcular_total_personalizacao_inexistente():
    """Gera erro quando a personalização não pertence ao produto."""
    produtos = [
        {
            "id": "cappuccino",
            "preco_centavos": 1400,
            "personalizacoes": [],
        }
    ]

    pedido = Pedido(
        itens=[
            {
                "produto_id": "cappuccino",
                "quantidade": 1,
                "personalizacoes": ["personalizacao_inexistente"],
            }
        ]
    )

    with pytest.raises(ValueError):
        calcular_total(pedido, produtos)


# --------------------------------------------------
# Testes da formatação monetária
# --------------------------------------------------


def test_formatar_valor_sem_centavos():
    """Formata valores inteiros em reais."""
    assert formatar_valor(4200) == "R$ 42,00"


def test_formatar_valor_com_centavos():
    """Formata valores que possuem centavos."""
    assert formatar_valor(150) == "R$ 1,50"


def test_formatar_valor_com_milhar():
    """Utiliza o separador brasileiro de milhares."""
    assert formatar_valor(125075) == "R$ 1.250,75"


def test_formatar_valor_zero():
    """Formata corretamente o valor zero."""
    assert formatar_valor(0) == "R$ 0,00"


def test_formatar_valor_negativo():
    """Gera erro quando o valor informado é negativo."""
    with pytest.raises(ValueError):
        formatar_valor(-100)
