from typing import TypedDict

class State(TypedDict, total=False):
    mensagem: str
    intencao: str
    resposta: str
    quer_pedir: bool
    filtros_cardapio: dict
    cardapio: list[dict]
    pedido: dict
    campos_faltantes: list[str]
    estoque_ok: bool
    faltas: list[dict]
    total_centavos: int
    resumo: str
    idempotency_key: str
    confirmado: bool
    pedido_id: str