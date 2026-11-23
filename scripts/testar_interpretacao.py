"""Teste MANUAL da interpretação de preferências com o LLM real (etapa 2.4).

Gasta uma requisição por frase (limite de ~50 por dia nos modelos gratuitos): use com moderação.
Precisa do .env preenchido e do adaptador do LLM (src/utils/llm_adapter.py).

Uso: python scripts/testar_interpretacao.py
"""

import asyncio

from src.graph.nodes.atendimento import interpretar_preferencias

FRASES_E_FILTROS_ESPERADOS = [
    (
        "Quero uma bebida gelada, doce e sem lactose",
        {"categoria": "bebida", "temperatura": "gelado", "doce": True, "sem_lactose": True},
    ),
    ("Tem algo para comer até 10 reais?", {"categoria": "comida", "preco_maximo_centavos": 1000}),
    ("Um café quente que não seja doce", {"temperatura": "quente", "doce": False}),
    ("Oi, o que vocês recomendam?", {}),
]


async def main() -> None:
    acertos = 0
    for frase, esperado in FRASES_E_FILTROS_ESPERADOS:
        obtido = (await interpretar_preferencias(frase)).model_dump(exclude_none=True)
        resultado = "OK " if obtido == esperado else "DIF"
        acertos += obtido == esperado
        print(f"[{resultado}] {frase}\n      esperado: {esperado}\n      obtido:   {obtido}")
    print(f"\n{acertos}/{len(FRASES_E_FILTROS_ESPERADOS)} frases com o filtro esperado.")


if __name__ == "__main__":
    asyncio.run(main())
