# Contratos entre componentes

Estes são os pontos de encontro entre as quatro pessoas. Foram propostos na [divisão de responsabilidades](divisao-de-responsabilidades.md) e aprovados pela equipe. **Qualquer mudança exige um Pull Request aprovado por todos.**

Guardiã deste arquivo: Pessoa 1.

## 1. Cliente MCP (dono: Pessoa 4)

```python
async def chamar_ferramenta(nome: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do MCP. Sempre devolve {"ok": ...}; nunca levanta exceção."""
```

Servidor fora do ar: `{"ok": False, "erro": {"codigo": "MCP_INDISPONIVEL", "mensagem": "..."}}`.

Endereço do servidor: variável `MCP_URL` (`http://127.0.0.1:8000/mcp`). O stub é ativado por `USAR_MCP_STUB=1` e **imita o comportamento do servidor**, inclusive a idempotência (guarda as chaves em memória).

## 2. Formato de resposta das ferramentas

```json
{"ok": true,  "dados": { }}
{"ok": false, "erro": {"codigo": "ESTOQUE_INSUFICIENTE", "mensagem": "Faltam 200 ml de leite de aveia."}}
```

Códigos de erro: `PRODUTO_INEXISTENTE`, `QUANTIDADE_INVALIDA`, `ESTOQUE_INSUFICIENTE`, `PEDIDO_INVALIDO`, `MCP_INDISPONIVEL`, `ERRO_INTERNO`.

## 3. Ferramentas do MCP (dono: Pessoa 4)

| Ferramenta | Entrada | Saída (`dados`) |
|---|---|---|
| `consultar_cardapio` | filtros opcionais: `temperatura`, `sem_lactose`, `doce`, `categoria`, `preco_maximo_centavos` | `produtos`: lista com `id`, `nome`, `categoria`, `descricao`, `preco_centavos`, `temperatura`, `doce`, `sem_lactose`, `alergenos`, `personalizacoes` (cada uma com `id`, `nome`, `acrescimo_centavos`, `torna_sem_lactose`) |
| `verificar_estoque` | `itens`: lista de `{produto_id, quantidade, personalizacoes}` | `suficiente` (booleano) e `faltas`: lista de `{ingrediente, faltam, unidade}`. **Não altera nada** |
| `registrar_pedido` | `itens`, `total_centavos` e `idempotency_key` (**obrigatória**) | `pedido_id`, `total_centavos` e `duplicate` (booleano). Registra o pedido e baixa o estoque (tudo ou nada) |

### 3.1 Filtro `sem_lactose`

Devolve os produtos com `sem_lactose: true` **ou** que tenham alguma personalização com `torna_sem_lactose: true`. Assim, um cappuccino aparece em "sem lactose" porque pode ser pedido com leite de aveia. Quem apresenta o resultado ao cliente deve dizer **com qual personalização** o produto fica sem lactose.

### 3.2 Idempotência do `registrar_pedido`

Repetir o mesmo comando não pode gravar o pedido duas vezes nem baixar o estoque em dobro (por exemplo, quando a rede falha depois do envio e o sistema reenvia).

| Regra | Detalhe |
|---|---|
| Quem gera a chave | O nó `montar_resumo` (Pessoa 3), **uma vez por pedido**, com `uuid4` em texto. Fica no estado em `idempotency_key` |
| Reaproveitamento | Qualquer nova tentativa do mesmo pedido (`finalizar_pedido`) usa **a mesma chave**. Nunca se gera chave nova numa tentativa |
| Chave obrigatória | Ausente ou vazia: erro `PEDIDO_INVALIDO` |
| Chave já usada com sucesso | O servidor devolve o pedido original com `duplicate: true`, **sem** conferir o estoque de novo e **sem** alterar nada |
| Chave já usada com itens diferentes | Erro `PEDIDO_INVALIDO` |
| O que o servidor guarda | Só pedidos registrados com sucesso (a chave fica no registro em `pedidos.json`). Erros **não** consomem a chave: o cliente pode tentar de novo com dados corretos |
| Pedidos iguais em momentos diferentes | São pedidos legítimos e têm chaves diferentes. Por isso a chave **não** é um hash do conteúdo |

Exemplo:

```json
1ª chamada: {"ok": true, "dados": {"pedido_id": "P-0001", "total_centavos": 4200, "duplicate": false}}
2ª chamada, mesma chave: {"ok": true, "dados": {"pedido_id": "P-0001", "total_centavos": 4200, "duplicate": true}}
```

O nó `finalizar_pedido` trata `duplicate: true` como **sucesso**.

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
| `cardapio` | lista de produtos | `carregar_cardapio` | `estruturar_pedido`, `calcular_valor` |
| `pedido` | dicionário validado por `Pedido` | `estruturar_pedido` | estoque, valor, resumo |
| `campos_faltantes` | lista de textos | `estruturar_pedido` | `pedir_esclarecimento` |
| `estoque_ok` | booleano | `verificar_disponibilidade` | roteamento |
| `faltas` | lista | `verificar_disponibilidade` | resposta ao cliente |
| `total_centavos` | inteiro | `calcular_valor` | resumo, registro |
| `resumo` | texto | `montar_resumo` | `confirmar_pedido` |
| `idempotency_key` | texto (`uuid4`) | `montar_resumo` | `finalizar_pedido` |
| `confirmado` | booleano | `confirmar_pedido` | roteamento |
| `pedido_id` | texto | `finalizar_pedido` | resposta ao cliente |

Cada nó devolve **só o que mudou**.

## 7. Caminho do pedido e confirmação humana

Ordem dos nós (cada desvio termina em resposta ao cliente):

```text
classify → carregar_cardapio → estruturar_pedido → verificar_disponibilidade
  → calcular_valor → montar_resumo → confirmar_pedido → finalizar_pedido → resposta
```

Desvios: dados incompletos → `pedir_esclarecimento`; estoque insuficiente → informar indisponibilidade; cliente disse não → `cancelar_pedido`; servidor fora do ar em qualquer passo que chame o MCP → aviso de serviço indisponível, sem registrar nada.

**Por que `carregar_cardapio` vem antes de `estruturar_pedido`:** o LLM precisa conhecer os ids válidos de produtos e personalizações para extrair o pedido sem inventar nomes, e o `calcular_valor` precisa dos preços. O nó guarda o cardápio no estado e os dois reaproveitam.

**Confirmação:** o grafo pausa no nó `confirmar_pedido`, mostrando o `resumo` (texto feito pela Pessoa 3). O cliente responde sim ou não, e o grafo retoma com `confirmado: true` ou `false`. Só `confirmado: true` chega ao `finalizar_pedido`.

## 8. Formatos de dados

Os arquivos de exemplo estão em [`dados/`](../dados/), com o formato de cada campo e as regras de consistência em [`dados/README.md`](../dados/README.md).

| Arquivo | Dono | Resumo |
|---|---|---|
| `cardapio.json` | Pessoa 2 | `produtos` com `id`, `nome`, `categoria`, `descricao`, `preco_centavos`, `temperatura`, `doce`, `sem_lactose`, `alergenos`, `personalizacoes` |
| `estoque.json` | Pessoa 4 | `ingredientes` com `id`, `nome`, `unidade`, `quantidade`, `quantidade_minima` |
| `receitas.json` | Pessoa 4 | `receitas` por produto: ingredientes de uma unidade e ações por personalização (`substituir`, `adicionar`, `remover`) |
| `pedidos.json` | Pessoa 4 | `pedidos` registrados, cada um com `pedido_id`, `idempotency_key`, `itens`, `total_centavos` e `registrado_em` (começa vazio) |

- Dinheiro em **centavos inteiros**; identificadores em `snake_case`.
- Os arquivos se ligam por `id` (produto, personalização, ingrediente). A consistência entre eles está nas regras de `dados/README.md`.

## 9. Decisões tomadas

| Decisão | Valor | Data |
|---|---|---|
| Transporte do MCP | HTTP local, servidor em outro terminal | 22/11/2026 |
| Versão do Python | 3.13 | 22/11/2026 |
| Dinheiro | Centavos inteiros | 22/11/2026 |
| Nó `carregar_cardapio` antes de `estruturar_pedido` | Aprovado (estado ganha o campo `cardapio`) | 22/11/2026 |
| Sem lactose | Campo `sem_lactose` no produto e `torna_sem_lactose` na personalização (sem campo `vegano`) | 22/11/2026 |
| Campos novos no cardápio | `descricao` e `torna_sem_lactose` | 22/11/2026 |
| Idempotência | `idempotency_key` **obrigatória** em `registrar_pedido`, gerada no `montar_resumo` (seção 3.2) | 22/11/2026 |
| Porta do servidor | 8000 | |

## 10. Pontos a decidir

Recomendações ainda não aprovadas. A equipe aprova ou ajusta e depois atualiza os documentos.

| # | Ponto | Recomendação | Quem é afetado |
|---|---|---|---|
| 1 | **Total do pedido:** `registrar_pedido` recebe `total_centavos` da aplicação. Quem garante que está certo? | O servidor recalcula com o cardápio e rejeita divergência com `PEDIDO_INVALIDO` | Pessoa 4 |
| 2 | **Voltar os dados ao início:** testes e demonstrações alteram `estoque.json` e `pedidos.json` e sujam o Git | Os arquivos do Git são **sementes**; ao subir, o servidor copia para `estoque.runtime.json` e `pedidos.runtime.json` (já ignorados pelo `.gitignore`) e trabalha neles | Pessoa 4 |
| 3 | **Limite de quantidade por item** (`MAX_QUANTIDADE_POR_ITEM`) | 10 unidades. Validado no modelo `ItemPedido` e de novo no servidor | Pessoas 3 e 4 |
| 4 | **Formato de `pedido_id`** | `P-0001`, sequencial, gerado pelo servidor | Pessoa 4 |
| 5 | **Do atendimento para o pedido:** a flag `quer_pedir` precisa de uma função de roteamento | `route_after_atendimento` em `routing.py` | Pessoa 1 |
