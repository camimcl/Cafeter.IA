"""Nó recusar: responde quando a mensagem não pode ser atendida agora (dono: Pessoa 1)."""

from src.graph.state import State

MENSAGEM_FORA_ESCOPO = (
    "Desculpe, só posso ajudar com assuntos relacionados à nossa cafeteria, "
    "como dúvidas sobre nosso cardápio ou pedidos de nossos produtos!"
)
MENSAGEM_PEDIDO_INDISPONIVEL = (
    "Os pedidos por aqui ainda não estão disponíveis. "
    "Enquanto isso, posso te ajudar a escolher algo do cardápio!"
)


def recusar(state: State) -> dict[str, str]:
    """Devolve uma resposta educada: fora do escopo ou pedido ainda não disponível."""
    if state.get("intencao") == "pedido":
        return {"resposta": MENSAGEM_PEDIDO_INDISPONIVEL}
    return {"resposta": MENSAGEM_FORA_ESCOPO}
