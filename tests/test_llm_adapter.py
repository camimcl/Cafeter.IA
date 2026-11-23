from src.utils import llm_adapter


def test_get_llm_le_variaveis_de_ambiente(monkeypatch) -> None:
    valores = {
        "LLM_MODEL": "openrouter/free",
        "LLM_PROVIDER": "openai",
        "OPENROUTER_API_KEY": "teste",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    }

    for chave, valor in valores.items():
        monkeypatch.setenv(chave, valor)

    recebidos: dict = {}

    def inicializar_fake(**kwargs):
        recebidos.update(kwargs)
        return object()

    monkeypatch.setattr(llm_adapter, "init_chat_model", inicializar_fake)

    resultado = llm_adapter.get_llm()

    assert resultado is not None
    assert recebidos["model"] == "openrouter/free"
    assert recebidos["api_key"] == "teste"
