"""Stub do cliente MCP: responde como o servidor, sem rede, para desenvolver e testar.

Usa as mesmas funções do servidor (mcp_server.ferramentas) com os dados reais de dados/,
então o stub e o servidor dão as mesmas respostas. É ativado com USAR_MCP_STUB=1.
"""

import logging

from mcp_server.ferramentas import consultar_cardapio, resposta_erro, verificar_estoque
from mcp_server.repositorio import ler_cardapio, ler_estoque, ler_receitas

logger = logging.getLogger(__name__)

# Argumentos que cada ferramenta aceita. O servidor real recusa os outros, e o stub também.
ARGUMENTOS_ACEITOS = {
    "consultar_cardapio": {
        "temperatura",
        "sem_lactose",
        "doce",
        "categoria",
        "preco_maximo_centavos",
    },
    "verificar_estoque": {"itens"},
}


def executar_ferramenta(nome: str, argumentos: dict) -> dict:
    """Roda a ferramenta pedida com os dados de dados/ e devolve a resposta do contrato."""
    if nome == "consultar_cardapio":
        return consultar_cardapio(ler_cardapio(), argumentos)
    return verificar_estoque(argumentos.get("itens"), ler_receitas(), ler_estoque())


async def chamar_ferramenta(nome: str, argumentos: dict | None = None) -> dict:
    """Chama a ferramenta localmente. Mesmo contrato do cliente real; nunca levanta exceção."""
    argumentos = argumentos or {}

    if nome not in ARGUMENTOS_ACEITOS:
        logger.error("Stub do MCP: ferramenta desconhecida '%s'", nome)
        return resposta_erro("ERRO_INTERNO", f"A ferramenta '{nome}' não existe.")

    desconhecidos = set(argumentos) - ARGUMENTOS_ACEITOS[nome]
    if desconhecidos:
        logger.error("Stub do MCP: argumentos inválidos para '%s': %s", nome, desconhecidos)
        return resposta_erro("ERRO_INTERNO", f"Argumentos inválidos para '{nome}'.")

    try:
        return executar_ferramenta(nome, argumentos)
    except Exception:
        # Dados corrompidos ou arquivo ausente: é falha nossa, não do cliente.
        logger.exception("Stub do MCP: falha ao executar '%s'", nome)
        return resposta_erro("ERRO_INTERNO", "Não foi possível consultar a cafeteria agora.")
