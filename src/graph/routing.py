"""Funções de roteamento do grafo (dono: Pessoa 1).

Cada função recebe o estado e devolve o nome do próximo caminho.
"""

from src.graph.state import State


def route_by_intent(state: State) -> str:
    """Decide o caminho pela intenção: "atendimento" ou "recusar".

    O fluxo de pedido ainda não está ligado ao grafo. Por enquanto, a intenção "pedido" vai
    para o nó recusar, que avisa o cliente de que os pedidos ainda não estão disponíveis.
    """
    if state.get("intencao") == "atendimento":
        return "atendimento"
    return "recusar"
