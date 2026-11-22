"""Testes do FiltroCardapio (etapa 2.2).

Regra do projeto: o LLM interpreta a frase do cliente e o Python valida o resultado.
Estes testes garantem que o "formulário" aceita o que é válido e recusa o resto.
"""

import pytest
from pydantic import ValidationError

from src.schemas.filtro_cardapio import FiltroCardapio


def test_filtro_vazio_e_valido():
    filtro = FiltroCardapio()

    assert filtro.temperatura is None
    assert filtro.sem_lactose is None
    assert filtro.doce is None
    assert filtro.categoria is None
    assert filtro.preco_maximo_centavos is None


def test_filtro_completo_guarda_os_valores():
    filtro = FiltroCardapio(
        temperatura="gelado",
        sem_lactose=True,
        doce=True,
        categoria="bebida",
        preco_maximo_centavos=1500,
    )

    assert filtro.temperatura == "gelado"
    assert filtro.sem_lactose is True
    assert filtro.doce is True
    assert filtro.categoria == "bebida"
    assert filtro.preco_maximo_centavos == 1500


@pytest.mark.parametrize("temperatura", ["quente", "gelado", "ambiente"])
def test_temperaturas_validas(temperatura):
    assert FiltroCardapio(temperatura=temperatura).temperatura == temperatura


def test_temperatura_invalida_e_recusada():
    with pytest.raises(ValidationError):
        FiltroCardapio(temperatura="morno")


def test_categoria_invalida_e_recusada():
    with pytest.raises(ValidationError):
        FiltroCardapio(categoria="sobremesa")


@pytest.mark.parametrize("preco", [0, -100])
def test_preco_zero_ou_negativo_e_recusado(preco):
    with pytest.raises(ValidationError):
        FiltroCardapio(preco_maximo_centavos=preco)


def test_preco_com_virgula_e_recusado():
    # 15.50 reais NÃO é aceito: o preço é sempre inteiro, em centavos (1550).
    with pytest.raises(ValidationError):
        FiltroCardapio(preco_maximo_centavos=15.5)


def test_campo_desconhecido_e_recusado():
    # Se o LLM inventar um campo (ex.: "vegano"), preferimos o erro a ignorar em silêncio.
    with pytest.raises(ValidationError):
        FiltroCardapio(vegano=True)


def test_para_argumentos_mcp_omite_campos_vazios():
    filtro = FiltroCardapio(temperatura="gelado", doce=True)

    # Este dicionário é o que será enviado ao consultar_cardapio.
    assert filtro.model_dump(exclude_none=True) == {"temperatura": "gelado", "doce": True}
