from src.schemas.pedido import Pedido

CENTAVOS_POR_REAL = 100


def calcular_total(pedido: Pedido, produtos: list[dict]) -> int:
    """Calcula o valor total do pedido em centavos."""
    total_centavos = 0

    for item in pedido.itens:
        produto_encontrado = None

        for produto in produtos:
            if produto["id"] == item.produto_id:
                produto_encontrado = produto
                break

        if produto_encontrado is None:
            raise ValueError(f"Produto não encontrado: {item.produto_id}")

        preco_unitario = produto_encontrado["preco_centavos"]

        for personalizacao_id in item.personalizacoes:
            personalizacao_encontrada = None

            for personalizacao in produto_encontrado["personalizacoes"]:
                if personalizacao["id"] == personalizacao_id:
                    personalizacao_encontrada = personalizacao
                    break

            if personalizacao_encontrada is None:
                raise ValueError(f"Personalização não encontrada: {personalizacao_id}")

            preco_unitario += personalizacao_encontrada["acrescimo_centavos"]

        total_centavos += preco_unitario * item.quantidade

    return total_centavos


def formatar_valor(total_centavos: int) -> str:
    """Formata um valor em centavos como moeda brasileira."""
    if total_centavos < 0:
        raise ValueError("O valor não pode ser negativo.")

    reais, centavos = divmod(total_centavos, CENTAVOS_POR_REAL)

    reais_formatados = f"{reais:,}".replace(",", ".")

    return f"R$ {reais_formatados},{centavos:02d}"
