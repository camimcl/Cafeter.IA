"""Testes do nó carregar_cardapio"""

from unittest.mock import AsyncMock, patch

import pytest

from src.graph.nodes.carregar_cardapio import carregar_cardapio

# Dados fixos que imitam a resposta de chamar_ferramenta("consultar_cardapio", {})
CARDAPIO_STUB = {
    "ok": True,
    "dados": {
        "produtos": [
            {
                "id": "cappuccino",
                "nome": "Cappuccino",
                "preco_centavos": 1400,
                "personalizacoes": [
                    {"id": "leite_aveia", "acrescimo_centavos": 300, "torna_sem_lactose": True}
                ],
            }
        ]
    },
}


@pytest.mark.asyncio
async def test_carregar_cardapio_sucesso():
    """O campo 'cardapio' chega populado no estado quando o MCP responde com sucesso."""
    with patch(
        "src.graph.nodes.carregar_cardapio.chamar_ferramenta",
        new=AsyncMock(return_value=CARDAPIO_STUB),
    ):
        resultado = await carregar_cardapio({})

    assert "cardapio" in resultado
    assert resultado["cardapio"][0]["id"] == "cappuccino"
    assert "resposta" not in resultado  # sem mensagem de erro


MCP_INDISPONIVEL = {
    "ok": False,
    "erro": {
        "codigo": "MCP_INDISPONIVEL",
        "mensagem": "Não foi possível conectar ao servidor MCP.",
    },
}


@pytest.mark.asyncio
async def test_carregar_cardapio_mcp_indisponivel():
    """Com servidor fora do ar, o nó não quebra e devolve mensagem amigável."""
    with patch(
        "src.graph.nodes.carregar_cardapio.chamar_ferramenta",
        new=AsyncMock(return_value=MCP_INDISPONIVEL),
    ):
        resultado = await carregar_cardapio({})

    assert "resposta" in resultado  # mensagem amigável ao cliente
    assert "cardapio" not in resultado  # sem cardápio
    assert isinstance(resultado["resposta"], str)
    assert len(resultado["resposta"]) > 0  # mensagem não vazia
