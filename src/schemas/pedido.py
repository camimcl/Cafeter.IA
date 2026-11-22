from pydantic import BaseModel, Field

class ItemPedido(BaseModel):
    produto_id: str
    quantidade: int = Field(strict=True, gt=0) # Evita pedidos negativos e valores decimais
    personalizacoes: list[str]

class Pedido(BaseModel):
    itens: list[ItemPedido] = Field(min_length=1)
    total_centavos: int = Field(default=0, ge=0)
