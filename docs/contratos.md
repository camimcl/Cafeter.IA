# Contratos entre componentes

Estes são os pontos de encontro entre as quatro pessoas. Foram propostos na [divisão de responsabilidades](divisao-de-responsabilidades.md) e **precisam ser aprovados pela equipe no Marco 0** (Fase 1 do [passo a passo](passo-a-passo.md)). Depois de aprovados, **qualquer mudança exige um Pull Request aprovado por todos**.

Guardiã deste arquivo: Pessoa 1.

## 1. Cliente MCP (dono: Pessoa 4)

```python
async def chamar_ferramenta(nome: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do MCP. Sempre devolve {"ok": ...}; nunca levanta exceção."""
```

Servidor fora do ar: `{"ok": False, "erro": {"codigo": "MCP_INDISPONIVEL", "mensagem": "..."}}`.

Endereço do servidor: variável `MCP_URL` (`http://127.0.0.1:8000/mcp`). O stub é ativado por `USAR_MCP_STUB=1`.

## 2. Formato de resposta das ferramentas

```json
{"ok": true,  "dados": { }}
{"ok": false, "erro": {"codigo": "ESTOQUE_INSUFICIENTE", "mensagem": "Faltam 200 ml de leite de aveia."}}
```

Códigos de erro: `PRODUTO_INEXISTENTE`, `QUANTIDADE_INVALIDA`, `ESTOQUE_INSUFICIENTE`, `PEDIDO_INVALIDO`, `MCP_INDISPONIVEL`, `ERRO_INTERNO`.

## 3. Ferramentas do MCP (dono: Pessoa 4)

| Ferramenta | Entrada | Saída (`dados`) |
|---|---|---|
| `consultar_cardapio` | filtros opcionais: `temperatura`, `sem_lactose`, `doce`, `categoria`, `preco_maximo_centavos` | `produtos`: lista com `id`, `nome`, `categoria`, `preco_centavos`, `temperatura`, `doce`, `sem_lactose`, `alergenos`, `personalizacoes` (cada uma com `id`, `nome`, `acrescimo_centavos`) |
| `verificar_estoque` | `itens`: lista de `{produto_id, quantidade, personalizacoes}` | `suficiente` (booleano) e `faltas`: lista de `{ingrediente, faltam, unidade}`. **Não altera nada** |
| `registrar_pedido` | `itens` e `total_centavos` | `pedido_id` e `total_centavos`. Registra o pedido e baixa o estoque (tudo ou nada) |

## 4. Pedido (dono: Pessoa 3)

```text
ItemPedido: produto_id (texto), quantidade (inteiro > 0), personalizacoes (lista de ids)
Pedido:     itens (lista de ItemPedido), total_centavos (preenchido só pelo Python)
```

## 5. Filtros do cardápio (dono: Pessoa 2)

```text
FiltroCardapio (todos opcionais): temperatura, sem_lactose, doce, categoria, preco_maximo_centavos
```

## 6. Estado compartilhado do grafo (`State`, dono: Pessoa 1)

| Campo | Tipo | Quem escreve | Quem lê |
|---|---|---|---|
| `mensagem` | texto | entrada | supervisor, agentes |
| `intent` | texto (`atendimento`, `pedido`, `fora_escopo`) | `classify` | roteamento |
| `resposta` | texto | agentes e nós finais | saída |
| `quer_pedir` | booleano | atendimento | roteamento |
| `filtros_cardapio` | dicionário | atendimento | atendimento |
| `pedido` | dicionário validado por `Pedido` | `estruturar_pedido` | estoque, valor, resumo |
| `campos_faltantes` | lista de textos | `estruturar_pedido` | `pedir_esclarecimento` |
| `estoque_ok` | booleano | `verificar_disponibilidade` | roteamento |
| `faltas` | lista | `verificar_disponibilidade` | resposta ao cliente |
| `total_centavos` | inteiro | `calcular_valor` | resumo, registro |
| `resumo` | texto | `montar_resumo` | `confirmar_pedido` |
| `confirmado` | booleano | `confirmar_pedido` | roteamento |
| `pedido_id` | texto | `finalizar_pedido` | resposta ao cliente |

Cada nó devolve **só o que mudou**.

## 7. Confirmação humana (Pessoas 1 e 3)

O grafo pausa no nó `confirmar_pedido` mostrando o `resumo` (texto feito pela Pessoa 3). O cliente responde sim ou não, e o grafo retoma com `confirmado: true` ou `false`. Só `confirmado: true` chega ao `finalizar_pedido`.

## 8. Formatos de dados

Os arquivos de exemplo estão em [`dados/`](../dados/), com o formato de cada campo e as regras de consistência em [`dados/README.md`](../dados/README.md).

| Arquivo | Dono | Resumo |
|---|---|---|
| `cardapio.json` | Pessoa 2 | `produtos` com `id`, `nome`, `categoria`, `descricao`, `preco_centavos`, `temperatura`, `doce`, `sem_lactose`, `alergenos`, `personalizacoes` |
| `estoque.json` | Pessoa 4 | `ingredientes` com `id`, `nome`, `unidade`, `quantidade`, `quantidade_minima` |
| `receitas.json` | Pessoa 4 | `receitas` por produto: ingredientes de uma unidade e ações por personalização (`substituir`, `adicionar`, `remover`) |
| `pedidos.json` | Pessoa 4 | `pedidos` registrados (começa vazio) |

- Dinheiro em **centavos inteiros**; identificadores em `snake_case`.
- Os arquivos se ligam por `id` (produto, personalização, ingrediente). A consistência entre eles está nas regras de `dados/README.md`.

## 9. Decisões tomadas

| Decisão | Valor | Data |
|---|---|---|
| Transporte do MCP | HTTP local, servidor em outro terminal | 22/11/2026 |
| Dinheiro | Centavos inteiros (a confirmar) | |
| Porta do servidor | 8000 (a confirmar) | |
| Formato dos dados | Exemplos em `dados/` (aprovar na reunião) | |

## 10. Pontos a decidir no Marco 0

Lacunas encontradas ao montar os dados de exemplo. Cada uma tem uma recomendação; a equipe aprova ou ajusta e depois atualiza os documentos.

| # | Ponto | Recomendação | Quem é afetado |
|---|---|---|---|
| 1 | **Como o LLM conhece os `produto_id` válidos?** Hoje `estruturar_pedido` roda antes de qualquer chamada ao MCP, mas o modelo precisa da lista de produtos e personalizações para extrair ids corretos. O cálculo do valor também precisa dos preços | Novo nó `carregar_cardapio` (MCP `consultar_cardapio` sem filtros) **antes** de `estruturar_pedido`, com o resultado guardado no estado (campo `cardapio`) e reaproveitado em `calcular_valor` | Pessoas 1 (estado e grafo) e 3 |
| 2 | **"Sem lactose" e personalizações:** um cappuccino com leite de aveia fica sem lactose, mas `sem_lactose` descreve só o produto base | Campo `torna_sem_lactose` em cada personalização; o filtro `sem_lactose` devolve produtos com `sem_lactose: true` **ou** com alguma personalização que torna sem lactose | Pessoas 2 e 4 |
| 3 | **Campos novos no cardápio** além do contrato original: `descricao` (ajuda a recomendação) e `torna_sem_lactose` | Aceitar os dois | Pessoas 2, 3 e 4 |
| 4 | **Total do pedido:** `registrar_pedido` recebe `total_centavos` da aplicação. Quem garante que está certo? | O servidor recalcula com o cardápio e rejeita divergência com `PEDIDO_INVALIDO` | Pessoa 4 |
| 5 | **Pedido duplicado:** um reenvio por falha de rede, ou uma confirmação repetida, gravaria o pedido duas vezes | `idempotency_key` opcional em `registrar_pedido`; mesma chave devolve o pedido já registrado, sem baixar o estoque de novo | Pessoas 3 e 4 |
| 6 | **Voltar os dados ao início:** testes e demonstrações alteram `estoque.json` e `pedidos.json` e sujam o Git | Os arquivos do Git são **sementes**; ao subir, o servidor copia para `estoque.runtime.json` e `pedidos.runtime.json` (já ignorados pelo `.gitignore`) e trabalha neles | Pessoa 4 |
| 7 | **Limite de quantidade por item** (`MAX_QUANTIDADE_POR_ITEM`) | 10 unidades. Validado no modelo `ItemPedido` e de novo no servidor | Pessoas 3 e 4 |
| 8 | **Formato de `pedido_id`** | `P-0001`, sequencial, gerado pelo servidor | Pessoa 4 |
| 9 | **Do atendimento para o pedido:** a flag `quer_pedir` precisa de uma função de roteamento | `route_after_atendimento` em `routing.py` | Pessoa 1 |

