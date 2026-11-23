import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()


def get_llm():
    """Retorna o modelo de linguagem configurado pelas variaveis de ambiente."""
    model = os.environ["LLM_MODEL"]
    model_provider = os.environ["LLM_PROVIDER"]
    api_key = os.environ["OPENROUTER_API_KEY"]
    base_url = os.environ["OPENROUTER_BASE_URL"]

    return init_chat_model(
        model=model, model_provider=model_provider, api_key=api_key, base_url=base_url
    )
