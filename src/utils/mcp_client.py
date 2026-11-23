"""Cliente MCP: o único ponto por onde a aplicação chama as ferramentas da cafeteria.

Com USAR_MCP_STUB=1, usa o stub (sem servidor). Sem isso, conecta no servidor HTTP em MCP_URL.
Sempre devolve {"ok": ...} no formato do contrato e nunca levanta exceção.
"""

import logging
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ToolError

from src.utils import mcp_stub

load_dotenv()
logger = logging.getLogger(__name__)

URL_PADRAO = "http://127.0.0.1:8000/mcp"
TIMEOUT_SEGUNDOS = 10

MENSAGEM_INDISPONIVEL = (
    "O serviço da cafeteria não está no ar. Verifique se o servidor MCP foi iniciado "
    "em outro terminal (python mcp_server/servidor.py)."
)
MENSAGEM_ERRO_INTERNO = "A cafeteria não conseguiu concluir a operação agora."


def resposta_erro(codigo: str, mensagem: str) -> dict:
    """Monta a resposta de erro no formato do contrato."""
    return {"ok": False, "erro": {"codigo": codigo, "mensagem": mensagem}}


def esta_usando_stub() -> bool:
    """Diz se o stub está ligado (USAR_MCP_STUB=1). Lido a cada chamada, não só ao importar."""
    return os.getenv("USAR_MCP_STUB", "").strip() == "1"


def url_do_servidor() -> str:
    """Endereço do servidor MCP, lido de MCP_URL."""
    return os.getenv("MCP_URL") or URL_PADRAO


def converter_resultado(resultado: object) -> dict:
    """Confere se a resposta do servidor está no formato do contrato e a devolve."""
    dados = getattr(resultado, "structured_content", None)
    if isinstance(dados, dict) and isinstance(dados.get("ok"), bool):
        return dados
    logger.error("Resposta do servidor MCP fora do contrato: %r", dados)
    return resposta_erro("ERRO_INTERNO", MENSAGEM_ERRO_INTERNO)


async def chamar_no_servidor(nome: str, argumentos: dict) -> dict:
    """Chama a ferramenta no servidor HTTP e trata servidor fora do ar e falhas da ferramenta."""
    endereco = url_do_servidor()
    try:
        async with Client(endereco, timeout=TIMEOUT_SEGUNDOS) as cliente:
            resultado = await cliente.call_tool(nome, argumentos)
    except ToolError as erro:
        # A ferramenta existe, mas falhou ou recebeu argumentos que não aceita.
        logger.error("Ferramenta '%s' falhou no servidor MCP: %s", nome, erro)
        return resposta_erro("ERRO_INTERNO", MENSAGEM_ERRO_INTERNO)
    except Exception as erro:
        # Conexão recusada, tempo esgotado ou queda no meio: o servidor não respondeu.
        logger.warning("Servidor MCP indisponível em %s: %s", endereco, erro)
        return resposta_erro("MCP_INDISPONIVEL", MENSAGEM_INDISPONIVEL)
    return converter_resultado(resultado)


async def chamar_ferramenta(nome: str, argumentos: dict | None = None) -> dict:
    """Chama uma ferramenta do MCP. Sempre devolve {"ok": ...}; nunca levanta exceção."""
    argumentos = argumentos or {}
    if esta_usando_stub():
        return await mcp_stub.chamar_ferramenta(nome, argumentos)
    return await chamar_no_servidor(nome, argumentos)
