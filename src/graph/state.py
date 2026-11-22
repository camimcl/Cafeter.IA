from typing import TypedDict

class State(TypedDict, total=False):
    mensagem: str
    intencao: str
    resposta: str
    quer_pedir: bool
    filtros_cardapio: dict
    pedido: Pedido
    campos_faltantes: list[str]
    estoque_ok: bool
    faltas: list[str]
    total_centavos: int
    resumo: str
    confirmado: bool
    pedido_id: str