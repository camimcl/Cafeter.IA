"""Testes do servidor MCP, sem rede: o Client do FastMCP conversa com o servidor em memória."""

import pytest
from fastmcp import Client

from mcp_server import servidor
from src.utils import mcp_client, mcp_stub

# As três consultas do teste do dia (meta de 22/11), já como filtros.
FRASES_DO_TESTE = [
    {"temperatura": "gelado", "doce": True, "sem_lactose": True},
    {"preco_maximo_centavos": 500},
    {},
]


@pytest.fixture
def cliente_no_servidor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Faz o chamar_ferramenta usar este servidor (em memória) em vez do stub."""
    monkeypatch.setenv("USAR_MCP_STUB", "0")
    monkeypatch.setattr(mcp_client, "url_do_servidor", lambda: servidor.mcp)


async def test_servidor_expoe_as_ferramentas() -> None:
    async with Client(servidor.mcp) as cliente:
        nomes = {ferramenta.name for ferramenta in await cliente.list_tools()}
    assert nomes == {"consultar_cardapio", "verificar_estoque"}


async def test_cada_ferramenta_tem_descricao() -> None:
    async with Client(servidor.mcp) as cliente:
        ferramentas = await cliente.list_tools()
    assert all(ferramenta.description for ferramenta in ferramentas)


@pytest.mark.parametrize(
    "filtros", FRASES_DO_TESTE, ids=["gelado_doce_sem_lactose", "5_reais", "sem_filtros"]
)
async def test_servidor_responde_igual_ao_stub(cliente_no_servidor: None, filtros: dict) -> None:
    do_servidor = await mcp_client.chamar_ferramenta("consultar_cardapio", filtros)
    do_stub = await mcp_stub.chamar_ferramenta("consultar_cardapio", filtros)
    assert do_servidor["ok"] is True
    assert do_servidor == do_stub


async def test_verificar_estoque_cenario_3(cliente_no_servidor: None) -> None:
    itens = [{"produto_id": "cappuccino", "quantidade": 3, "personalizacoes": ["leite_aveia"]}]
    resposta = await mcp_client.chamar_ferramenta("verificar_estoque", {"itens": itens})
    assert resposta == await mcp_stub.chamar_ferramenta("verificar_estoque", {"itens": itens})
    assert resposta["dados"]["faltas"][0]["faltam"] == 50


async def test_argumento_desconhecido_da_erro_interno(cliente_no_servidor: None) -> None:
    resposta = await mcp_client.chamar_ferramenta("consultar_cardapio", {"vegano": True})
    assert resposta["erro"]["codigo"] == "ERRO_INTERNO"


async def test_falha_nos_dados_vira_erro_interno(
    cliente_no_servidor: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def ler_com_falha() -> list[dict]:
        raise FileNotFoundError("cardapio.json sumiu")

    monkeypatch.setattr(servidor.repositorio, "ler_cardapio", ler_com_falha)
    resposta = await mcp_client.chamar_ferramenta("consultar_cardapio", {})
    assert resposta == {
        "ok": False,
        "erro": {"codigo": "ERRO_INTERNO", "mensagem": servidor.MENSAGEM_ERRO_INTERNO},
    }


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("http://127.0.0.1:8000/mcp", ("127.0.0.1", 8000, "/mcp")),
        ("http://localhost:9001/outro", ("localhost", 9001, "/outro")),
        ("http://127.0.0.1", ("127.0.0.1", 8000, "/mcp")),
    ],
)
def test_endereco_do_servidor(url: str, esperado: tuple[str, int, str]) -> None:
    assert servidor.endereco_do_servidor(url) == esperado
