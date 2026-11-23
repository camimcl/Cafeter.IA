from langgraph.graph import END, START, StateGraph

from src.graph.nodes.classify import classify
from src.graph.nodes.recusar import recusar
from src.graph.state import State

# Nó de Atendimento (Pessoa 2) - usa stub temporário se o arquivo ainda não existir
try:
    from src.graph.nodes.atendimento import atendimento
except ImportError:
    def atendimento(state: State) -> dict[str, str]:
        """Stub temporário do Agente de Atendimento (dono: Pessoa 2)."""
        return {"resposta": "Olá! Sou o atendente virtual da Cafeter.IA. Em que posso ajudar?"}

# Roteamento por intenção - usa routing.py se existir, senão usa função local como fallback
try:
    from src.graph.routing import route_by_intent
except ImportError:
    def route_by_intent(state: State) -> str:
        """Roteia para atendimento ou recusa (fora de escopo ou pedido pausado)."""
        intencao = state.get("intencao")
        if intencao == "atendimento":
            return "atendimento"
        return "recusar"


def criar_grafo():

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
