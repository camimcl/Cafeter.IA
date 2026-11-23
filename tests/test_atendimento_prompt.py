"""Testes do prompt do atendente (etapa 2.3).

Não chamamos o LLM (testes são offline). O que dá para garantir sem ele é que as regras
combinadas pela equipe continuam escritas no texto do prompt: se alguém apagar uma regra
sem querer, o teste correspondente quebra.
"""

from src.graph.prompts.atendimento_prompt import ATENDIMENTO_PROMPT

TEXTO = ATENDIMENTO_PROMPT.lower()


def test_prompt_e_um_texto_nao_vazio():
    assert isinstance(ATENDIMENTO_PROMPT, str)
    assert ATENDIMENTO_PROMPT.strip()


def test_prompt_manda_responder_em_portugues():
    assert "português" in TEXTO


def test_prompt_limita_o_escopo_a_cafeteria():
    assert "cafeteria" in TEXTO
    assert "fora do assunto" in TEXTO


def test_regra_de_ouro_so_recomendar_o_que_veio_da_lista():
    assert "lista de produtos" in TEXTO
    assert "nunca invente" in TEXTO


def test_regra_sem_lactose_exige_dizer_qual_personalizacao():
    assert "sem lactose" in TEXTO
    assert "personalização" in TEXTO


def test_prompt_manda_avisar_sobre_alergenos():
    assert "alérgenos" in TEXTO


def test_prompt_proibe_calcular_valores():
    assert "não calcule" in TEXTO


def test_prompt_proibe_registrar_pedido_e_prometer_estoque():
    assert "não registre pedidos" in TEXTO
    assert "estoque" in TEXTO


def test_prompt_diz_o_que_fazer_quando_nao_ha_produtos():
    assert "lista vazia" in TEXTO


def test_prompt_nao_tem_chaves_para_nao_quebrar_formatacao():
    # Se um dia o prompt for usado com .format(), chaves soltas gerariam erro.
    assert "{" not in ATENDIMENTO_PROMPT
    assert "}" not in ATENDIMENTO_PROMPT
