"""Servidor MCP da Cafeter.IA: expõe as ferramentas da cafeteria em HTTP local.

Rode em outro terminal, na raiz do projeto:  python mcp_server/servidor.py
Endereço lido de MCP_URL (padrão http://127.0.0.1:8000/mcp).
"""

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

# Rodando como script, a raiz do projeto não entra no sys.path e "import mcp_server" falharia.
RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DO_PROJETO))

import os  # noqa: E402

from dotenv import load_dotenv  # noqa: E402
from fastmcp import FastMCP  # noqa: E402

from mcp_server import ferramentas, repositorio  # noqa: E402

logger = logging.getLogger(__name__)

URL_PADRAO = "http://127.0.0.1:8000/mcp"
MENSAGEM_ERRO_INTERNO = "A cafeteria não conseguiu concluir a operação agora."

mcp = FastMCP(
    "Cafeter.IA",
    instructions="Ferramentas da cafeteria: consultar o cardápio e verificar o estoque.",
)


def executar_com_seguranca(nome: str, operacao: Callable[[], dict]) -> dict:
    """Roda a ferramenta; falha inesperada (ex.: dados corrompidos) vira ERRO_INTERNO."""
    try:
        return operacao()
    except Exception:
        logger.exception("Falha inesperada na ferramenta '%s'", nome)
        return ferramentas.resposta_erro("ERRO_INTERNO", MENSAGEM_ERRO_INTERNO)


@mcp.tool
def consultar_cardapio(
    temperatura: str | None = None,
    sem_lactose: bool | None = None,
    doce: bool | None = None,
    categoria: str | None = None,
    preco_maximo_centavos: int | None = None,
) -> dict:
    """Consulta o cardápio da cafeteria. Sem filtros, devolve todos os produtos.

    Filtros opcionais, combinados com E: temperatura ("quente", "gelado" ou "ambiente"),
    sem_lactose, doce, categoria ("bebida" ou "comida") e preco_maximo_centavos (inteiro,
    R$ 15,00 = 1500). sem_lactose=true inclui produtos que ficam sem lactose com alguma
    personalização (ex.: leite de aveia); veja torna_sem_lactose em cada personalização.
    """
    filtros = {
        "temperatura": temperatura,
        "sem_lactose": sem_lactose,
        "doce": doce,
        "categoria": categoria,
        "preco_maximo_centavos": preco_maximo_centavos,
    }
    return executar_com_seguranca(
        "consultar_cardapio",
        lambda: ferramentas.consultar_cardapio(repositorio.ler_cardapio(), filtros),
    )


@mcp.tool
def verificar_estoque(itens: list[dict]) -> dict:
    """Verifica se há ingredientes para o pedido inteiro. Não altera nada no estoque.

    itens: lista de {produto_id, quantidade, personalizacoes}. Devolve suficiente (booleano)
    e faltas: lista de {ingrediente, faltam, unidade}.
    """
    return executar_com_seguranca(
        "verificar_estoque",
        lambda: ferramentas.verificar_estoque(
            itens, repositorio.ler_receitas(), repositorio.ler_estoque()
        ),
    )


def endereco_do_servidor(url: str) -> tuple[str, int, str]:
    """Separa a MCP_URL em host, porta e caminho (ex.: 127.0.0.1, 8000, /mcp)."""
    partes = urlparse(url)
    return partes.hostname or "127.0.0.1", partes.port or 8000, partes.path or "/mcp"


def iniciar() -> None:
    """Sobe o servidor HTTP no endereço de MCP_URL."""
    load_dotenv(RAIZ_DO_PROJETO / ".env")
    logging.basicConfig(level=logging.INFO)
    host, porta, caminho = endereco_do_servidor(os.getenv("MCP_URL") or URL_PADRAO)
    logger.info("Servidor MCP da Cafeter.IA em http://%s:%s%s", host, porta, caminho)
    mcp.run(transport="http", host=host, port=porta, path=caminho)


if __name__ == "__main__":
    iniciar()
