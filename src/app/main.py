"""Entrada do Cafeter.IA no terminal (dono: Pessoa 1).

Uso, na raiz do projeto: python -m src.app.main
Com USAR_MCP_STUB=1 no .env, funciona sem o servidor MCP. Sem o stub, suba antes o servidor
em outro terminal: python mcp_server/servidor.py
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

PALAVRAS_DE_SAIDA = {"sair", "exit", "quit"}
MENSAGEM_SEM_RESPOSTA = "Desculpe, não consegui responder agora. Pode repetir?"
MENSAGEM_FALHA = "Tive um problema para responder agora. Tente de novo em instantes, por favor."


def e_saida(texto: str) -> bool:
    """Diz se o cliente quer encerrar a conversa."""
    return texto.strip().lower() in PALAVRAS_DE_SAIDA


async def responder(grafo, mensagem: str) -> str:
    """Roda o grafo com a mensagem e devolve a resposta. Uma falha vira mensagem amigável."""
    try:
        resultado = await grafo.ainvoke({"mensagem": mensagem})
    except Exception:
        logger.exception("Falha ao rodar o grafo para a mensagem: %r", mensagem)
        return MENSAGEM_FALHA
    return resultado.get("resposta") or MENSAGEM_SEM_RESPOSTA


async def conversar() -> None:
    """Conversa no terminal até o cliente digitar "sair"."""
    # Importado aqui para que responder e e_saida possam ser testados sem o langgraph.
    from src.graph.builder import criar_grafo

    grafo = criar_grafo()
    print("Cafeter.IA: Olá! Como posso ajudar? (digite 'sair' para encerrar)")
    while True:
        mensagem = input("Você: ").strip()
        if not mensagem:
            continue
        if e_saida(mensagem):
            print("Cafeter.IA: Até logo!")
            return
        print(f"Cafeter.IA: {await responder(grafo, mensagem)}")


def main() -> None:
    """Ponto de entrada do programa."""
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(conversar())


if __name__ == "__main__":
    main()
