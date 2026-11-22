# Passo a passo do Cafeter.IA

Este documento guia a equipe da primeira linha de código até a demonstração. Ele está dividido em **fases**. As fases 0 a 6 formam o **MVP**. As fases 7 a 9 completam o projeto com RAG, MCP e observabilidade, reforçando todos os assuntos do bootcamp.

**Regra de ouro:** o LLM interpreta e conversa; **Python calcula e valida**; o LangGraph decide o caminho.

## Mapa das fases

| Fase | O que entrega | Responsável sugerido | Conceito reforçado |
|---|---|---|---|
| 0 | Ambiente pronto | Todos | Configuração, segurança do `.env` |
| 1 | Contratos e dados | Todos (Pessoa 4 lidera os dados) | Pydantic, contratos entre componentes |
| 2 | Ferramentas de estoque e valor | Pessoa 4 e Pessoa 3 | Tools determinísticas, testes |
| 3 | Agente de Atendimento | Pessoa 2 | Prompt, tool calling |
| 4 | Agente de Pedidos | Pessoa 3 | Saída estruturada |
| 5 | Supervisor e grafo com confirmação | Pessoa 1 | Roteamento condicional, human-in-the-loop |
| 6 | Integração e testes do MVP | Todos | Cenários de demonstração |
| 7 | RAG e análise de estoque | Pessoas 2 e 4 | RAG, filtro, grade, extração, reducer |
| 8 | Comprador, revisor e MCP | Pessoas 1 e 3 | Multiagentes, MCP, versão e idempotência |
| 9 | Observabilidade e avaliação | Pessoa 4 | Langfuse, `avaliar.py` |
| 10 | Apresentação | Todos | Explicar o que foi construído |

---

## Fase 0: Preparação

1. Clone o repositório e crie o ambiente virtual (comandos no README).
2. Instale com `pip install -r requirements-dev.txt`.
3. Copie `.env.example` para `.env` e preencha a chave do OpenRouter.
4. Confira os modelos gratuitos:
   - `LLM_MODEL=openrouter/free`
   - `EMBEDDINGS_MODEL` terminado em `:free`
5. Confirme que o `.env` está no `.gitignore` e **não aparece** em `git status`.
6. Combine o fluxo de Git: uma branch por funcionalidade (`feat/agente-pedidos`, `feat/estoque`...) e Pull Request revisado por outra pessoa.

**Pronto quando:** todos conseguem rodar `pytest` (mesmo sem testes ainda) e nenhum segredo está no repositório.

---

## Fase 1: Contratos e dados

Antes de qualquer agente, defina **o que cada parte recebe e devolve**. Registre em `docs/contratos.md`.

### 1.1 Modelos Pydantic (`src/schemas/`)

Defina, no mínimo:

- `ItemPedido`: `produto`, `quantidade` (inteiro maior que zero), `personalizacoes` (lista, ex.: `["leite de aveia"]`).
- `Pedido`: lista de `ItemPedido`, `total` (preenchido só pelo Python), `confirmado` (booleano, começa `False`).
- `Intencao`: `Literal` com as intenções do supervisor (no MVP: `atendimento`, `pedido`, `fora_escopo`).

### 1.2 Dados simulados (`dados/`)

Crie arquivos JSON pequenos:

- `cardapio.json`: produtos com id, nome, categoria, preço, temperatura (quente ou gelado), alérgenos, ingredientes por unidade e se contém lactose.
- `estoque.json`: ingrediente, quantidade, unidade e quantidade mínima.
- `pedidos.json`: começa vazio (`[]`); é onde o registro do pedido grava.

Inclua propositalmente: um item sem lactose, um item gelado e doce, e **um ingrediente com estoque baixo** (o cenário 3 depende dele).

### 1.3 Estado compartilhado do grafo

Liste em `docs/contratos.md` os campos do `State` (mensagem do cliente, intenção, pedido estruturado, resultado da verificação de estoque, resposta final). Cada nó devolve **só o que mudou**.

**Pronto quando:** os quatro integrantes concordam, por escrito, com os campos e os formatos.

---

## Fase 2: Ferramentas de estoque e valor (Python puro)

Em `src/graph/tools.py` (ou `src/utils/`), crie funções **determinísticas**, sem LLM:

| Ferramenta | O que faz |
|---|---|
| `consultar_cardapio(filtros)` | Devolve produtos que atendem a filtros (gelado, sem lactose, categoria) |
| `verificar_estoque(pedido)` | Soma os ingredientes necessários e compara com o estoque |
| `calcular_valor(pedido)` | Calcula o total pelas regras de preço |
| `registrar_pedido(pedido)` | Grava em `pedidos.json` (só após confirmação) |
| `atualizar_estoque(pedido)` | Baixa os ingredientes (só após confirmação) |
| `estoque_baixo()` | Lista ingredientes abaixo do mínimo |

**Cuidados:**

- `verificar_estoque` **não altera nada**. Só `atualizar_estoque` altera.
- Trate produto inexistente e quantidade inválida com erro claro, não com exceção solta.
- Escreva os testes em `tests/` **agora**: estoque suficiente, insuficiente, produto inexistente, quantidade zero ou negativa, valor total correto.

**Pronto quando:** os testes das ferramentas passam sem nenhuma chamada ao LLM.

---

## Fase 3: Agente de Atendimento

Responsável pelas dúvidas e recomendações.

1. Crie o prompt em `src/graph/prompts/` (papel: atendente simpático que só fala de cafeteria).
2. Dê ao agente a ferramenta `consultar_cardapio` (tool calling).
3. Regra no prompt: **só recomendar o que existe no cardápio**, respeitando restrições (sem lactose, gelado, doce).
4. O nó recebe a mensagem e devolve a resposta no estado.

Teste com: "Quero uma bebida gelada, doce e sem lactose. O que vocês recomendam?"

**Pronto quando:** as recomendações vêm do cardápio e respeitam as restrições pedidas.

---

## Fase 4: Agente de Pedidos

Responsável por transformar texto em pedido.

1. Use **saída estruturada** com o modelo `Pedido` do Pydantic (`with_structured_output`).
2. Prompt: copiar produtos, quantidades e personalizações **sem inventar**. Se faltar quantidade, marcar como não informada para o sistema perguntar de volta.
3. Depois da extração, o **Python** chama `verificar_estoque` e `calcular_valor`. O LLM não calcula nada.
4. Monte o resumo do pedido (itens, personalizações, total) para a confirmação.

Teste com: "Quero dois cappuccinos com leite de aveia e um pão de queijo."

**Pronto quando:** o pedido sai estruturado e o total vem do Python, igual ao valor calculado à mão.

---

## Fase 5: Supervisor e grafo com confirmação humana

1. **Nó `classify`:** LLM com saída estruturada devolve a intenção (`atendimento`, `pedido`, `fora_escopo`).
2. **Roteamento condicional:** `route_by_intent` leva ao nó certo.
3. **Caminho do pedido:**
   `estruturar → verificar_estoque → (insuficiente: informar indisponibilidade) | (suficiente: calcular_valor → resumo → confirmação)`.
4. **Human-in-the-loop:** pause o grafo no resumo e retome com a resposta do cliente (checkpointer e `interrupt`, como na Semana 1).
   - Cliente confirmou → `registrar_pedido` e `atualizar_estoque`.
   - Cliente não confirmou → encerra **sem registrar e sem mexer no estoque**.
5. **Nó `refuse`:** resposta educada para assuntos fora da cafeteria.
6. Monte o `builder.py` e ligue tudo.

**Pronto quando:** os três cenários do README funcionam de ponta a ponta e o estoque só muda após o "sim".

---

## Fase 6: Integração e testes do MVP

Cubra, com testes automatizados (as funções de roteamento e as ferramentas são testáveis sem LLM):

- produto existente e produto inexistente;
- estoque suficiente e insuficiente;
- quantidade inválida ou não informada;
- cancelamento antes da confirmação;
- pedido confirmado;
- pergunta fora do escopo;
- **estoque só atualiza após a confirmação**;
- valores calculados conferem com as regras em Python.

Faça uma rodada manual com cada cenário de demonstração. Use poucas chamadas reais ao LLM (limite diário do plano gratuito).

**Fim do MVP.** A partir daqui, a versão completa.

---

## Fase 7: RAG e análise de estoque

### 7.1 Documentos

Em `dados/`, crie:

- `manual_cafeteria.txt`: seções com `##` (receitas e gramas por dose, validade de leite e grãos, alérgenos, política de desconto, estoque mínimo, **fator de dia de pico**).
- `relatorio_estoque.txt`: uma seção `##` por item (lote de grãos, data da torra, quantidade, mínimo, consumo diário).
- `avaliacao.json`: cerca de 9 perguntas com os termos esperados na resposta.

### 7.2 Busca (`src/utils/vector_store.py`)

- Indexe os dois documentos, dividindo por seção, e coloque `doc` no metadado.
- Crie `buscar(pergunta, doc, k)` com **filtro por documento**.
- Para perguntas que comparam todos os itens, use `k` grande para trazer **todas** as seções do relatório.

### 7.3 Novos nós

- `classify` ganha as intenções `regra` e `analise`.
- Caminho `regra`: `retrieve_regras → grade → generate | nao_encontrado`. Se o manual não tiver a resposta, devolve "Não encontrado no manual da cafeteria" (não inventa).
- Caminho `analise`: `retrieve_estoque → retrieve_regras_calculo → extract_estoque → prepare → analyze ⇄ tools → format`.
- `extract_estoque`: saída estruturada transformando o relatório em lista de itens, copiando os valores.
- Campo `fontes` no estado com **reducer** (`operator.add`) para acumular fontes de vários nós.

### 7.4 Ferramentas da análise

| Ferramenta | Papel |
|---|---|
| `estoque_ok(quantidade, minimo)` | O item está acima do mínimo? |
| `consumo_efetivo(consumo_base, dia_de_pico, fator_pico)` | Consumo real; o **fator de pico vem do manual**, não do código |
| `dias_de_estoque(quantidade, consumo)` | Em quantos dias o item acaba |

O modelo precisa ler o fator no manual e passá-lo à ferramenta. Se o manual mudar, o comportamento muda sem alterar o código.

Teste: "Qual item acaba primeiro?" e "Algum item está abaixo do mínimo?".

**Pronto quando:** as três intenções seguem caminhos diferentes, uma pergunta sem base termina em "não encontrado" e as ferramentas (não o LLM) fazem as contas.

---

## Fase 8: Comprador, revisor e MCP

### 8.1 Servidor MCP (`mcp_server/server.py`)

Processo **separado**, em outro terminal. Duas ferramentas:

- `get_shop_state()`: itens de estoque com `state_version`.
- `create_restock_order(item_id, qty, expected_state_version, idempotency_key)`: valida, confere a versão, aplica e incrementa a versão. É **idempotente**.

Regras do servidor:

| Regra | Efeito |
|---|---|
| Chave repetida | Devolve a resposta original, com `duplicate: true`, sem alterar de novo |
| Versão velha | Erro `STATE_VERSION_CONFLICT` |
| Item inexistente ou quantidade fora do passo | Erro `INVALID_SCHEMA` |
| Só respostas de sucesso são memorizadas | Erros permitem nova tentativa com dados corretos |

Chave sugerida: `cafe:<item>:RESTOCK:v<versao>`.

### 8.2 Teste direto das ferramentas (`scripts/testar_mcp.py`, sem LLM)

Nesta ordem, com o servidor recém-iniciado:

1. reposição válida → `committed`, versão sobe;
2. mesma chamada de novo → `duplicate: true`, versão não muda;
3. outra chave com versão velha → `STATE_VERSION_CONFLICT`;
4. quantidade inválida → `INVALID_SCHEMA`.

Reinicie o servidor antes de rodar o grafo.

### 8.3 Grafo da ação

```text
ler_estado → comprador → revisor → validar → aprovacao_gerente → executar → (reler | confirmar)
                           └ rejeitado 2x → escalar
```

- **comprador** (LLM): propõe item e quantidade, com justificativa.
- **revisor** (LLM, independente): aprova ou rejeita com motivo. O laço volta ao comprador com no máximo **2 rodadas**; depois, `escalar`.
- **validar** (código): confere múltiplos da embalagem, orçamento e item válido, **mesmo com o revisor tendo aprovado**.
- **aprovacao_gerente** (human-in-the-loop): obrigatória para compra acima de um valor ou descarte de lote.
- **executar** (MCP, assíncrono): envia `expected_state_version` e `idempotency_key`.
- **reler:** em `STATE_VERSION_CONFLICT`, relê o estado e decide de novo (no máximo 2 tentativas). Não repete a mesma chamada às cegas.
- Nós que chamam o MCP são `async def`; use `ainvoke` e `asyncio.run`.

### 8.4 Experimento de conflito

Com `SIMULAR_CONFLITO=1`, na primeira tentativa envie `state_version - 1`. O log deve mostrar a primeira tentativa rejeitada e a segunda concluída.

### 8.5 Defesa em camadas

| Camada | Garante |
|---|---|
| Revisor (LLM) | Julga a proposta |
| `validar` (código) | Regras de negócio, independente do LLM |
| Servidor MCP | Versão e idempotência, independente do cliente |

**Pronto quando:** o estado do servidor só muda com revisor aprovando, validação passando e gerente confirmando, e repetir o comando não altera o estado de novo.

---

## Fase 9: Observabilidade e avaliação

1. Configure o Langfuse no `.env` (opcional). Sem ele, use `graph.stream(..., stream_mode="updates")` como trace local.
2. Rode um pedido e uma pergunta de regra e compare: qual nó demorou mais, quantas chamadas ao LLM, quantos tokens.
3. Crie `scripts/avaliar.py`: percorre `dados/avaliacao.json`, roda o grafo e confere se a resposta **contém** os termos esperados. Imprime a taxa de acerto.
4. Compare o custo em tokens entre os caminhos (`regra` costuma ser mais barato que `analise` e `acao`).

**Pronto quando:** `avaliar.py` roda todas as perguntas e reporta a taxa de acerto.

---

## Fase 10: Apresentação

Roteiro sugerido (cerca de 15 minutos):

1. **Problema:** erro de pedido, item indisponível, estoque sem controle.
2. **Princípio:** a IA interpreta, o Python calcula, o LangGraph coordena.
3. **Demo 1:** pedido com confirmação humana.
4. **Demo 2:** recomendação (atendimento).
5. **Demo 3:** item indisponível (nada é registrado).
6. **Demo 4 (completa):** pergunta de regra com "não encontrado".
7. **Demo 5 (completa):** reposição com revisor, aprovação do gerente, conflito de versão e idempotência.
8. **Trace:** mostrar o caminho dos nós e o custo em tokens.
9. **Aprendizados e próximos passos.**

### Perguntas que os colegas podem fazer

- Por que o estoque é uma ferramenta Python e não um agente?
- Por que validar em código se o revisor já aprovou?
- O que acontece se o cliente nunca confirmar?
- Por que repetir um comando com a mesma chave é seguro?
- Por que o fator de pico fica no manual e não no código?

---

## Checklist final

- [ ] `.env` fora do Git; `.env.example` sem valores reais
- [ ] Estoque só atualiza após a confirmação
- [ ] Valores calculados em Python
- [ ] Pergunta sem base termina em "não encontrado"
- [ ] Servidor MCP em processo separado (versão completa)
- [ ] Repetir o mesmo comando não altera o estado de novo
- [ ] Testes passando (`pytest`)
- [ ] `avaliar.py` reporta a taxa de acerto
- [ ] README atualizado com os nomes da equipe
