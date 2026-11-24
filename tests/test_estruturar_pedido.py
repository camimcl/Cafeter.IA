from src.graph.nodes.estruturar_pedido import (
    ItemPedidoExtraido,
    PedidoExtraido,
    estruturar_pedido,
)
from src.graph.prompts.pedido_prompt import PEDIDO_PROMPT


class LlmFalso:
    """Imita o LLM utilizado pelo nó estruturar_pedido."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.schema = None
        self.mensagens = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def __call__(self, mensagens):
        self.mensagens = mensagens
        return self.resposta


def test_estrutura_pedido_completo(monkeypatch):
    """Transforma uma solicitação completa em dois itens estruturados."""

    resposta_llm = PedidoExtraido(
        itens=[
            ItemPedidoExtraido(
                produto_id="cappuccino",
                quantidade=2,
                personalizacoes=["leite_aveia"],
            ),
            ItemPedidoExtraido(
                produto_id="pao_de_queijo",
                quantidade=1,
            ),
        ]
    )

    llm = LlmFalso(resposta_llm)

    monkeypatch.setattr(
        "src.graph.nodes.estruturar_pedido.get_llm",
        lambda: llm,
    )

    state = {
        "mensagem": "dois cappuccinos com leite de aveia e um pão de queijo",
        "cardapio": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "personalizacoes": [{"id": "leite_aveia", "nome": "Leite de aveia"}],
            },
            {
                "id": "pao_de_queijo",
                "nome": "Pão de queijo",
                "personalizacoes": [],
            },
        ],
    }

    resultado = estruturar_pedido(state)

    assert resultado["pedido"] == {
        "itens": [
            {
                "produto_id": "cappuccino",
                "quantidade": 2,
                "personalizacoes": ["leite_aveia"],
            },
            {
                "produto_id": "pao_de_queijo",
                "quantidade": 1,
                "personalizacoes": [],
            },
        ],
        "total_centavos": 0,
    }

    assert resultado["campos_faltantes"] == []
    assert llm.schema is PedidoExtraido


def test_identifica_quantidade_faltante(monkeypatch):
    """Identifica quando o cliente não informa a quantidade."""

    resposta_llm = PedidoExtraido(
        itens=[
            ItemPedidoExtraido(
                produto_id="cappuccino",
                quantidade=None,
            )
        ]
    )

    llm = LlmFalso(resposta_llm)

    monkeypatch.setattr(
        "src.graph.nodes.estruturar_pedido.get_llm",
        lambda: llm,
    )

    state = {
        "mensagem": "Quero um cappuccino",
        "cardapio": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "personalizacoes": [],
            }
        ],
    }

    resultado = estruturar_pedido(state)

    assert resultado["campos_faltantes"] == ["quantidade do item 1"]
    assert "pedido" not in resultado


def test_identifica_produto_inexistente(monkeypatch):
    """Impede que um produto ausente do cardápio entre no pedido."""

    resposta_llm = PedidoExtraido(
        itens=[
            ItemPedidoExtraido(
                produto_id="pastel",
                quantidade=1,
            )
        ]
    )

    llm = LlmFalso(resposta_llm)

    monkeypatch.setattr(
        "src.graph.nodes.estruturar_pedido.get_llm",
        lambda: llm,
    )

    state = {
        "mensagem": "Quero um pastel",
        "cardapio": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "personalizacoes": [],
            }
        ],
    }

    resultado = estruturar_pedido(state)

    assert resultado["campos_faltantes"] == ["produto 'pastel' não disponível no cardápio"]
    assert "pedido" not in resultado


def test_identifica_quantidade_invalida(monkeypatch):
    """Identifica quantidades iguais a zero ou menores que zero."""

    resposta_llm = PedidoExtraido(
        itens=[
            ItemPedidoExtraido(
                produto_id="cappuccino",
                quantidade=0,
            )
        ]
    )

    llm = LlmFalso(resposta_llm)

    monkeypatch.setattr(
        "src.graph.nodes.estruturar_pedido.get_llm",
        lambda: llm,
    )

    state = {
        "mensagem": "Quero zero cappuccinos",
        "cardapio": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "personalizacoes": [],
            }
        ],
    }

    resultado = estruturar_pedido(state)

    assert resultado["campos_faltantes"] == ["quantidade válida do item 1"]
    assert "pedido" not in resultado


def test_identifica_pedido_vazio(monkeypatch):
    """Identifica quando o LLM não retorna nenhum item."""

    resposta_llm = PedidoExtraido(itens=[])

    llm = LlmFalso(resposta_llm)

    monkeypatch.setattr(
        "src.graph.nodes.estruturar_pedido.get_llm",
        lambda: llm,
    )

    state = {
        "mensagem": "Quero fazer um pedido",
        "cardapio": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "personalizacoes": [],
            }
        ],
    }

    resultado = estruturar_pedido(state)

    assert resultado["campos_faltantes"] == ["itens do pedido"]
    assert "pedido" not in resultado


def test_variaveis_do_prompt():
    assert set(PEDIDO_PROMPT.input_variables) == {
        "mensagem",
        "cardapio",
    }
