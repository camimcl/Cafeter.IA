# Contratos entre componentes

Preencham **antes** de codar (Fase 1 do [passo a passo](passo-a-passo.md)). Cada integrante só começa depois que os quatro concordarem.

## Estado compartilhado do grafo (`State`)

| Campo | Tipo | Quem escreve | Quem lê |
|---|---|---|---|
| `mensagem` | `str` | entrada | supervisor |
| `intent` | `str` | supervisor | roteamento |
| `pedido` | `Pedido` | Agente de Pedidos | estoque, valor, confirmação |
| `disponivel` | `bool` | verificar estoque | roteamento |
| `resposta` | `str` | agentes | saída |

*(Ajustem a tabela conforme o grupo decidir.)*

## Modelos Pydantic

- `ItemPedido`: _a definir_
- `Pedido`: _a definir_

## Ferramentas (entrada e saída)

| Ferramenta | Entrada | Saída |
|---|---|---|
| `consultar_cardapio` | _a definir_ | _a definir_ |
| `verificar_estoque` | _a definir_ | _a definir_ |
| `calcular_valor` | _a definir_ | _a definir_ |
| `registrar_pedido` | _a definir_ | _a definir_ |
| `atualizar_estoque` | _a definir_ | _a definir_ |

## Decisões tomadas

_Registrem aqui cada decisão da equipe, com data e motivo._
