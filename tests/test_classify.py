from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

from src.graph.nodes import classify
from src.graph.prompts.classify_prompt import CLASSIFY_PROMPT


@pytest.mark.parametrize(
    ("mensagem", "intencao_esperada"),
    [
        ("Quais bebidas geladas vocês têm?", "atendimento"),
        ("Quero pedir um cappuccino", "pedido"),
        ("Qual é a previsão do tempo?", "fora_escopo"),
    ],
)
def test_classificar_retorna_intencao(
    monkeypatch,
    mensagem: str,
    intencao_esperada: str,
) -> None:
    mensagem_recebida: dict[str, str] = {}

    def interpretar_saida(prompt) -> SimpleNamespace:
        mensagens = prompt.to_messages()
        mensagem_recebida["conteudo"] = str(mensagens[-1].content)
        return SimpleNamespace(intencao=intencao_esperada)

    class LlmFake:
        def with_structured_output(self, modelo):
            assert modelo is classify.Classificacao
            return RunnableLambda(interpretar_saida)

    monkeypatch.setattr(classify, "get_llm", lambda: LlmFake())

    resultado = classify.classify({"mensagem": mensagem})

    assert resultado == {"intencao": intencao_esperada}
    assert mensagem_recebida["conteudo"] == mensagem


def test_prompt_classificar_exige_mensagem() -> None:
    assert CLASSIFY_PROMPT.input_variables == ["mensagem"]

    prompt = CLASSIFY_PROMPT.invoke({"mensagem": "Quero um pedido"})

    mensagens = prompt.to_messages()

    assert len(mensagens) == 2
    assert "atendimento" in str(mensagens[0].content)
    assert "pedido" in str(mensagens[0].content)
    assert "fora_escopo" in str(mensagens[0].content)
    assert mensagens[-1].content == "Quero um pedido"