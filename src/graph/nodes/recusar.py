from src.graph.state import State


def recusar(state: State) -> dict[str, str]:
    """Retorna uma resposta educada para mensagens fora do escopo da cafeteria."""
    return {
        "resposta": (
            "Desculpe, só posso ajudar com assuntos relacionados à nossa cafeteria, "
            "como dúvidas sobre nosso cardápio ou pedidos de nossos produtos!"
        )
    }
