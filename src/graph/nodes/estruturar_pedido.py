"""Nó estruturar_pedido"""

import json

from pydantic import BaseModel, Field

from src.graph.prompts.pedido_prompt import PEDIDO_PROMPT
from src.graph.state import State
from src.schemas.pedido import ItemPedido, Pedido
from src.utils.llm_adapter import get_llm


class ItemPedidoExtraido(BaseModel):
    """Representa um item extraído pelo LLM, permitindo campos incompletos."""

    produto_id: str | None = None
    quantidade: int | None = Field(default=None, strict=True)
    personalizacoes: list[str] = Field(default_factory=list)


class PedidoExtraido(BaseModel):
    """Representa o pedido extraído antes da validação definitiva."""

    itens: list[ItemPedidoExtraido] = Field(default_factory=list)


def estruturar_pedido(state: State) -> dict:
    """Extrai os itens do pedido usando o LLM e o cardápio disponível."""

    llm_estruturado = get_llm().with_structured_output(PedidoExtraido)

    cadeia = PEDIDO_PROMPT | llm_estruturado

    ids_validos = {
        produto["id"]
        for produto in state.get("cardapio", [])
        if isinstance(produto, dict) and isinstance(produto.get("id"), str)
    }

    resultado = cadeia.invoke(
        {
            "mensagem": state["mensagem"],
            "cardapio": json.dumps(
                state["cardapio"],
                ensure_ascii=False,
                indent=2,
            ),
        }
    )

    campos_faltantes = []
    itens_pedido = []

    for indice, item in enumerate(resultado.itens, start=1):
        if not item.produto_id:
            campos_faltantes.append(f"produto do item {indice}")

        elif item.produto_id not in ids_validos:
            campos_faltantes.append(f"produto '{item.produto_id}' não disponível no cardápio")

        if item.quantidade is None:
            campos_faltantes.append(f"quantidade do item {indice}")
        elif item.quantidade <= 0:
            campos_faltantes.append(f"quantidade válida do item {indice}")

        if item.produto_id in ids_validos and item.quantidade is not None and item.quantidade > 0:
            itens_pedido.append(
                ItemPedido(
                    produto_id=item.produto_id,
                    quantidade=item.quantidade,
                    personalizacoes=item.personalizacoes,
                )
            )

    if not resultado.itens:
        campos_faltantes.append("itens do pedido")

    if campos_faltantes:
        return {"campos_faltantes": campos_faltantes}

    pedido = Pedido(itens=itens_pedido)

    return {
        "pedido": pedido.model_dump(),
        "campos_faltantes": [],
    }
