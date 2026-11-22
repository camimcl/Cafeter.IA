# Divisão de responsabilidades do Cafeter.IA

Este documento quebra o projeto em **etapas pequenas, com dono único**, para quatro pessoas trabalharem em paralelo sem pisar uma na outra. Ele complementa a divisão geral do documento [`CafeterIA.md`](CafeterIA.md) e segue os padrões de [`padronizacao.md`](padronizacao.md).

## 1. Como esta divisão evita conflitos

Na divisão geral, havia pontos em que as responsabilidades se cruzavam. Cada um foi resolvido assim:

| Problema encontrado | Decisão |
|---|---|
| A Pessoa 4 (MCP e dados) era gargalo: todos dependiam dela | A Pessoa 4 entrega **no início** um *stub* (versão falsa, com dados fixos) do cliente MCP. Os outros trabalham nele e trocam pelo real na integração |
| O cliente MCP não tinha dono | Dono: **Pessoa 4**. Todos usam uma única função, `chamar_ferramenta` |
| Quem converte "cappuccino com leite de aveia" em ingredientes? | **Pessoa 4**, dentro da ferramenta `verificar_estoque`, usando `receitas.json`. A Pessoa 3 só envia produto, quantidade e personalizações |
| Cálculo de valor (Pessoa 3) usa preços do cardápio | A Pessoa 3 lê os preços do cardápio guardado no estado pelo nó `carregar_cardapio`. O contrato do cardápio é fixado no dia 1 |
| Como o LLM conhece os ids válidos de produtos e personalizações? | Novo nó `carregar_cardapio` (Pessoa 3), **antes** de `estruturar_pedido`: busca o cardápio no MCP e guarda no estado |
| Pedido gravado duas vezes (reenvio ou confirmação repetida) | `idempotency_key` **obrigatória** em `registrar_pedido`: gerada uma vez por pedido, no `montar_resumo`, e guardada no estado. O servidor devolve o pedido já registrado em vez de gravar de novo |
| Quem implementa a pausa de confirmação humana? | **Pessoa 1** (o nó e a retomada). A Pessoa 3 só entrega o texto do resumo |
| `state.py` (Pessoa 1) e `Pedido` (Pessoa 3) se tocam | O `State` guarda o pedido como dicionário validado pelo modelo da Pessoa 3. Cada um edita só o seu arquivo |
| Testes integrados sem dono | **Pessoa 2** (ver seção 6) |
| Carga desigual (Pessoa 2 mais leve, Pessoa 4 mais pesada) | A Pessoa 2 assume o conteúdo do cardápio, os testes integrados e o roteiro da demonstração |

**Regras de convivência:**
1. **Dono único por arquivo.** Só o dono edita. Os outros pedem a mudança.
2. **Contrato antes de código.** O que cada parte recebe e devolve fica em `docs/contratos.md` antes de qualquer implementação.
3. **Contratos só mudam com aviso.** Mudança de contrato é um Pull Request que **todos** aprovam.
4. **Stubs primeiro.** Ninguém espera o outro terminar.
5. **Pull Requests pequenos**, um por etapa concluída.

## 2. Contratos essenciais (definir no Marco 0)

Estes são os pontos de encontro entre as pessoas. Os detalhes finais vão em `docs/contratos.md`.

### 2.1 Cliente MCP (dono: Pessoa 4)

```python
async def chamar_ferramenta(nome: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do MCP. Sempre devolve {"ok": ...}; nunca levanta exceção."""
```

Se o servidor não responder, devolve `{"ok": False, "erro": {"codigo": "MCP_INDISPONIVEL", "mensagem": "..."}}`.

### 2.2 Ferramentas do MCP (dono: Pessoa 4)

| Ferramenta | Entrada | Saída (`dados`) |
|---|---|---|
| `consultar_cardapio` | filtros opcionais: `temperatura`, `sem_lactose`, `doce`, `categoria`, `preco_maximo_centavos` | `produtos`: lista com `id`, `nome`, `categoria`, `descricao`, `preco_centavos`, `temperatura`, `doce`, `sem_lactose`, `alergenos`, `personalizacoes` (cada uma com `id`, `nome`, `acrescimo_centavos`, `torna_sem_lactose`) |
| `verificar_estoque` | `itens`: lista de `{produto_id, quantidade, personalizacoes}` | `suficiente` (booleano) e `faltas`: lista de `{ingrediente, faltam, unidade}`. **Não altera nada** |
| `registrar_pedido` | `itens`, `total_centavos` e `idempotency_key` (**obrigatória**) | `pedido_id`, `total_centavos` e `duplicate` (booleano). Registra o pedido e baixa o estoque (tudo ou nada). A mesma chave de novo devolve o pedido já registrado com `duplicate: true`, sem baixar o estoque outra vez |

Regras completas (filtro `sem_lactose` e idempotência) em [`contratos.md`](contratos.md), seções 3.1 e 3.2.

### 2.3 Pedido (dono: Pessoa 3)

```text
ItemPedido: produto_id (texto), quantidade (inteiro > 0), personalizacoes (lista de ids)
Pedido:     itens (lista de ItemPedido), total_centavos (preenchido só pelo Python)
```

### 2.4 Campos do estado compartilhado (dono: Pessoa 1)

`mensagem`, `intent`, `resposta`, `quer_pedir`, `filtros_cardapio`, `cardapio`, `pedido`, `campos_faltantes`, `estoque_ok`, `faltas`, `total_centavos`, `resumo`, `idempotency_key`, `confirmado`, `pedido_id`.

### 2.5 Confirmação humana (donas: Pessoa 1 e Pessoa 3)

O grafo pausa no nó `confirmar_pedido`, mostrando o `resumo` (texto feito pela Pessoa 3). O cliente responde sim ou não, e o grafo retoma com `confirmado: true` ou `false`.

## 3. Quem é dono de cada arquivo

| Arquivo ou pasta | Dono |
|---|---|
| `src/graph/state.py`, `builder.py`, `routing.py` | Pessoa 1 |
| `src/graph/nodes/classify.py`, `confirmar_pedido.py`, `cancelar_pedido.py`, `recusar.py` | Pessoa 1 |
| `src/graph/prompts/classify_prompt.py` | Pessoa 1 |
| `src/app/main.py`, `src/utils/llm_adapter.py` | Pessoa 1 |
| `docs/contratos.md` | Pessoa 1 (guardiã; mudanças com aprovação de todos) |
| `src/graph/nodes/atendimento.py`, `src/graph/prompts/atendimento_prompt.py` | Pessoa 2 |
| `src/schemas/filtro_cardapio.py` | Pessoa 2 |
| `dados/cardapio.json` | Pessoa 2 |
| `tests/e2e/` (testes dos cenários), roteiro da demonstração | Pessoa 2 |
| `src/schemas/pedido.py` | Pessoa 3 |
| `src/graph/nodes/carregar_cardapio.py`, `estruturar_pedido.py`, `pedir_esclarecimento.py`, `verificar_disponibilidade.py`, `calcular_valor.py`, `montar_resumo.py`, `finalizar_pedido.py` | Pessoa 3 |
| `src/graph/prompts/pedido_prompt.py` | Pessoa 3 |
| `src/utils/valores.py` (cálculo e formatação de dinheiro) | Pessoa 3 |
| `mcp_server/` (servidor, repositório de dados, ferramentas) | Pessoa 4 |
| `dados/estoque.json`, `receitas.json`, `pedidos.json` | Pessoa 4 |
| `src/utils/mcp_client.py`, `mcp_stub.py`, `scripts/testar_mcp.py` | Pessoa 4 |

---

## 4. Etapas por pessoa

Cada etapa traz: **o que fazer**, **arquivos**, **depende de** e **pronto quando**. Siga a ordem numérica. As etapas que dependem de outra pessoa usam o *stub* até a integração.

### Pessoa 1: Arquitetura e Supervisor

Responsável por montar o grafo, rotear as solicitações e controlar a confirmação humana. É também quem guarda os contratos.

**1.1 Esqueleto e contratos** (Marco 0)
- Reunir a equipe e fechar o `docs/contratos.md` (seção 2 deste documento).
- Definir o `State` em `state.py` com os campos combinados.
- Arquivos: `docs/contratos.md`, `src/graph/state.py`.
- Pronto quando: os quatro aprovaram o contrato em Pull Request.

**1.2 Adaptador do LLM**
- Função `get_llm()` lendo `LLM_MODEL` e a chave do `.env`, só com modelos gratuitos.
- Arquivo: `src/utils/llm_adapter.py`.
- Pronto quando: uma chamada simples responde e a chave não aparece em nenhum log.

**1.3 Nó `classify` (supervisor)**
- Saída estruturada com `Literal["atendimento", "pedido", "fora_escopo"]`.
- Prompt separado em `classify_prompt.py`, com exemplos de cada intenção.
- Arquivos: `nodes/classify.py`, `prompts/classify_prompt.py`.
- Pronto quando: as 3 frases dos cenários do projeto e uma frase fora do assunto vão para a intenção correta.

**1.4 Roteamento**
- `route_by_intent` (devolve a string do caminho) e `route_after_confirm` (confirmado ou não).
- Arquivo: `routing.py`. Testes de roteamento sem LLM.
- Pronto quando: os testes cobrem todos os caminhos.

**1.5 Nós simples: `recusar` e `cancelar_pedido`**
- `recusar`: resposta educada para assunto fora da cafeteria.
- `cancelar_pedido`: "Pedido cancelado, nada foi registrado".
- Pronto quando: ambos não tocam em estoque nem em MCP.

**1.6 Confirmação humana (human-in-the-loop)**
- Nó `confirmar_pedido` que mostra o `resumo` e pausa o grafo, usando `interrupt` e checkpointer; retoma com `confirmado: true` ou `false`.
- Arquivo: `nodes/confirmar_pedido.py`.
- Depende de: o `resumo` da etapa 3.7 (use um texto fixo no stub).
- Pronto quando: o grafo pausa, retoma com "sim" e com "não", e o "não" nunca chega ao registro.

**1.7 Montagem do grafo**
- `builder.py` liga os nós. Comece com os nós de cada pessoa em versão stub e troque pelos reais conforme chegarem.
- O caminho do pedido começa em `carregar_cardapio` e passa pelo estado os campos `cardapio` e `idempotency_key`.
- Nós que chamam o MCP são `async def`; o grafo roda com `ainvoke`.
- Pronto quando: o grafo compila e percorre os três caminhos com os stubs.

**1.8 Aplicação de linha de comando**
- `main.py` com laço de conversa: lê a mensagem, executa o grafo, mostra a resposta e trata a pausa de confirmação.
- Pronto quando: dá para fazer o cenário 1 inteiro digitando no terminal.

**1.9 Tratamento de falhas no grafo**
- Se uma ferramenta devolver `MCP_INDISPONIVEL` ou `ERRO_INTERNO` (inclusive no `carregar_cardapio`, logo no início do pedido), o grafo responde com mensagem amigável e encerra sem registrar nada.
- Como o servidor MCP roda em outro terminal, **esquecer de subi-lo é o erro mais comum**: a mensagem deve deixar claro que o serviço não está no ar.
- Pronto quando: com o servidor desligado, o cliente recebe aviso claro.

### Pessoa 2: Agente de Atendimento, cardápio e testes integrados

Responsável pela conversa de dúvidas e recomendações, pelo conteúdo do cardápio e pela validação ponta a ponta.

**2.1 Conteúdo do cardápio**
- Criar `dados/cardapio.json` no formato do contrato: pelo menos 8 produtos, com bebidas quentes e geladas, doces e não doces, itens com e sem lactose, comidas e personalizações com acréscimo de preço e com o campo `torna_sem_lactose` (ex.: leite de aveia).
- Incluir `cappuccino`, `pao_de_queijo` e uma bebida gelada, doce e sem lactose (cenário 2).
- Pronto quando: o arquivo valida contra o contrato e a Pessoa 4 consegue ler.

**2.2 Modelo de filtros**
- `FiltroCardapio` em Pydantic: `temperatura`, `sem_lactose`, `doce`, `categoria`, `preco_maximo_centavos` (todos opcionais).
- Arquivo: `src/schemas/filtro_cardapio.py`.
- Pronto quando: valores inválidos são rejeitados.

**2.3 Prompt do atendente**
- Persona simpática, escopo só de cafeteria, regra de ouro: **só recomendar produtos que vieram da ferramenta**.
- Arquivo: `prompts/atendimento_prompt.py`.
- Pronto quando: o prompt está revisado pela Pessoa 1.

**2.4 Interpretar preferências**
- Primeira chamada ao LLM com saída estruturada: transforma "gelada, doce e sem lactose" em um `FiltroCardapio`.
- Pronto quando: as frases de teste geram os filtros esperados.

**2.5 Consultar o cardápio**
- Chamar `chamar_ferramenta("consultar_cardapio", filtros)` e tratar o `ok: false`.
- Depende de: o stub da Pessoa 4.
- Pronto quando: funciona com o stub e com o servidor real.

**2.6 Montar a recomendação**
- Segunda chamada ao LLM: escreve a resposta natural **a partir dos produtos retornados**. Sem resultados compatíveis, diz isso e sugere o mais próximo.
- Pronto quando: nenhuma resposta cita produto fora do cardápio.

**2.7 Sinalizar vontade de pedir**
- Devolver `quer_pedir: true` quando, no meio da conversa, o cliente decide pedir ("quero esse"). O supervisor então encaminha para o fluxo de pedidos.
- Arquivo: `nodes/atendimento.py`.
- Pronto quando: a flag aparece nos casos de teste combinados com a Pessoa 1.

**2.8 Testes do atendimento**
- Testes de filtros e de formatação sem LLM; casos: sem resultado, produto inexistente, pergunta ambígua.
- Pronto quando: `pytest` passa.

**2.9 Testes integrados (cenários)**
- Em `tests/e2e/`: os 3 cenários do projeto e os casos da seção "Testes e validação" do `CafeterIA.md`, com o LLM substituído por respostas fixas.
- Verificar em especial: **estoque só muda após a confirmação**, valores batem com o cálculo em Python, servidor MCP indisponível e **confirmação repetida: o pedido é registrado uma só vez e o estoque baixa uma só vez**.
- Pronto quando: todos os casos da lista de validação têm um teste.

**2.10 Roteiro da demonstração**
- Montar o passo a passo da demonstração com a ordem das falas, as frases do cliente e os resultados esperados.
- Pronto quando: a equipe ensaia o roteiro do início ao fim sem surpresas.

### Pessoa 3: Agente de Pedidos

Responsável por transformar a fala do cliente em um pedido estruturado, calcular o valor e finalizar o registro.

**3.1 Modelos do pedido**
- `ItemPedido` e `Pedido` em Pydantic, com validações: quantidade inteira maior que zero, lista de itens não vazia.
- Arquivo: `src/schemas/pedido.py`.
- Pronto quando: testes de validação passam (quantidade zero, negativa, fracionada).

**3.2 Cálculo de valores (Python puro)**
- `calcular_total(pedido, produtos)` soma `preco_centavos` + acréscimos das personalizações, vezes a quantidade. Formatação `R$ 18,00` em função separada.
- Arquivo: `src/utils/valores.py`.
- Pronto quando: testes com valores conferidos à mão passam, sem `float`.

**3.3 Carregar o cardápio**
- Nó `carregar_cardapio`: chama `consultar_cardapio` sem filtros pelo cliente MCP e guarda a lista no estado, no campo `cardapio`. É o **primeiro nó** do caminho do pedido.
- Por quê: o LLM precisa conhecer os ids válidos de produtos e personalizações, e o `calcular_valor` precisa dos preços.
- Arquivo: `nodes/carregar_cardapio.py`.
- Depende de: stub da Pessoa 4.
- Pronto quando: o campo `cardapio` chega ao estado e, com o servidor fora do ar, o nó devolve o aviso de indisponibilidade sem quebrar.

**3.4 Prompt e extração do pedido**
- Nó `estruturar_pedido`: LLM com saída estruturada devolve o `Pedido`. O prompt recebe o cardápio do estado, manda copiar o que o cliente disse, **usar só os ids do cardápio** e **não inventar**.
- Ids que não existem no cardápio são tratados na etapa 3.5.
- Arquivos: `nodes/estruturar_pedido.py`, `prompts/pedido_prompt.py`.
- Pronto quando: "dois cappuccinos com leite de aveia e um pão de queijo" vira 2 itens: `cappuccino` (com `leite_aveia`) e `pao_de_queijo`.

**3.5 Dados faltando ou inválidos**
- Nó `pedir_esclarecimento`: quando falta quantidade, o produto não existe ou a quantidade é inválida, devolve uma pergunta ao cliente em vez de seguir.
- Pronto quando: os três casos geram a pergunta certa e o fluxo não segue para o estoque.

**3.6 Verificar disponibilidade**
- Nó `verificar_disponibilidade`: chama `verificar_estoque` pelo cliente MCP e converte a resposta em `estoque_ok` e `faltas`. Mensagem clara sobre o que falta (cenário 3).
- Depende de: stub da Pessoa 4.
- Pronto quando: com o stub, 3 cappuccinos com leite de aveia dão `estoque_ok: false`.

**3.7 Calcular valor e montar o resumo**
- Nó `calcular_valor`: chama a função da 3.2 usando os preços do campo `cardapio`.
- Nó `montar_resumo`: texto com itens, personalizações e total, e **gera a `idempotency_key`** (`uuid4` em texto) **uma vez por pedido**, guardando-a no estado. Se o nó rodar de novo e a chave já existir, **não gera outra**.
- Pronto quando: o resumo bate com o cálculo manual, é entregue no campo `resumo` e a chave existe no estado e não muda ao reexecutar o nó.

**3.8 Finalizar o pedido**
- Nó `finalizar_pedido`: só roda depois de `confirmado: true`; chama `registrar_pedido` com `itens`, `total_centavos` e a `idempotency_key` do estado, e devolve a confirmação ao cliente com o número do pedido.
- Se vier `duplicate: true`, trata como **sucesso** ("seu pedido já estava registrado").
- Se o servidor estiver indisponível, pode tentar de novo **com a mesma chave**; nunca cria chave nova numa tentativa. Trata também estoque que mudou no meio do caminho.
- Pronto quando: registra uma única vez, mesmo repetindo a chamada, e, em caso de erro, não diz ao cliente que deu certo.

**3.9 Testes do pedido**
- Testes de modelos, cálculo, geração e reaproveitamento da chave, e tratamento das respostas do MCP (usando o stub), incluindo `duplicate: true`.
- Pronto quando: `pytest` passa sem chamar o LLM.

### Pessoa 4: Servidor MCP, dados e cliente

Responsável pelas ferramentas da cafeteria, pelos dados de estoque e receitas, e pela ponte entre o grafo e o MCP.

**4.1 Contrato de dados e dados iniciais** (Marco 0 e 1)
- Definir com a equipe os formatos e criar `dados/estoque.json` e `dados/receitas.json`.
- Em `receitas.json`: ingredientes por unidade de produto e **substituições por personalização** (ex.: leite de aveia substitui o leite integral).
- Montar o estoque de modo que **3 cappuccinos com leite de aveia dêem falta** (cenário 3) e 2 cappuccinos com um pão de queijo passem (cenário 1).
- Pronto quando: os cenários 1 e 3 conseguem ser reproduzidos só com os dados.

**4.2 Stub do cliente MCP (prioridade máxima)**
- `mcp_stub.py` com a mesma função `chamar_ferramenta`, devolvendo respostas fixas no formato do contrato. O stub **imita a idempotência** do `registrar_pedido` (guarda as chaves em memória e devolve `duplicate: true` na repetição). Escolha entre stub e real por uma variável de ambiente (nome a combinar, por exemplo `USAR_MCP_STUB`).
- Pronto quando: a Pessoa 2 e a Pessoa 3 conseguem rodar seus nós.
- Este é o item que destrava o resto da equipe. Entregue-o primeiro.

**4.3 Repositório de dados**
- Funções para ler e gravar os JSON com segurança (gravação completa ou nada, sem deixar arquivo pela metade).
- Arquivo: `mcp_server/repositorio.py`.
- Pronto quando: testes de leitura e gravação passam em arquivos temporários.

**4.4 Ferramenta `consultar_cardapio`**
- Lê `cardapio.json` e aplica os filtros. Sem filtros, devolve tudo.
- Filtro `sem_lactose`: produtos com `sem_lactose: true` **ou** com alguma personalização `torna_sem_lactose: true`.
- Pronto quando: testes por filtro passam (gelado, sem lactose, doce, combinados), incluindo o cappuccino aparecendo em "sem lactose" por causa do leite de aveia.

**4.5 Ferramenta `verificar_estoque`**
- Para cada item, resolve a receita, aplica as substituições, soma os ingredientes de todo o pedido e compara com o estoque. **Não altera nada.** Erros: `PRODUTO_INEXISTENTE`, `QUANTIDADE_INVALIDA`.
- Pronto quando: cenários 1 e 3 dão o resultado esperado e o estoque fica intacto.

**4.6 Ferramenta `registrar_pedido`**
- Exige `idempotency_key` (ausente ou vazia: `PEDIDO_INVALIDO`).
- **Primeiro** procura a chave nos pedidos já registrados: se existe com os mesmos itens, devolve o pedido original com `duplicate: true`, sem conferir nem baixar o estoque; se existe com itens diferentes, `PEDIDO_INVALIDO`.
- Chave nova: confere o estoque de novo (outra pessoa pode ter pedido antes), baixa os ingredientes e grava o pedido **com a chave**, **tudo ou nada**. Devolve `pedido_id` e `duplicate: false`.
- Só sucessos são guardados; erros não consomem a chave.
- Pronto quando: pedido válido baixa o estoque uma vez; repetir a mesma chave não altera nada; estoque insuficiente não grava nada.

**4.7 Servidor MCP**
- `server.py` expõe as três ferramentas com docstrings claras. Transporte **HTTP local**, como no exercício do bootcamp: o servidor roda **em outro terminal** (`python mcp_server/server.py`) e atende em `http://127.0.0.1:8000/mcp`, endereço lido da variável `MCP_URL` do `.env`.
- Documentar no README como subir o servidor antes de rodar a aplicação.
- Pronto quando: o servidor sobe em um terminal e lista as três ferramentas para um cliente em outro.

**4.8 Cliente MCP real**
- `mcp_client.py` com `chamar_ferramenta`: conecta em `MCP_URL`, descobre as ferramentas, chama, converte a resposta no formato do contrato e trata servidor indisponível (`MCP_INDISPONIVEL`). As chamadas são assíncronas.
- Pronto quando: a Pessoa 2 e a Pessoa 3 trocam o stub pelo real sem alterar o código dos nós.

**4.9 Teste independente do MCP**
- `scripts/testar_mcp.py`: chama as três ferramentas **sem LLM**, cobrindo sucesso, produto inexistente, quantidade inválida, estoque insuficiente, **chave repetida** (`duplicate: true`, estoque inalterado), chave ausente e mesma chave com itens diferentes. Mais testes automatizados em `tests/`.
- Pronto quando: roda do início ao fim com o servidor em outro terminal, e o estado é reiniciável (voltar aos dados originais).

---

## 5. Dependências entre as pessoas

| Quem precisa | De quem | O quê | Como não esperar |
|---|---|---|---|
| Pessoas 2 e 3 | Pessoa 4 | `chamar_ferramenta` | Usam o stub (etapa 4.2) |
| Pessoa 4 | Pessoa 2 | Conteúdo de `cardapio.json` | A Pessoa 4 usa um cardápio mínimo próprio nos testes |
| Pessoa 3 | Pessoa 2 | Formato do cardápio (preços) | Contrato fixado no Marco 0 |
| Pessoa 1 | Pessoas 2, 3 e 4 | Nós para ligar no grafo | Liga os stubs e troca pelos reais |
| Pessoa 1 | Pessoa 3 | Texto do `resumo` | Usa um resumo fixo até a etapa 3.7 |
| Pessoas 1 e 3 | Pessoa 1 | Campos `cardapio` e `idempotency_key` no estado | Definidos no Marco 0 em `contratos.md` |
| Pessoa 3 | Pessoa 4 | Comportamento da idempotência no `registrar_pedido` | O stub já imita (etapa 4.2) |
| Pessoa 2 | Todos | Fluxo funcionando para os testes integrados | Escreve os testes com respostas fixas antes e roda no final |

## 6. Marcos

| Marco | O que acontece | Responsáveis |
|---|---|---|
| **0. Contratos** | Fechar `contratos.md`, `State`, formatos de dados e assinaturas. Reunião com todos | Todos (Pessoa 1 conduz) |
| **1. Stubs e dados** | Stub do cliente MCP, dados iniciais, esqueleto do grafo | Pessoa 4 (stub e dados), Pessoa 1 (grafo) |
| **2. Componentes** | Cada um conclui suas etapas contra os stubs | Todos |
| **3. Integração** | Troca dos stubs pelo real: servidor MCP, nós e grafo | Pessoa 1 lidera; Pessoa 4 apoia |
| **4. Testes** | Cenários ponta a ponta, falhas, ajustes | Pessoa 2 lidera |
| **5. Apresentação** | Ensaio e demonstração | Todos |

## 7. Plano alternativo

Se a integração do MCP der problema, o `CafeterIA.md` prevê chamar as ferramentas diretamente pelo Python. Como todo o grafo usa só `chamar_ferramenta`, a troca acontece **em um único lugar** (`mcp_client.py`) e os nós das Pessoas 1, 2 e 3 não mudam.

## 8. Roteiro para alinhar com a equipe

Levem estas perguntas para a primeira reunião (30 a 40 minutos). Anotem as respostas em `docs/contratos.md`.

1. **Apresentação:** cada pessoa conta com o que já trabalhou (LangGraph, Pydantic, MCP, prompts) e qual parte quer assumir. A divisão acima é uma sugestão; troquem de papéis se fizer sentido.
2. **Contrato do cardápio e do estoque:** os campos listados na seção 2.2 estão bons? Falta algum (por exemplo, tamanho da bebida)?
3. **Personalizações:** quais existem (leite de aveia, sem açúcar, tamanho)? Algumas cobram a mais? Alteram a receita? Tornam o produto sem lactose?
4. **Dinheiro:** concordamos em centavos inteiros?
5. **Servidor MCP (HTTP):** a porta 8000 serve para todos? Quem sobe o servidor durante os testes integrados e a demonstração? (Decisão já tomada: transporte HTTP, em outro terminal.)
6. **Confirmação:** o "sim" e o "não" do cliente serão digitados no terminal? Aceitamos só "sim" e "não" ou outras formas?
7. **Mensagens de erro:** o tom das respostas está alinhado (simpático, direto, em português)?
8. **Fluxo de Git:** todos têm acesso de escrita ao repositório? Quem aprova os Pull Requests de cada área?
9. **Prazos:** quando é cada marco? Quando é a demonstração?
10. **Limite de uso do LLM:** quem testa com o LLM real e quando, já que o limite diário é pequeno?

## 9. Depois do MVP (opcional)

Os temas do bootcamp que ficaram fora do MVP podem entrar em uma segunda etapa, reaproveitando a mesma divisão: RAG sobre um manual da cafeteria (Pessoa 2), análise de estoque e comprador com revisor (Pessoas 1 e 3), versão de estado no servidor MCP (Pessoa 4) e Langfuse com avaliação automática (Pessoa 4). Detalhes no [`passo-a-passo.md`](passo-a-passo.md).
