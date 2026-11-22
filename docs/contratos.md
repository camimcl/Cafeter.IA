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

## 8. Formatos de dados (a definir no Marco 0)

Arquivos em `dados/`: `cardapio.json` (Pessoa 2), `estoque.json`, `receitas.json` e `pedidos.json` (Pessoa 4).

- Dinheiro em **centavos inteiros** (`preco_centavos`).
- Identificadores em `snake_case` e estáveis (`cappuccino`, `leite_aveia`).
- `receitas.json`: ingredientes por unidade de produto e **substituições por personalização** (ex.: leite de aveia no lugar do leite integral).

_Colem aqui um exemplo real de cada arquivo depois de aprovado._

## 9. Decisões tomadas

| Decisão | Valor | Data |
|---|---|---|
| Transporte do MCP | HTTP local, servidor em outro terminal | 22/11/2026 |
| Dinheiro | Centavos inteiros (a confirmar) | |
| Porta do servidor | 8000 (a confirmar) | |
