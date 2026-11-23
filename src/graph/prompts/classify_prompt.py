from langchain_core.prompts import ChatPromptTemplate

CLASSIFICAR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Classifique a mensagem do cliente em exatamente uma destas intenções:\n\n"
            "- atendimento: conversa, recomendações ou dúvidas sobre o cardápio.\n"
            "- pedido: desejo de escolher ou solicitar itens do pedido.\n"
            "- fora_escopo: mensagem não relacionada à cafeteria.\n\n"
            "Responda apenas com: atendimento, pedido ou fora_escopo.",
        ),
        ("human", "{mensagem}"),
    ]
)