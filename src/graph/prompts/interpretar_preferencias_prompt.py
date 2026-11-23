"""Prompt da interpretação de preferências (etapa 2.4).

Instrui o LLM a preencher o FiltroCardapio a partir da frase do cliente. A validação do
resultado é do Pydantic; aqui ficam só as regras de preenchimento.
"""

INTERPRETAR_PREFERENCIAS_PROMPT = """\
Você lê a mensagem de um cliente de cafeteria e preenche um filtro de busca do cardápio.

Preencha apenas o que o cliente disse. Campo que ele não mencionou fica vazio. Não adivinhe.

- temperatura: "quente", "gelado" ou "ambiente". "Gelada", "fria" ou "com gelo" valem "gelado".
- doce: true se ele quer algo doce; false se disse que não quer nada doce.
- sem_lactose: true se pediu sem lactose, sem leite de vaca ou contou que tem intolerância.
  Nunca use false: sem essa menção, deixe vazio.
- categoria: "bebida" ou "comida". "Algo para comer", "lanche" ou "salgado" valem "comida".
- preco_maximo_centavos: o valor máximo que ele aceita pagar, em centavos inteiros.
  "Até 15 reais" vira 1500; "R$ 12,50" vira 1250.

Não crie outros campos. Se a mensagem não trouxer nenhuma preferência, deixe tudo vazio.
"""
