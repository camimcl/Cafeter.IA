"""Testes das ferramentas do servidor MCP (funções puras, sem servidor e sem LLM)."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from mcp_server.ferramentas import (
    aplicar_acoes,
    consultar_cardapio,
    consumo_do_item,
    tem_opcao_sem_lactose,
    verificar_estoque,
)

PASTA_DADOS = Path(__file__).parent.parent / "dados"


def ler_dados(nome_arquivo: str) -> dict:
    """Lê um arquivo JSON da pasta dados/."""
    return json.loads((PASTA_DADOS / nome_arquivo).read_text(encoding="utf-8"))


@pytest.fixture
def cardapio() -> list[dict]:
    """Produtos do cardápio semente em dados/cardapio.json."""
    return ler_dados("cardapio.json")["produtos"]


@pytest.fixture
def receitas() -> dict:
    """Receitas semente em dados/receitas.json."""
    return ler_dados("receitas.json")["receitas"]


@pytest.fixture
def estoque() -> list[dict]:
    """Ingredientes do estoque semente em dados/estoque.json."""
    return ler_dados("estoque.json")["ingredientes"]


def item(produto_id: str, quantidade: object, personalizacoes: list | None = None) -> dict:
    """Monta um item do pedido no formato do contrato."""
    return {
        "produto_id": produto_id,
        "quantidade": quantidade,
        "personalizacoes": personalizacoes or [],
    }


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


# --- verificar_estoque: cenários do projeto ---


def test_verificar_estoque_cenario_1_suficiente(receitas: dict, estoque: list[dict]) -> None:
    itens = [item("cappuccino", 2, ["leite_aveia"]), item("pao_de_queijo", 1)]
    resposta = verificar_estoque(itens, receitas, estoque)
    assert resposta == {"ok": True, "dados": {"suficiente": True, "faltas": []}}


def test_verificar_estoque_cenario_3_falta_leite_aveia(receitas: dict, estoque: list[dict]) -> None:
    resposta = verificar_estoque([item("cappuccino", 3, ["leite_aveia"])], receitas, estoque)
    assert resposta == {
        "ok": True,
        "dados": {
            "suficiente": False,
            "faltas": [{"ingrediente": "leite_aveia", "faltam": 50, "unidade": "ml"}],
        },
    }


def test_verificar_estoque_falta_em_unidades(receitas: dict, estoque: list[dict]) -> None:
    resposta = verificar_estoque([item("croissant", 3)], receitas, estoque)
    faltas = resposta["dados"]["faltas"]
    assert faltas == [{"ingrediente": "croissant_pronto", "faltam": 1, "unidade": "un"}]


def test_verificar_estoque_quantidade_igual_ao_estoque_e_suficiente(
    receitas: dict, estoque: list[dict]
) -> None:
    # Há exatamente 2 croissants no estoque.
    resposta = verificar_estoque([item("croissant", 2)], receitas, estoque)
    assert resposta["dados"]["suficiente"] is True


def test_verificar_estoque_soma_o_consumo_de_todos_os_itens(
    receitas: dict, estoque: list[dict]
) -> None:
    # Sozinhos cabem (300 ml e 200 ml de aveia), juntos passam dos 400 ml do estoque.
    itens = [item("cappuccino", 2, ["leite_aveia"]), item("latte", 1, ["leite_aveia"])]
    faltas = verificar_estoque(itens, receitas, estoque)["dados"]["faltas"]
    assert faltas == [{"ingrediente": "leite_aveia", "faltam": 100, "unidade": "ml"}]


def test_verificar_estoque_sem_aveia_usa_leite_integral(
    receitas: dict, estoque: list[dict]
) -> None:
    # 3 cappuccinos com leite integral cabem, mesmo faltando aveia para 3.
    resposta = verificar_estoque([item("cappuccino", 3)], receitas, estoque)
    assert resposta["dados"]["suficiente"] is True


def test_verificar_estoque_nao_altera_estoque_nem_receitas(
    receitas: dict, estoque: list[dict]
) -> None:
    estoque_original, receitas_original = deepcopy(estoque), deepcopy(receitas)
    verificar_estoque([item("cappuccino", 3, ["leite_aveia"])], receitas, estoque)
    verificar_estoque([item("cappuccino", 2, ["leite_aveia", "extra_shot"])], receitas, estoque)
    assert estoque == estoque_original
    assert receitas == receitas_original


# --- verificar_estoque: erros ---


def test_verificar_estoque_produto_inexistente(receitas: dict, estoque: list[dict]) -> None:
    resposta = verificar_estoque([item("pizza", 1)], receitas, estoque)
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "PRODUTO_INEXISTENTE"


@pytest.mark.parametrize("quantidade", [0, -1, 1.5, 2.0, "2", None, True])
def test_verificar_estoque_quantidade_invalida(
    receitas: dict, estoque: list[dict], quantidade: object
) -> None:
    resposta = verificar_estoque([item("cappuccino", quantidade)], receitas, estoque)
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "QUANTIDADE_INVALIDA"


def test_verificar_estoque_quantidade_ausente(receitas: dict, estoque: list[dict]) -> None:
    resposta = verificar_estoque([{"produto_id": "cappuccino"}], receitas, estoque)
    assert resposta["erro"]["codigo"] == "QUANTIDADE_INVALIDA"


@pytest.mark.parametrize(
    "itens",
    [
        [],
        None,
        [{"quantidade": 1}],
        [item("cappuccino", 1, ["chantilly"])],
        [{"produto_id": "cappuccino", "quantidade": 1, "personalizacoes": "leite_aveia"}],
    ],
    ids=["vazio", "none", "sem_produto_id", "personalizacao_inexistente", "personalizacoes_texto"],
)
def test_verificar_estoque_pedido_invalido(
    receitas: dict, estoque: list[dict], itens: object
) -> None:
    resposta = verificar_estoque(itens, receitas, estoque)
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "PEDIDO_INVALIDO"


def test_verificar_estoque_erro_nao_verifica_os_outros_itens(
    receitas: dict, estoque: list[dict]
) -> None:
    # Um item inválido invalida o pedido inteiro, mesmo que os outros estejam certos.
    itens = [item("cappuccino", 1), item("pizza", 1)]
    assert verificar_estoque(itens, receitas, estoque)["erro"]["codigo"] == "PRODUTO_INEXISTENTE"


# --- aplicar_acoes: as três ações das personalizações ---


def test_aplicar_acoes_substituir_mantem_a_quantidade() -> None:
    acoes = [{"acao": "substituir", "ingrediente": "leite_integral", "por": "leite_aveia"}]
    resultado = aplicar_acoes({"cafe_graos": 18, "leite_integral": 150}, acoes)
    assert resultado == {"cafe_graos": 18, "leite_aveia": 150}


def test_aplicar_acoes_adicionar_soma() -> None:
    acoes = [{"acao": "adicionar", "ingrediente": "cafe_graos", "quantidade": 18}]
    assert aplicar_acoes({"cafe_graos": 18}, acoes) == {"cafe_graos": 36}


def test_aplicar_acoes_remover_tira_o_ingrediente() -> None:
    acoes = [{"acao": "remover", "ingrediente": "calda_chocolate"}]
    resultado = aplicar_acoes({"cafe_graos": 18, "calda_chocolate": 30}, acoes)
    assert resultado == {"cafe_graos": 18}


def test_aplicar_acoes_nao_altera_a_receita_original() -> None:
    original = {"leite_integral": 150}
    acoes = [{"acao": "substituir", "ingrediente": "leite_integral", "por": "leite_aveia"}]
    aplicar_acoes(original, acoes)
    assert original == {"leite_integral": 150}


def test_aplicar_acoes_desconhecida_levanta_erro() -> None:
    with pytest.raises(ValueError):
        aplicar_acoes({"cafe_graos": 18}, [{"acao": "dobrar", "ingrediente": "cafe_graos"}])


# --- consumo_do_item: receita x quantidade, com personalizações ---


def test_consumo_do_item_sem_personalizacao(receitas: dict) -> None:
    consumo = consumo_do_item(item("cappuccino", 2), receitas)
    assert consumo == {"cafe_graos": 36, "leite_integral": 300}


def test_consumo_do_item_com_aveia_e_shot_extra(receitas: dict) -> None:
    consumo = consumo_do_item(item("cappuccino", 2, ["leite_aveia", "extra_shot"]), receitas)
    assert consumo == {"cafe_graos": 72, "leite_aveia": 300}


def test_consumo_do_item_personalizacao_repetida_conta_uma_vez(receitas: dict) -> None:
    repetida = item("cappuccino", 1, ["extra_shot", "extra_shot"])
    assert consumo_do_item(repetida, receitas) == {"cafe_graos": 36, "leite_integral": 150}
