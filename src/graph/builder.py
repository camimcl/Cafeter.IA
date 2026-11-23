"""Montagem do grafo do Cafeter.IA (dono: Pessoa 1).

Hoje o grafo cobre a conversa de recomendação:
START → classify → (atendimento | recusar) → END.
O nó atendimento é assíncrono, então o grafo roda com `ainvoke`.
"""

from langgraph.graph import END, START, StateGraph

from src.graph.nodes.atendimento import atendimento
from src.graph.nodes.classify import classify
from src.graph.nodes.recusar import recusar
from src.graph.routing import route_by_intent
from src.graph.state import State


def criar_grafo():
    """Monta e compila o grafo: classifica a intenção e encaminha para o nó certo."""
    graph = StateGraph(State)

    graph.add_node("classify", classify)
    graph.add_node("atendimento", atendimento)
    graph.add_node("recusar", recusar)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "atendimento": "atendimento",
            "recusar": "recusar",
        },
    )
    graph.add_edge("atendimento", END)
    graph.add_edge("recusar", END)

    return graph.compile()
