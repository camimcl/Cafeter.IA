"""Nó carregar_cardapio

Busca o cardápio completo no servidor MCP logo no início do fluxo de pedidos
para abastecer o estado com os produtos e preços vigentes.
"""

import logging

from src.graph.state import State

try:
    from src.utils.mcp_client import chamar_ferramenta
except ImportError:
    # Fallback provisório enquanto a Pessoa 4 não finaliza o cliente MCP
    async def chamar_ferramenta(nome: str, argumentos: dict) -> dict:  # pragma: no cover
        raise NotImplementedError("Cliente MCP ainda não implementado.")


logger = logging.getLogger(__name__)

MENSAGEM_SERVICO_INDISPONIVEL = (
    "Desculpe, nosso serviço está temporariamente indisponível no momento. "
    "Por favor, tente novamente em instantes."
)


async def carregar_cardapio(state: State) -> dict:
    """Busca o cardápio completo no MCP e guarda no estado."""
    # Chama o MCP sem filtros para carregar todos os produtos disponíveis
    resposta = await chamar_ferramenta("consultar_cardapio", {})

    if not resposta.get("ok"):
        logger.warning("Falha ao consultar cardápio no MCP: %s", resposta.get("erro"))
        # Se falhar, devolve apenas a mensagem ao cliente sem interromper com exceção
        return {"resposta": MENSAGEM_SERVICO_INDISPONIVEL}

    # Cada nó devolve apenas o que mudou no estado (regra do projeto)
    produtos = resposta.get("dados", {}).get("produtos", [])
    return {"cardapio": produtos}