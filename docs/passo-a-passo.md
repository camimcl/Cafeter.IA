# Passo a passo do Cafeter.IA

Este guia leva a equipe da primeira reunião até a demonstração. Ele mostra **a ordem** do trabalho. Os detalhes de cada etapa de cada pessoa estão em [`divisao-de-responsabilidades.md`](divisao-de-responsabilidades.md), e as regras de escrita em [`padronizacao.md`](padronizacao.md).

**Regra de ouro:** o LLM interpreta e conversa; **o Python calcula e valida**; as ferramentas executam; o MCP padroniza a comunicação; o LangGraph decide o caminho.

## Visão em uma tela

| Fase | Marco | O que entrega | Quem |
|---|---|---|---|
| 0 | | Ambiente pronto | Todos |
| 1 | **Marco 0** | Contratos fechados | Todos (Pessoa 1 conduz) |
| 2 | **Marco 1** | Stub do cliente MCP, dados e esqueleto do grafo | Pessoa 4 e Pessoa 1 |
| 3 | **Marco 2** | Componentes prontos, cada um contra o stub | Todos, em paralelo |
| 4 | **Marco 3** | Integração: servidor MCP real no lugar do stub | Pessoa 1 lidera |
| 5 | **Marco 4** | Testes dos cenários e das falhas | Pessoa 2 lidera |
| 6 | **Marco 5** | Ensaio e demonstração | Todos |
| 7 | | Depois do MVP (opcional): RAG, comprador e revisor, versão de estado, Langfuse | A combinar |

---

## Fase 0: Preparação

1. Clone o repositório e crie o ambiente virtual (comandos no README).
2. Instale com `pip install -r requirements-dev.txt`.
3. Copie `.env.example` para `.env` e preencha a chave do OpenRouter.
4. Use só modelos gratuitos: `LLM_MODEL=openrouter/free` e `EMBEDDINGS_MODEL` terminado em `:free`.
5. Confirme que o `.env` está no `.gitignore` e **não aparece** em `git status`.
6. Leia [`padronizacao.md`](padronizacao.md) (idioma, nomes, Git). Todos seguem o mesmo guia.
7. Combinem o fluxo de Git: uma branch por funcionalidade (`feat/pedidos-estruturar`) e Pull Request aprovado por outra pessoa.

**Pronto quando:** todos rodam `pytest` sem erro e nenhum segredo está no repositório.

---

## Fase 1: Contratos (Marco 0)

Primeira reunião da equipe, de 30 a 40 minutos. Use o roteiro de perguntas da seção 8 da [divisão de responsabilidades](divisao-de-responsabilidades.md).

O que precisa ficar escrito em [`contratos.md`](contratos.md) antes de qualquer código:

1. **Campos do estado compartilhado** (`State`).
2. **Modelos Pydantic:** `ItemPedido`, `Pedido`, `FiltroCardapio`.
3. **Assinatura do cliente MCP:** `chamar_ferramenta(nome, argumentos) -> dict`, sempre devolvendo `{"ok": ...}` e nunca levantando exceção.
4. **Contrato das três ferramentas MCP** (entradas e saídas): `consultar_cardapio`, `verificar_estoque`, `registrar_pedido`.
5. **Formato dos dados em JSON:** cardápio, estoque, receitas e pedidos.
6. **Códigos de erro:** os da [padronização](padronizacao.md#8-erros-e-respostas-das-ferramentas).
7. **Decisões:** dinheiro em centavos, servidor MCP em HTTP (porta 8000), Python 3.13, nome da variável do stub (`USAR_MCP_STUB`).
8. **Caminho do pedido:** o primeiro nó é `carregar_cardapio` (o LLM precisa dos ids válidos e o cálculo, dos preços); o estado ganha `cardapio` e `idempotency_key`.
9. **Idempotência:** `idempotency_key` obrigatória no `registrar_pedido`, gerada uma vez por pedido (regras na seção 3.2 de [`contratos.md`](contratos.md)).

**Pronto quando:** os quatro aprovaram o contrato em um Pull Request.

---

## Fase 2: Stubs, dados e esqueleto (Marco 1)

Objetivo: **ninguém ficar esperando ninguém.**

| Quem | O que | Etapa |
|---|---|---|
| Pessoa 4 | **Stub do cliente MCP** (a mesma função `chamar_ferramenta`, com respostas fixas) | 4.2 |
| Pessoa 4 | `estoque.json` e `receitas.json`, já preparados para os cenários 1 e 3 | 4.1 |
| Pessoa 2 | `cardapio.json` com pelo menos 8 produtos | 2.1 |
| Pessoa 1 | `State`, `llm_adapter`, esqueleto do `builder.py` com nós falsos | 1.1, 1.2, 1.7 |

O stub é a peça que destrava o resto. A Pessoa 4 entrega ele **primeiro**.

**Pronto quando:** a Pessoa 2 e a Pessoa 3 conseguem chamar `chamar_ferramenta` e receber respostas no formato do contrato.

---

## Fase 3: Componentes em paralelo (Marco 2)

Cada pessoa trabalha **só nos seus arquivos**, contra o stub. A ordem e os critérios de "pronto" estão na divisão de responsabilidades.

### Pessoa 1: supervisor e fluxo
- `classify` com saída estruturada (`atendimento`, `pedido`, `fora_escopo`) e `route_by_intent`.
- Nós `recusar` e `cancelar_pedido`.
- **Confirmação humana:** nó `confirmar_pedido` que pausa o grafo e retoma com sim ou não (`interrupt` e checkpointer).
- `main.py` com a conversa no terminal.
- Tratamento de falhas: servidor fora do ar, erro de ferramenta.

### Pessoa 2: atendimento e cardápio
- Prompt do atendente: só recomenda o que veio da ferramenta.
- Interpretar preferências ("gelada, doce, sem lactose") em um `FiltroCardapio` por saída estruturada.
- Chamar `consultar_cardapio` e escrever a recomendação.
- Sinalizar `quer_pedir` quando o cliente decide pedir.

### Pessoa 3: pedidos
- Modelos `ItemPedido` e `Pedido` com validações.
- Função pura `calcular_total` (centavos, sem `float`).
- Nó `carregar_cardapio`: busca o cardápio no MCP e guarda no estado, antes de tudo.
- Nó `estruturar_pedido` (saída estruturada, usa só os ids do cardápio, sem inventar dados) e `pedir_esclarecimento` (falta quantidade, produto inexistente, quantidade inválida).
- Nós `verificar_disponibilidade`, `calcular_valor` e `montar_resumo`, que também **gera a `idempotency_key`** (uma por pedido).
- Nó `finalizar_pedido` (só roda depois do "sim"): envia a mesma chave sempre e trata `duplicate: true` como sucesso.

### Pessoa 4: servidor MCP e dados
- Repositório de dados (gravação segura em JSON).
- Ferramentas `consultar_cardapio`, `verificar_estoque` (resolve receita e personalização, **não altera nada**) e `registrar_pedido` (exige a `idempotency_key`, confere o estoque de novo, grava tudo ou nada e devolve o pedido original se a chave se repetir).
- Servidor em HTTP e cliente real.
- `scripts/testar_mcp.py`, que testa as ferramentas sem LLM.

**Pronto quando:** cada pessoa tem seus testes passando (`pytest`, sem chamar o LLM) e seus nós funcionam com o stub.

---

## Fase 4: Integração (Marco 3)

Aqui o stub dá lugar ao servidor real.

1. **Teste o servidor sozinho**, sem o grafo:
   ```bash
   # Terminal 1
   python mcp_server/server.py
   # Terminal 2
   python -m scripts.testar_mcp
   ```
   Cubra: sucesso, produto inexistente, quantidade inválida, estoque insuficiente.
2. **Troque o stub pelo cliente real** (`USAR_MCP_STUB` desligado). Os nós das Pessoas 1, 2 e 3 **não devem mudar**: é o teste de que o contrato foi respeitado.
3. **Ligue os nós reais no `builder.py`**, um caminho por vez:
   - caminho do atendimento (cenário 2);
   - caminho do pedido (cenário 1);
   - estoque insuficiente (cenário 3);
   - fora do escopo.
4. **Confirme a pausa humana:** o "não" nunca chega ao `registrar_pedido`.
5. Rode o cenário 1 inteiro pelo terminal (`python -m src.app.main`), com o servidor em outro terminal.

**Problemas comuns:**
- Esquecer de subir o servidor MCP → a aplicação deve avisar que o serviço não está no ar.
- Estoque do JSON alterado por um teste anterior → o servidor precisa voltar aos dados originais para a demo.
- Contrato mudou sem aviso → volte ao `contratos.md` e corrijam juntos.

**Plano alternativo:** se o MCP travar a entrega, a troca é feita **em um único lugar** (`mcp_client.py`), chamando as funções diretamente pelo Python. Os nós não mudam, porque todos usam só `chamar_ferramenta`.

**Pronto quando:** os três cenários rodam de ponta a ponta com o servidor real.

---

## Fase 5: Testes e validação (Marco 4)

A Pessoa 2 lidera, com todos corrigindo o que aparecer.

| Caso | O que verificar |
|---|---|
| Produto existente | Pedido estruturado corretamente |
| Produto inexistente | Pergunta de esclarecimento, sem seguir para o estoque |
| Estoque suficiente | Segue para valor e resumo |
| Estoque insuficiente | Informa o que falta; **nada** é registrado |
| Quantidade inválida ou ausente | Pede esclarecimento |
| Cancelamento antes da confirmação | Encerra sem registrar e sem alterar o estoque |
| Pedido confirmado | Registra uma vez e baixa o estoque |
| Confirmação repetida ou reenvio | Mesma `idempotency_key`: devolve o pedido já registrado (`duplicate: true`); estoque baixa **uma só vez** |
| Chave ausente, ou repetida com itens diferentes | Erro `PEDIDO_INVALIDO`, nada é registrado |
| Pergunta fora do escopo | Recusa educada |
| Servidor MCP indisponível | Mensagem clara, nada registrado |
| Falha de ferramenta | Erro tratado, sem dizer ao cliente que deu certo |

Confirme também que:
- o **estoque só muda depois do "sim"**;
- os valores batem com o cálculo em Python (conferido à mão);
- nenhum teste automatizado chama o LLM.

Use poucas chamadas reais ao LLM nas rodadas manuais (limite diário do plano gratuito).

**Pronto quando:** cada caso da tabela tem um teste e `pytest` passa.

---

## Fase 6: Apresentação (Marco 5)

Roteiro sugerido (cerca de 15 minutos), montado pela Pessoa 2 e ensaiado por todos:

1. **Problema:** erro de pedido, item indisponível, estoque sem controle.
2. **Princípio:** a IA interpreta, o Python calcula, o MCP padroniza, o LangGraph coordena.
3. **Arquitetura:** o fluxo principal do README.
4. **Demo 1:** pedido com confirmação humana (cenário 1).
5. **Demo 2:** recomendação (cenário 2).
6. **Demo 3:** item indisponível; nada é registrado (cenário 3).
7. **Demo 4:** servidor MCP desligado; o sistema avisa e não registra nada.
8. **Demo 5:** confirmação repetida; o pedido não é gravado duas vezes e o estoque não baixa de novo.
9. **Aprendizados e próximos passos.**

Antes da demo: reiniciar o servidor para os dados voltarem ao estado original.

**Perguntas que os colegas podem fazer:**
- Por que o estoque é consultado por MCP e não direto no Python?
- Por que validar em código se o LLM já extraiu o pedido?
- O que acontece se o cliente nunca confirmar?
- Por que dinheiro em centavos?
- O que muda se o servidor MCP cair?
- O que impede o pedido de ser gravado duas vezes?

---

## Depois do MVP (opcional)

Estes temas reforçam o que o bootcamp ensinou. Entram quando o MVP estiver estável, reaproveitando a divisão por pessoas.

### RAG sobre o manual da cafeteria (sugestão: Pessoa 2)
- Documento `dados/manual_cafeteria.txt`: receitas, validade, alérgenos, políticas, **fator de dia de pico**.
- Busca com filtro por documento; `classify` ganha a intenção `regra`.
- Caminho `regra`: `retrieve → grade → generate`, ou "Não encontrado" quando o manual não tem a resposta.
- `fontes` no estado com reducer (`operator.add`).

### Análise de estoque (sugestão: Pessoa 4 com Pessoa 2)
- Documento `relatorio_estoque.txt`, extração estruturada em lista de itens.
- Ferramentas `estoque_ok`, `consumo_efetivo` (o fator de pico vem do manual, não do código) e `dias_de_estoque`.
- O modelo usa as ferramentas para qualquer conta; nunca calcula de cabeça.

### Comprador e revisor (sugestão: Pessoas 1 e 3)
- Agente **comprador** propõe reposição; **revisor** independente julga; laço de no máximo 2 rodadas, depois `escalar`.
- Nó `validar` em código (múltiplos da embalagem, orçamento) mesmo com o revisor aprovando.
- **Aprovação do gerente** (human-in-the-loop) para compra acima de um valor.

### Servidor MCP mais seguro (sugestão: Pessoa 4)
- Ferramenta `criar_pedido_reposicao` com `expected_state_version` (a `idempotency_key` já existe no MVP).
- Erros `STATE_VERSION_CONFLICT` (relê o estado e decide de novo, sem repetir às cegas) e `INVALID_SCHEMA`.
- Experimento de conflito com `SIMULAR_CONFLITO=1`.

### Observabilidade e avaliação (sugestão: Pessoa 4)
- Langfuse (ou `graph.stream(..., stream_mode="updates")` como trace local).
- `scripts/avaliar.py` percorre `dados/avaliacao.json` e reporta a taxa de acerto.
- Comparar o custo em tokens entre os caminhos.

---

## Checklist final do MVP

- [ ] `.env` fora do Git; `.env.example` sem valores reais
- [ ] Servidor MCP em processo separado (HTTP)
- [ ] Estoque só atualiza após a confirmação
- [ ] Valores calculados em Python, em centavos
- [ ] Servidor indisponível e falhas de ferramenta tratados
- [ ] Os três cenários funcionam de ponta a ponta
- [ ] Testes passando (`pytest`), sem chamar o LLM
- [ ] `ruff check .` sem problemas
- [ ] Documentação e README atualizados com os nomes da equipe
