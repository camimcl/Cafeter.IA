"""Testes do cliente MCP (sem internet).

O caminho do servidor é testado com um servidor FastMCP em memória, que o Client aceita
no lugar da URL, e com uma porta local fechada para simular o servidor fora do ar.
"""

import socket

import pytest
from fastmcp import FastMCP

from src.utils import mcp_client
from src.utils.mcp_client import chamar_ferramenta, converter_resultado


@pytest.fixture
def sem_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Desliga o stub, mesmo que o .env de quem roda os testes o tenha ligado."""
    monkeypatch.setenv("USAR_MCP_STUB", "0")


def servidor_de_teste() -> FastMCP:
    """Servidor MCP em memória com ferramentas de mentira, só para os testes."""
    servidor = FastMCP("teste")

    @servidor.tool
    def consultar_cardapio(temperatura: str | None = None) -> dict:
        """Devolve um produto fixo com a temperatura pedida."""
        return {"ok": True, "dados": {"produtos": [{"id": "teste", "temperatura": temperatura}]}}

    @servidor.tool
    def ferramenta_que_quebra() -> dict:
        """Simula uma falha inesperada dentro do servidor."""
        raise ValueError("dados corrompidos")

    @servidor.tool
    def fora_do_contrato() -> dict:
        """Devolve uma resposta sem o campo ok."""
        return {"produtos": []}

    return servidor


@pytest.fixture
def com_servidor_de_teste(sem_stub: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Faz o cliente conversar com o servidor em memória em vez da URL."""
    servidor = servidor_de_teste()
    monkeypatch.setattr(mcp_client, "url_do_servidor", lambda: servidor)


def porta_local_fechada() -> int:
    """Encontra uma porta local livre, onde nenhum servidor está escutando."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --- escolha entre stub e servidor ---


async def test_com_stub_ligado_usa_o_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USAR_MCP_STUB", "1")
    monkeypatch.setenv("MCP_URL", f"http://127.0.0.1:{porta_local_fechada()}/mcp")
    resposta = await chamar_ferramenta("consultar_cardapio", {"preco_maximo_centavos": 500})
    assert resposta == {"ok": True, "dados": {"produtos": []}}


@pytest.mark.parametrize("valor", ["", "0", "nao"])
def test_stub_so_liga_com_1(monkeypatch: pytest.MonkeyPatch, valor: str) -> None:
    monkeypatch.setenv("USAR_MCP_STUB", valor)
    assert mcp_client.esta_usando_stub() is False


def test_url_padrao_quando_mcp_url_nao_existe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_URL", raising=False)
    assert mcp_client.url_do_servidor() == "http://127.0.0.1:8000/mcp"


# --- caminho do servidor ---


async def test_sucesso_devolve_a_resposta_do_servidor(com_servidor_de_teste: None) -> None:
    resposta = await chamar_ferramenta("consultar_cardapio", {"temperatura": "gelado"})
    assert resposta == {
        "ok": True,
        "dados": {"produtos": [{"id": "teste", "temperatura": "gelado"}]},
    }


@pytest.mark.parametrize(
    ("nome", "argumentos"),
    [
        ("ferramenta_que_quebra", {}),
        ("ferramenta_inexistente", {}),
        ("consultar_cardapio", {"vegano": True}),
        ("fora_do_contrato", {}),
    ],
    ids=["falha_no_servidor", "inexistente", "argumento_invalido", "fora_do_contrato"],
)
async def test_falhas_da_ferramenta_viram_erro_interno(
    com_servidor_de_teste: None, nome: str, argumentos: dict
) -> None:
    resposta = await chamar_ferramenta(nome, argumentos)
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "ERRO_INTERNO"


async def test_servidor_fora_do_ar_da_mcp_indisponivel(
    sem_stub: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MCP_URL", f"http://127.0.0.1:{porta_local_fechada()}/mcp")
    resposta = await chamar_ferramenta("consultar_cardapio", {})
    assert resposta["ok"] is False
    assert resposta["erro"]["codigo"] == "MCP_INDISPONIVEL"
    assert "servidor" in resposta["erro"]["mensagem"]


# --- converter_resultado ---


def test_converter_resultado_sem_structured_content_da_erro_interno() -> None:
    assert converter_resultado(object())["erro"]["codigo"] == "ERRO_INTERNO"
