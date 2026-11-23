"""Agente de Atendimento: dúvidas e recomendações do cardápio (Pessoa 2).

Etapa 2.4: interpretar as preferências do cliente como um FiltroCardapio.

As dependências externas (LLM) podem ser passadas por parâmetro. Assim os testes usam um
falso e nunca chamam o modelo de verdade.
"""

import logging

from pydantic import ValidationError

from src.graph.prompts.interpretar_preferencias_prompt import INTERPRETAR_PREFERENCIAS_PROMPT
from src.schemas.filtro_cardapio import FiltroCardapio

logger = logging.getLogger(__name__)


def _obter_llm():
    """Busca o LLM do adaptador só na hora do uso (o adaptador carrega o langchain)."""
    from src.utils.llm_adapter import get_llm

    return get_llm()


async def interpretar_preferencias(mensagem: str, llm=None) -> FiltroCardapio:
    """Transforma a frase do cliente em filtros do cardápio, com saída estruturada do LLM.

    Se o LLM falhar ou devolver algo fora do contrato, segue sem filtros: o cliente vê o
    cardápio e pode refinar a pergunta, em vez de a conversa quebrar.
    """
    if llm is None:
        llm = _obter_llm()

    estruturado = llm.with_structured_output(FiltroCardapio)
    mensagens = [("system", INTERPRETAR_PREFERENCIAS_PROMPT), ("human", mensagem)]

    try:
        resultado = await estruturado.ainvoke(mensagens)
        if isinstance(resultado, FiltroCardapio):
            return resultado
        return FiltroCardapio.model_validate(resultado)
    except ValidationError:
        logger.warning("Resposta do LLM fora do FiltroCardapio; seguindo sem filtros.")
    except Exception:
        logger.warning("Falha ao interpretar preferências; seguindo sem filtros.", exc_info=True)

    return FiltroCardapio()
