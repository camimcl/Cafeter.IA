"""Testes da entrada no terminal (src/app/main.py), com um grafo falso."""

import asyncio
import logging

from src.app import main


class GrafoFalso:
    def __init__(self, resultado=None, falha=None):
        self.resultado = resultado
        self.falha = falha
        self.entradas = []

    async def ainvoke(self, entrada):
        self.entradas.append(entrada)
        if self.falha:
            raise self.falha
        return self.resultado


def test_responder_envia_a_mensagem_e_devolve_a_resposta():
    grafo = GrafoFalso({"mensagem": "oi", "resposta": "Olá!"})

    resposta = asyncio.run(main.responder(grafo, "oi"))

    assert grafo.entradas == [{"mensagem": "oi"}]
    assert resposta == "Olá!"


def test_resultado_sem_resposta_vira_mensagem_padrao():
    grafo = GrafoFalso({"mensagem": "oi"})

    assert asyncio.run(main.responder(grafo, "oi")) == main.MENSAGEM_SEM_RESPOSTA


def test_falha_no_grafo_vira_mensagem_amigavel(caplog):
    grafo = GrafoFalso(falha=RuntimeError("LLM fora do ar"))

    with caplog.at_level(logging.ERROR):
        resposta = asyncio.run(main.responder(grafo, "oi"))

    assert resposta == main.MENSAGEM_FALHA
    assert "LLM fora do ar" in caplog.text


def test_palavras_de_saida():
    assert main.e_saida("sair")
    assert main.e_saida("  SAIR ")
    assert not main.e_saida("quero um café")
