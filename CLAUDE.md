# Cafeter.IA: guia para o Claude Code

Este arquivo é lido no início de cada sessão do Claude Code. Ele resume o projeto, as regras da equipe
e a forma de trabalhar. Os documentos completos estão em `docs/`; em caso de dúvida, vale o que
está lá. Este arquivo **não substitui** `docs/contratos.md` nem `docs/padronizacao.md`.

## 1. O projeto

**Cafeter.IA** é um sistema multiagente para uma cafeteria, feito como exercício do bootcamp de
agentic AI (Deloitte). Ele repete a estrutura do projeto anterior (frota de navios) em outra
temática. Quatro pessoas trabalham nele, e todos os assuntos do bootcamp precisam aparecer.

O sistema atende o cliente por texto: recomenda itens do cardápio, monta o pedido, confere o
estoque, calcula o valor, pede confirmação e registra o pedido.

**Princípio central:** a IA interpreta e orienta; as ferramentas executam; o **Python valida e
calcula**; o MCP padroniza a comunicação; o LangGraph coordena.

- O LLM **nunca** calcula valores, decide se há estoque nem confirma pedidos. Isso é Python.
- O LLM só recomenda o que veio da ferramenta (`consultar_cardapio`). Nunca inventa produto.

Conceitos do bootcamp presentes: LangGraph (StateGraph, roteamento condicional, supervisor),
agentes com ferramentas, servidor e cliente MCP, Pydantic com saída estruturada, confirmação
humana (human-in-the-loop com interrupt e checkpointer) e idempotência.

## 2. Stack e ambiente

- Python **3.13** (`requires-python = ">=3.13"`). Ambiente virtual em `.venv/` (ignorado pelo Git).
- Instalação: `pip install -r requirements-dev.txt`.
- LangGraph, LangChain, Pydantic, FastMCP, python-dotenv. Testes com `pytest`; lint com `ruff`.
- LLM pelo OpenRouter, **somente modelos gratuitos** (`LLM_MODEL=openrouter/free`, embeddings
  terminando em `:free`). Limite de cerca de 50 requisições por dia. O `get_llm()` lê
  `LLM_MODEL`, `LLM_PROVIDER`, `OPENROUTER_API_KEY` e `OPENROUTER_BASE_URL` (ver `.env.example`).
- MCP por **HTTP local**: o servidor roda em outro terminal em `http://127.0.0.1:8000/mcp`
  (variável `MCP_URL`). A porta 8000 ainda não foi confirmada pela equipe.
- Stub do cliente MCP: `USAR_MCP_STUB=1` imita o servidor, inclusive a idempotência.
- Fim de linha **LF** em todos os arquivos, fixado pelo `.gitattributes`. No Windows, não reative
  a conversão para CRLF (`core.autocrlf`): ela quebra o teste de regravação dos dados semente.
- Chamadas ao MCP são `async` (`chamar_ferramenta`), então nós que usam o MCP também são `async` e
  o grafo roda com `ainvoke`.

## 3. Regras que nunca se quebram

1. **Nunca ler, imprimir, editar nem commitar o `.env`.** Só o `.env.example` (sem valores reais) é
   versionado. Antes de todo commit, conferir `git status`.
2. **Testes não chamam o LLM nem a internet.** Usar dados fixos, stubs e funções puras.
3. **Nunca commitar direto na `main`.** Uma branch e um PR pequeno por sessão de trabalho.
4. **Mostrar tudo antes de qualquer push ou PR.** Só enviar depois de a pessoa aprovar.
5. **O autor do commit é a pessoa dona do trabalho** (a identidade do Git dela).
6. Dinheiro **sempre em centavos inteiros**. Nunca `float`.
7. Só modelos gratuitos do OpenRouter.

## 4. Padronização (resumo de `docs/padronizacao.md`)

- **Idioma:** documentação, comentários, docstrings, commits e mensagens ao cliente em português
  (pt-BR). Identificadores em português, `snake_case`, **sem acento nem cedilha**. Termos técnicos
  ficam em inglês (`State`, `prompt`, `tool`, `stub`, `idempotency_key`, `duplicate`).
- **Nomes:** classes em `PascalCase`; constantes em `MAIUSCULAS`; ferramentas MCP com os nomes do
  contrato; campos de JSON em `snake_case`.
- **Glossário:** cardápio, produto, personalização, item do pedido, pedido, ingrediente, receita,
  estoque, intenção, nó, ferramenta. Usar sempre estes termos.
- **Grafo:** `State` é `TypedDict` com `total=False`, definido só em `src/graph/state.py`. Cada nó
  devolve **só o que mudou**. Um nó = um arquivo = uma função, com o mesmo nome do nó. Funções de
  roteamento ficam em `routing.py` e começam com `route_`.
- **Prompts:** `src/graph/prompts/<nome>_prompt.py`, em uma constante `NOME_PROMPT`.
- **LLM:** obtido sempre por `get_llm()` em `src/utils/llm_adapter.py`. Dados vindos do LLM usam
  saída estruturada com Pydantic.
- **Erros das ferramentas:** `{"ok": true, "dados": {...}}` ou
  `{"ok": false, "erro": {"codigo": "...", "mensagem": "..."}}`. Códigos: `PRODUTO_INEXISTENTE`,
  `QUANTIDADE_INVALIDA`, `ESTOQUE_INSUFICIENTE`, `PEDIDO_INVALIDO`, `MCP_INDISPONIVEL`,
  `ERRO_INTERNO`. Erro de negócio é dado, não exceção.
- **Estilo:** type hints e docstring curta em funções públicas; `ruff` com linha de 100; sem
  `print` fora de `src/app/main.py` (usar `logging`); sem números mágicos.
- **Git:** branches `tipo/area-assunto` (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`).
  Commits no formato `tipo(area): resumo no imperativo`, em português. O PR precisa de 1 aprovação
  de quem não é o autor.

## 5. Arquitetura

Caminho do pedido (cada desvio termina em resposta ao cliente):

```text
classify → carregar_cardapio → estruturar_pedido → verificar_disponibilidade
  → calcular_valor → montar_resumo → confirmar_pedido → finalizar_pedido → resposta
```

Desvios: dados incompletos → `pedir_esclarecimento`; estoque insuficiente → informar
indisponibilidade; cliente disse não → `cancelar_pedido`; servidor fora do ar em qualquer passo
que chame o MCP → aviso de serviço indisponível, sem registrar nada. Pedidos de recomendação vão
para o **Agente de Atendimento**; assuntos fora do escopo são recusados.

`carregar_cardapio` vem antes de `estruturar_pedido` porque o LLM precisa dos ids válidos e o
`calcular_valor` precisa dos preços.

**Ferramentas do MCP** (donas: Pessoa 4):
- `consultar_cardapio`: filtros opcionais `temperatura`, `sem_lactose`, `doce`, `categoria`,
  `preco_maximo_centavos`.
- `verificar_estoque`: só lê; devolve `suficiente` e `faltas`.
- `registrar_pedido`: `itens`, `total_centavos` e `idempotency_key` obrigatória; devolve
  `pedido_id`, `total_centavos` e `duplicate`.

Cliente: `chamar_ferramenta(nome, argumentos) -> dict` sempre devolve `{"ok": ...}`; nunca levanta
exceção. Servidor fora do ar vira `MCP_INDISPONIVEL`.

**Sem lactose:** o filtro devolve produtos com `sem_lactose: true` **ou** com alguma
personalização `torna_sem_lactose: true`. Quem apresenta o resultado deve dizer **com qual
personalização** o item fica sem lactose. Não existe campo `vegano`.

**Idempotência de `registrar_pedido`:** a chave (`uuid4`) é gerada **uma vez por pedido** no nó
`montar_resumo` e guardada em `idempotency_key`. Reenvios usam a mesma chave. Chave repetida com
os mesmos itens devolve o pedido original com `duplicate: true`, sem alterar o estoque, e
`finalizar_pedido` trata isso como sucesso. Chave repetida com itens diferentes, ou ausente, dá
`PEDIDO_INVALIDO`. Só pedidos com sucesso guardam a chave. A chave não é hash do conteúdo.

**Confirmação humana:** o grafo pausa em `confirmar_pedido` mostrando o `resumo`. Só
`confirmado: true` chega a `finalizar_pedido`.

**Campo da intenção no estado:** `intencao` (valores `atendimento`, `pedido`, `fora_escopo`).

## 6. Quem é dono de quê

Só o dono edita o arquivo. Quem precisa de mudança pede ao dono. Detalhes por arquivo em
`docs/divisao-de-responsabilidades.md`.

| Pessoa | Área |
|---|---|
| 1 | `state.py`, `builder.py`, `routing.py`, `classify`, `confirmar_pedido`, `cancelar_pedido`, recusa, `main.py`, `llm_adapter`, guarda de `docs/contratos.md` |
| 2 | Agente de Atendimento: `nodes/atendimento.py`, `prompts/atendimento_prompt.py`, `schemas/filtro_cardapio.py`, `dados/cardapio.json`, `tests/e2e/`, roteiro da demonstração |
| 3 | Pedido: `schemas/pedido.py`, `carregar_cardapio`, `estruturar_pedido`, `pedir_esclarecimento`, `verificar_disponibilidade`, `calcular_valor`, `montar_resumo`, `finalizar_pedido`, `utils/valores.py` |
| 4 | MCP e dados: `mcp_server/`, `estoque.json`, `receitas.json`, `pedidos.json`, cliente e stub do MCP, `scripts/testar_mcp.py` |

Mudanças de contrato exigem PR aprovado por todos. Pontos ainda sem decisão estão na seção 10 de
`docs/contratos.md` (recalcular o total no servidor, cópias `.runtime.json`, limite de
quantidade por item, formato de `pedido_id`, `route_after_atendimento`).

## 7. Como trabalhar (TDD e sessões)

- **Uma sessão = uma branch = um PR pequeno**, segmentado pelas etapas de
  `docs/divisao-de-responsabilidades.md`, com os testes da etapa dentro do próprio PR.
- **TDD:** escrever o teste, ver falhar pelo motivo certo, escrever o código mínimo, ver passar,
  rodar a suíte inteira e o `ruff` nos arquivos alterados. Arquivos de teste se chamam
  `test_<modulo>.py`.
- Antes de abrir PR: atualizar a branch com a `main`, rodar `pytest` e `ruff check`, conferir que
  não há `.env` no commit.
- Se o `ruff` ou um teste falhar em arquivo de outra pessoa, **avisar** em vez de corrigir.
- Revisar PRs dos colegas conferindo: contrato, padronização, testes reais (com `assert`),
  ordem de imports e escopo do PR.

## 8. Onde ver o estado do projeto

Esta seção não lista o que já foi feito, porque envelheceria a cada merge. Para saber o estado:

- `git log --oneline main` e a lista de PRs no GitHub: o que já entrou e o que está em revisão.
- `docs/passo-a-passo.md`: as fases e os marcos do MVP.
- `docs/divisao-de-responsabilidades.md`: as etapas de cada pessoa e o critério de pronto.

## 9. Preferências pessoais

Preferências de uma pessoa só (forma de explicar, ritmo, assinatura dos commits) ficam no
`CLAUDE.local.md` dela, na raiz do projeto. Esse arquivo está no `.gitignore` e o Claude Code o lê
junto com este. Não coloque preferências pessoais aqui.
