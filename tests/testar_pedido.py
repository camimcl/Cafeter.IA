from pydantic import ValidationError
from src.schemas.pedido import ItemPedido, Pedido

# Criando um item
item = ItemPedido(
    produto_id="cappuccino",
    quantidade=2,
    personalizacoes=["leite_aveia"]
)

# Criando um pedido com esse item
pedido = Pedido(itens=[item])

print("Pedido criado:")
print(pedido)

# Testando pedido vazio
try:
    Pedido(itens=[])
except ValidationError as erro:
    print("\nPedido vazio rejeitado:")
    print(erro)