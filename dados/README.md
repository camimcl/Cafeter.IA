# Dados de exemplo (sementes)

Dados fictícios usados pelo servidor MCP, pelos testes e pela demonstração. São a versão inicial; a equipe pode ajustar, **desde que os formatos abaixo e as regras de consistência continuem valendo**.

| Arquivo | Dono | Conteúdo |
|---|---|---|
| `cardapio.json` | Pessoa 2 | Produtos vendidos, preços e características |
| `estoque.json` | Pessoa 4 | Ingredientes e quantidades disponíveis |
| `receitas.json` | Pessoa 4 | Quanto de cada ingrediente cada produto consome e como as personalizações mudam isso |
| `pedidos.json` | Pessoa 4 | Pedidos registrados (começa vazio) |

Convenções: JSON em UTF-8 com indentação de 2 espaços, chaves em `snake_case`, dinheiro em **centavos inteiros**, identificadores estáveis em `snake_case` ([padronização](../docs/padronizacao.md)).

## `cardapio.json`

```json
{
  "produtos": [
    {
      "id": "cappuccino",
      "nome": "Cappuccino",
      "categoria": "bebida",
      "descricao": "Espresso com leite vaporizado e espuma cremosa.",
      "preco_centavos": 1400,
      "temperatura": "quente",
      "doce": false,
      "sem_lactose": false,
      "alergenos": ["leite"],
      "personalizacoes": [
        {"id": "leite_aveia", "nome": "Leite de aveia", "acrescimo_centavos": 300, "torna_sem_lactose": true}
      ]
    }
  ]
}
```

| Campo | Valores |
|---|---|
| `categoria` | `bebida` ou `comida` |
| `temperatura` | `quente`, `gelado` ou `ambiente` |
| `doce`, `sem_lactose` | booleanos; `sem_lactose` descreve o produto **sem personalização** |
| `alergenos` | lista com `leite`, `ovo`, `gluten` (vazia se nenhum) |
| `personalizacoes[].torna_sem_lactose` | `true` quando aplicar essa personalização deixa o produto sem lactose (ex.: leite de aveia) |

## `estoque.json`

```json
{
  "ingredientes": [
    {"id": "leite_aveia", "nome": "Leite de aveia", "unidade": "ml", "quantidade": 400, "quantidade_minima": 300}
  ]
}
```

`unidade` é `g`, `ml` ou `un`. A unidade de um ingrediente é a mesma no estoque e nas receitas.

## `receitas.json`

```json
{
  "receitas": {
    "cappuccino": {
      "ingredientes": [
        {"ingrediente": "cafe_graos", "quantidade": 18},
        {"ingrediente": "leite_integral", "quantidade": 150}
      ],
      "personalizacoes": {
        "leite_aveia": [{"acao": "substituir", "ingrediente": "leite_integral", "por": "leite_aveia"}],
        "extra_shot": [{"acao": "adicionar", "ingrediente": "cafe_graos", "quantidade": 18}]
      }
    }
  }
}
```

- `ingredientes`: o que **uma unidade** do produto consome.
- `personalizacoes`: para cada personalização do cardápio, uma lista de ações sobre a receita:

| Ação | Campos | Efeito |
|---|---|---|
| `substituir` | `ingrediente`, `por` | Troca o ingrediente, mantendo a quantidade |
| `adicionar` | `ingrediente`, `quantidade` | Soma essa quantidade ao ingrediente |
| `remover` | `ingrediente` | Tira o ingrediente da receita |

O consumo do pedido é: para cada item, a receita (com as ações das personalizações escolhidas) vezes a quantidade, somado entre todos os itens.

## `pedidos.json`

Começa vazio:

```json
{"pedidos": []}
```

O servidor grava aqui cada pedido registrado. Cada registro guarda a `idempotency_key`; é assim que o servidor reconhece um pedido repetido:

```json
{
  "pedidos": [
    {
      "pedido_id": "P-0001",
      "idempotency_key": "3f2b8c1e-9d4a-4c7e-8a15-6b0e2f7d9a31",
      "registrado_em": "2026-11-22T17:30:00-03:00",
      "itens": [
        {"produto_id": "cappuccino", "quantidade": 2, "personalizacoes": ["leite_aveia"]},
        {"produto_id": "pao_de_queijo", "quantidade": 1, "personalizacoes": []}
      ],
      "total_centavos": 4200
    }
  ]
}
```

Se a mesma chave chegar de novo, o servidor devolve esse pedido com `duplicate: true` e **não** baixa o estoque outra vez.

## Regras de consistência

Cada pessoa edita só o seu arquivo, então estas regras evitam que um arquivo quebre o outro:

1. Todo `id` de produto do cardápio tem uma entrada em `receitas.json`, e vice-versa.
2. Toda personalização listada em um produto do cardápio tem uma entrada em `receitas.json` para esse produto (pode ser lista vazia), e vice-versa.
3. Todo ingrediente citado em `receitas.json` existe em `estoque.json`.
4. Ids não se repetem.

Quem alterar um arquivo confere as regras antes do Pull Request.

## Resultados esperados com estes dados

| Situação | Resultado |
|---|---|
| **Cenário 1:** 2 cappuccinos com `leite_aveia` + 1 pão de queijo | Estoque suficiente; total de **R$ 42,00** (4200 centavos) |
| **Cenário 2:** bebida gelada, doce e sem lactose | `cafe_gelado_caramelo` e `cha_gelado_pessego`; `chocolate_gelado` também, se contar a personalização de aveia |
| **Cenário 3:** 3 cappuccinos com `leite_aveia` | Estoque insuficiente: faltam **50 ml** de `leite_aveia` |
| Extra: 3 croissants | Estoque insuficiente: falta **1 un** de `croissant_pronto` |

Conferência do cenário 1: cada cappuccino com aveia custa 1400 + 300 = 1700 centavos, dois dão 3400, mais o pão de queijo (800) dão 4200.

Repetir o registro do cenário 1 com a mesma chave não altera nada: o `leite_aveia` continua em 100 ml.

Depois de confirmar o cenário 1, o `leite_aveia` cai de 400 para 100 ml, e o cenário 3 continua falhando. Para repetir a demonstração do início, volte os dados ao estado original.
