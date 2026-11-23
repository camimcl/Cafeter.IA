from typing import Literal
from pydantic import BaseModel

from src.graph.state import State
from src.utils.llm_adapter import get_llm
from src.graph.prompts.classify_prompt import CLASSIFICAR_PROMPT

class Classificacao(BaseModel):
    intencao: Literal["atendimento", "pedido", "fora_escopo"]

def classificar(state: State) -> dict[str, str]:
    #Classifica a intenção da mensagerm do cliente.

    llm = get_llm()
    classificador = llm.with_structured_output(Classificacao)

    cadeia = CLASSIFICAR_PROMPT | classificador
    resultado = cadeia.invoke({"mensagem": state["mensagem"]})

    return {"intencao": resultado.intencao}