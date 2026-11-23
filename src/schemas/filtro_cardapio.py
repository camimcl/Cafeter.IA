"""Filtro de busca do cardápio (contrato: docs/contratos.md, seção 5).

O LLM transforma a frase do cliente neste "formulário"; o Python valida.
Todos os campos são opcionais: `None` significa "não filtre por isso".
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FiltroCardapio(BaseModel):
    """Preferências do cliente já traduzidas para filtros exatos."""

    # Campo inventado pelo LLM (ex.: "vegano") vira erro, em vez de ser ignorado em silêncio.
    model_config = ConfigDict(extra="forbid")

    temperatura: Literal["quente", "gelado", "ambiente"] | None = None
    sem_lactose: bool | None = None
    doce: bool | None = None
    categoria: Literal["bebida", "comida"] | None = None
    # Dinheiro sempre em centavos inteiros: R$ 15,00 = 1500.
    preco_maximo_centavos: int | None = Field(default=None, gt=0)
