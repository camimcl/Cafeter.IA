"""Testes da consulta ao cardápio pelo MCP (etapa 2.5).

O cliente MCP é substituído por um falso que segue o contrato: sempre devolve {"ok": ...}
e nunca levanta exceção (docs/contratos.md, seções 1 e 2).
"""

import asyncio
import sys
import types

from src.graph.nodes import atendimento
from src.schemas.filtro_cardapio import FiltroCardapio

CAPPUCCINO = {"id": "cappuccino", "nome": "Cappuccino", "preco_centavos": 1400}


class ClienteMcpFalso:
    """Guarda a chamada recebida e devolve a resposta combinada."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.chamadas = []

    async def __call__(self, nome, argumentos):
        self.chamadas.append((nome, argumentos))
        return self.resposta


def consultar(filtro, cliente):
    return asyncio.run(atendimento.consultar_produtos(filtro, chamar_ferramenta=cliente))


def test_chama_consultar_cardapio_so_com_os_filtros_preenchidos():
    cliente = ClienteMcpFalso({"ok": True, "dados": {"produtos": []}})

    consultar(FiltroCardapio(temperatura="gelado", doce=True), cliente)

    assert cliente.chamadas == [("consultar_cardapio", {"temperatura": "gelado", "doce": True})]


def test_filtro_vazio_consulta_sem_argumentos():
    cliente = ClienteMcpFalso({"ok": True, "dados": {"produtos": []}})

    consultar(FiltroCardapio(), cliente)

    assert cliente.chamadas == [("consultar_cardapio", {})]


def test_sucesso_devolve_a_resposta_do_mcp():
    resposta = {"ok": True, "dados": {"produtos": [CAPPUCCINO]}}

    assert consultar(FiltroCardapio(), ClienteMcpFalso(resposta)) == resposta


def test_servidor_fora_do_ar_devolve_o_erro_sem_levantar_excecao():
    resposta = {"ok": False, "erro": {"codigo": "MCP_INDISPONIVEL", "mensagem": "sem conexão"}}

    assert consultar(FiltroCardapio(), ClienteMcpFalso(resposta)) == resposta


def test_sem_cliente_informado_usa_o_chamar_ferramenta_do_mcp_client(monkeypatch):
    cliente = ClienteMcpFalso({"ok": True, "dados": {"produtos": []}})
    modulo_falso = types.ModuleType("src.utils.mcp_client")
    modulo_falso.chamar_ferramenta = cliente
    monkeypatch.setitem(sys.modules, "src.utils.mcp_client", modulo_falso)

    asyncio.run(atendimento.consultar_produtos(FiltroCardapio(doce=True)))

    assert cliente.chamadas == [("consultar_cardapio", {"doce": True})]


# --- mensagem ao cliente quando a consulta falha ---


def test_servidor_fora_do_ar_avisa_que_o_servico_nao_esta_no_ar():
    erro = {"codigo": "MCP_INDISPONIVEL", "mensagem": "Connection refused"}
    resposta = {"ok": False, "erro": erro}

    mensagem = atendimento.mensagem_de_erro(resposta)

    assert mensagem == atendimento.MENSAGEM_SERVICO_FORA_DO_AR
    assert "fora do ar" in mensagem


def test_outros_erros_viram_mensagem_generica_sem_detalhe_tecnico():
    resposta = {"ok": False, "erro": {"codigo": "ERRO_INTERNO", "mensagem": "KeyError: 'produtos'"}}

    mensagem = atendimento.mensagem_de_erro(resposta)

    assert mensagem == atendimento.MENSAGEM_ERRO_NA_CONSULTA
    assert "KeyError" not in mensagem
