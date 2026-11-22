"""Testes das ferramentas do servidor MCP (funções puras, sem servidor e sem LLM)."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from mcp_server.ferramentas import consultar_cardapio, tem_opcao_sem_lactose

CAMINHO_CARDAPIO = Path(__file__).parent.parent / "dados" / "cardapio.json"


@pytest.fixture
def cardapio() -> list[dict]:
    """Produtos do cardápio semente em dados/cardapio.json."""
    return json.loads(CAMINHO_CARDAPIO.read_text(encoding="utf-8"))["produtos"]


def ids(resposta: dict) -> list[str]:
    """Extrai os ids dos produtos de uma resposta de consultar_cardapio."""
    return [p["id"] for p in resposta["dados"]["produtos"]]


# --- consultar_cardapio: resultados com o cardápio semente ---


@pytest.mark.parametrize(
    ("filtros", "esperado"),
    [
        (
            {"temperatura": "gelado"},
            ["cafe_gelado_caramelo", "chocolate_gelado", "cha_gelado_pessego"],
        ),
        (
            {"sem_lactose": True},
            [
                "espresso",
                "cappuccino",
                "latte",
                "mocha",
                "cafe_gelado_caramelo",
                "chocolate_gelado",
                "cha_gelado_pessego",
            ],
        ),
        (
            {"doce": True},
            ["mocha", "cafe_gelado_caramelo", "chocolate_gelado", "cha_gelado_pessego", "brownie"],
        ),
        ({"categoria": "comida"}, ["pao_de_queijo", "brownie", "croissant"]),
        (
            {"preco_maximo_centavos": 1200},
            ["espresso", "cha_gelado_pessego", "pao_de_queijo", "brownie"],
        ),
    ],
)
def test_consultar_cardapio_filtro_unico(
    cardapio: list[dict], filtros: dict, esperado: list[str]
) -> None:
    assert ids(consultar_cardapio(cardapio, filtros)) == esperado


def test_consultar_cardapio_cenario_2_gelado_doce_sem_lactose(cardapio: list[dict]) -> None:
    filtros = {"temperatura": "gelado", "doce": True, "sem_lactose": True}
    assert ids(consultar_cardapio(cardapio, filtros)) == [
        "cafe_gelado_caramelo",
        "chocolate_gelado",
        "cha_gelado_pessego",
    ]


def test_consultar_cardapio_sem_filtros_devolve_tudo(cardapio: list[dict]) -> None:
    resposta = consultar_cardapio(cardapio)
    assert resposta["ok"] is True
    assert ids(resposta) == [p["id"] for p in cardapio]


def test_consultar_cardapio_filtros_vazios_ou_none_devolvem_tudo(cardapio: list[dict]) -> None:
    filtros_none = {"temperatura": None, "doce": None, "preco_maximo_centavos": None}
    assert ids(consultar_cardapio(cardapio, {})) == [p["id"] for p in cardapio]
    assert ids(consultar_cardapio(cardapio, filtros_none)) == [p["id"] for p in cardapio]


def test_consultar_cardapio_cappuccino_aparece_em_sem_lactose_pela_aveia(
    cardapio: list[dict],
) -> None:
    cappuccino = next(p for p in cardapio if p["id"] == "cappuccino")
    assert cappuccino["sem_lactose"] is False
    assert "cappuccino" in ids(consultar_cardapio(cardapio, {"sem_lactose": True}))


def test_consultar_cardapio_doce_false_devolve_so_nao_doces(cardapio: list[dict]) -> None:
    resposta = consultar_cardapio(cardapio, {"doce": False})
    assert ids(resposta)
    assert all(not p["doce"] for p in resposta["dados"]["produtos"])


def test_consultar_cardapio_sem_lactose_false_nao_restringe(cardapio: list[dict]) -> None:
    assert ids(consultar_cardapio(cardapio, {"sem_lactose": False})) == [p["id"] for p in cardapio]


def test_consultar_cardapio_valor_invalido_devolve_lista_vazia(cardapio: list[dict]) -> None:
    resposta = consultar_cardapio(cardapio, {"temperatura": "morno"})
    assert resposta == {"ok": True, "dados": {"produtos": []}}


def test_consultar_cardapio_preco_maximo_inclui_preco_igual(cardapio: list[dict]) -> None:
    # O chá gelado custa exatamente 1200 centavos.
    no_limite = ids(consultar_cardapio(cardapio, {"preco_maximo_centavos": 1200}))
    abaixo_do_limite = ids(consultar_cardapio(cardapio, {"preco_maximo_centavos": 1199}))
    assert "cha_gelado_pessego" in no_limite
    assert "cha_gelado_pessego" not in abaixo_do_limite


def test_consultar_cardapio_devolve_produto_completo(cardapio: list[dict]) -> None:
    produto = consultar_cardapio(cardapio, {"categoria": "bebida"})["dados"]["produtos"][1]
    assert produto == next(p for p in cardapio if p["id"] == produto["id"])
    assert "descricao" in produto
    assert "torna_sem_lactose" in produto["personalizacoes"][0]


def test_consultar_cardapio_nao_altera_os_dados_recebidos(cardapio: list[dict]) -> None:
    original = deepcopy(cardapio)
    resposta = consultar_cardapio(cardapio, {"doce": True})
    resposta["dados"]["produtos"][0]["preco_centavos"] = 0
    assert cardapio == original


# --- tem_opcao_sem_lactose ---


def test_tem_opcao_sem_lactose() -> None:
    sem_lactose = {"sem_lactose": True, "personalizacoes": []}
    com_aveia = {"sem_lactose": False, "personalizacoes": [{"torna_sem_lactose": True}]}
    com_lactose = {"sem_lactose": False, "personalizacoes": [{"torna_sem_lactose": False}]}
    assert tem_opcao_sem_lactose(sem_lactose) is True
    assert tem_opcao_sem_lactose(com_aveia) is True
    assert tem_opcao_sem_lactose(com_lactose) is False
