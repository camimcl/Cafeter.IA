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

```json
{"pedidos": []}
```

O servidor grava aqui cada pedido registrado.

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

Depois de confirmar o cenário 1, o `leite_aveia` cai de 400 para 100 ml, e o cenário 3 continua falhando. Para repetir a demonstração do início, volte os dados ao estado original.
