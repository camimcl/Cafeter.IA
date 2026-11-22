# Padronização do projeto Cafeter.IA

Este guia vale para **todos os integrantes**. O objetivo é que o código de quatro pessoas pareça escrito por uma só, e que ninguém perca tempo adivinhando nomes, formatos ou onde cada coisa fica.

Em caso de dúvida, vale o que está aqui. Para mudar uma regra, abra um Pull Request neste arquivo e combine com a equipe.

> Itens marcados com **[a confirmar]** são sugestões. Decidam juntos na primeira reunião e removam a marca.

---

## 1. Idioma

| O quê | Idioma |
|---|---|
| Documentação, README, comentários, docstrings | Português (pt-BR) |
| Mensagens mostradas ao cliente e prompts dos agentes | Português (pt-BR), tom simpático e direto |
| Nomes de funções, variáveis, arquivos, pastas e campos | Português, **sem acento e sem cedilha** (`calcular_total`, `quantidade`, `personalizacoes`) |
| Termos técnicos consagrados | Ficam em inglês (`State`, `prompt`, `tool`, `retry`, `stub`, `mock`, `idempotency_key`, `duplicate`) |
| Mensagens de commit | Português |

Misturar é aceitável **só** nos casos da tabela. Evite criar nomes como `calcularTotal` ou `get_pedido_total`.

## 2. Nomenclatura

| Elemento | Padrão | Exemplo |
|---|---|---|
| Arquivos e pastas | `snake_case`, sem acento | `estruturar_pedido.py` |
| Funções e variáveis | `snake_case` | `verificar_estoque`, `total_centavos` |
| Classes (inclui modelos Pydantic) | `PascalCase` | `Pedido`, `ItemPedido` |
| Constantes | `MAIUSCULAS_COM_UNDERSCORE` | `MAX_QUANTIDADE_POR_ITEM` |
| Campos de JSON e de modelos | `snake_case` | `sem_lactose`, `quantidade_minima` |
| Ferramentas MCP | Os nomes do documento do projeto, sem alterar | `consultar_cardapio`, `verificar_estoque`, `registrar_pedido` |

Regras de nomes:
- Nomes dizem **o que é** ou **o que faz**. Prefira `quantidade_em_estoque` a `qtd` ou `q`.
- Funções que **respondem sim ou não** começam com `tem_`, `e_` ou `esta_` (`esta_disponivel`).
- Funções que **só leem** não alteram nada. Funções que alteram deixam isso claro no nome (`registrar_`, `atualizar_`, `baixar_`).
- Sem abreviações obscuras. Abreviações permitidas: `id`, `qtd` apenas em variáveis locais curtas, `mcp`, `llm`.

## 3. Vocabulário fixo (glossário)

Use sempre estes termos, com este significado. Isso evita que duas pessoas chamem a mesma coisa de nomes diferentes.

| Termo | Significado |
|---|---|
| **cardápio** | Lista de produtos vendidos, com preço e características |
| **produto** | Algo vendido (ex.: cappuccino, pão de queijo) |
| **personalização** | Variação escolhida pelo cliente (ex.: leite de aveia) |
| **item do pedido** | Um produto + quantidade + personalizações |
| **pedido** | Conjunto de itens do pedido de um cliente |
| **ingrediente** | Insumo que compõe um produto (ex.: leite, café, farinha) |
| **receita** | Quais ingredientes e quanto de cada um um produto consome |
| **estoque** | Quantidade disponível de cada ingrediente |
| **intenção** | O que o cliente quer fazer (`atendimento`, `pedido`, `fora_escopo`) |
| **nó** | Uma etapa do grafo do LangGraph |
| **ferramenta (tool)** | Função que um agente chama; as do MCP vêm do servidor |

## 4. Estrutura de pastas e donos

Cada arquivo tem **um dono**. Só o dono edita. Quem precisa de mudança pede ao dono (conversa ou Pull Request). Isso evita conflitos de merge.

```text
Cafeter.IA/
├── docs/                    # todos: docs; contratos.md é guardado pela Pessoa 1
├── dados/
│   ├── cardapio.json        # Pessoa 2 (conteúdo)
│   ├── estoque.json         # Pessoa 4
│   ├── receitas.json        # Pessoa 4
│   └── pedidos.json         # Pessoa 4 (gerado pelo servidor)
├── mcp_server/              # Pessoa 4
├── scripts/                 # Pessoa 4 (testar_mcp.py); demais, quem criar
├── src/
│   ├── app/main.py          # Pessoa 1
│   ├── graph/
│   │   ├── state.py         # Pessoa 1
│   │   ├── builder.py       # Pessoa 1
│   │   ├── routing.py       # Pessoa 1
│   │   ├── nodes/           # cada nó tem o dono indicado na divisão
│   │   └── prompts/         # cada prompt tem o dono do seu nó
│   ├── schemas/             # cada modelo tem o dono indicado na divisão
│   └── utils/               # llm_adapter (Pessoa 1), mcp_client e stub (Pessoa 4)
└── tests/                   # cada teste fica com o dono do módulo testado
```

A tabela completa de donos por arquivo está em [`divisao-de-responsabilidades.md`](divisao-de-responsabilidades.md).

**Um nó, um arquivo, uma função:** o arquivo `nodes/estruturar_pedido.py` contém a função `estruturar_pedido`. O nome do arquivo e o nome da função são iguais ao nome do nó no grafo.

## 5. Regras do grafo e do estado

- O estado (`State`) é um `TypedDict` com `total=False`, definido só em `src/graph/state.py`.
- **Cada nó devolve apenas o que mudou**, em um dicionário. Nunca devolve o estado inteiro.
- Nenhum nó altera o estado recebido; ele devolve um dicionário novo.
- Funções de roteamento ficam em `routing.py`, começam com `route_` e devolvem uma **string** com o nome do caminho (`route_by_intent`, `route_after_confirm`).
- Quem precisa de um campo novo no estado pede à Pessoa 1, que atualiza `state.py` e `docs/contratos.md` no mesmo Pull Request.
- Prompts ficam em `src/graph/prompts/<nome>_prompt.py`, em uma constante `NOME_PROMPT`. Nunca deixe texto de prompt solto dentro do nó.

## 6. LLM, ferramentas e regras de negócio

**Princípio do projeto:** a IA interpreta e orienta; as ferramentas executam; o Python valida e calcula; o MCP padroniza a comunicação; o LangGraph coordena.

- O LLM **nunca** calcula valores, nunca decide se há estoque e nunca confirma pedidos. Isso é Python.
- O LLM é obtido **sempre** pela função `get_llm()` de `src/utils/llm_adapter.py`. Não crie clientes de LLM em outros lugares.
- Quando o LLM devolve dados, use **saída estruturada** com um modelo Pydantic (nunca peça JSON em texto livre).
- Funções de regra de negócio (`calcular_total`, `validar_quantidade`) são **puras**: recebem dados, devolvem resultado, não chamam LLM nem MCP. Assim são fáceis de testar.
- Só **modelos gratuitos** do OpenRouter (`openrouter/free`; embeddings `:free`). Limite de cerca de 50 requisições por dia, então **testes automatizados nunca chamam o LLM**.

## 7. Dados e formatos

- Dinheiro é guardado em **centavos, como inteiro** (`preco_centavos: 1800` significa R$ 18,00). Nunca use `float` para dinheiro. A conversão para texto (`R$ 18,00`) acontece só na hora de mostrar ao cliente **[a confirmar]**.
- Quantidades de ingredientes usam sempre a mesma unidade por ingrediente (gramas, mililitros ou unidades), escrita no campo `unidade`.
- Identificadores são textos em `snake_case` e estáveis: `cappuccino`, `leite_aveia`, `pao_de_queijo`.
- JSON com indentação de 2 espaços, codificação UTF-8 e chaves em `snake_case`.
- Os dados são **fictícios**. Nada de dados pessoais reais.

## 8. Erros e respostas das ferramentas

Toda ferramenta do MCP devolve um dicionário no mesmo formato:

```json
{"ok": true,  "dados": { ... }}
{"ok": false, "erro": {"codigo": "ESTOQUE_INSUFICIENTE", "mensagem": "Faltam 200 ml de leite de aveia."}}
```

Códigos de erro padronizados (novos códigos entram neste arquivo antes de serem usados):

| Código | Quando |
|---|---|
| `PRODUTO_INEXISTENTE` | O produto não está no cardápio |
| `QUANTIDADE_INVALIDA` | Quantidade zero, negativa, fracionada ou ausente |
| `ESTOQUE_INSUFICIENTE` | Falta ingrediente para o pedido |
| `PEDIDO_INVALIDO` | Estrutura do pedido fora do contrato |
| `MCP_INDISPONIVEL` | O servidor MCP não respondeu |
| `ERRO_INTERNO` | Falha inesperada da ferramenta |

- Erros esperados do negócio são **dados** (`ok: false`), não exceções.
- Exceções ficam para falhas inesperadas. Nunca engula uma exceção em silêncio.
- Mensagem ao cliente é amigável e em português; a mensagem técnica vai para o log.

## 9. Estilo de código

- Python **3.13** (todos usam a mesma versão; confira com `python --version`).
- **Type hints** em todas as funções públicas.
- **Docstring curta** (uma ou duas linhas, em português) em toda função pública e em toda ferramenta MCP. No MCP, a docstring vira a descrição que o modelo lê, então escreva com clareza.
- Formatação e imports: `ruff` (linha máxima de 100 caracteres, configurada no `pyproject.toml`). Rode antes de cada commit:
  ```bash
  ruff check . --fix
  ruff format .
  ```
- Funções pequenas, com uma responsabilidade. Se passou de cerca de 30 linhas, provavelmente dá para dividir.
- Sem `print` de depuração no código que vai para o repositório. Use `logging`. O `print` fica só em `src/app/main.py`.
- Comentários explicam o **porquê**, não o óbvio.
- Nada de números mágicos: use constantes nomeadas.

## 10. Testes

- Ferramenta: `pytest`. Arquivos em `tests/` com nome `test_<modulo>.py`.
- Nome de teste descreve o comportamento: `test_estoque_so_atualiza_apos_confirmacao`.
- **Testes não chamam LLM nem a internet.** Use dados fixos, stubs e funções puras.
- Quem escreve o código escreve os testes dele. Cobertura mínima: casos felizes e cada caso de erro listado na seção 8.
- Chamadas reais ao LLM ficam em scripts manuais (`scripts/`), usados com moderação por causa do limite diário.
- Antes de abrir um Pull Request, `pytest` precisa passar.

## 11. Git e Pull Requests

- Nunca commitar direto na `main`.
- Nome de branch: `tipo/area-assunto`, em minúsculas e com hífens.
  - Exemplos: `feat/pedidos-estruturar`, `fix/estoque-baixa-duplicada`, `docs/padronizacao`.
  - Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
- Mensagem de commit: `tipo(area): resumo curto no imperativo`, em português.
  - Exemplos: `feat(pedidos): estruturar pedido com Pydantic`, `fix(mcp): impedir baixa de estoque duplicada`.
- Commits pequenos e focados: uma ideia por commit.
- **Pull Request:** descreva o que mudou e como testar. Precisa de **1 aprovação de quem não é o autor** antes do merge. O dono do arquivo tocado deve ser um dos revisores.
- Atualize a sua branch com a `main` antes de abrir o PR (`git pull origin main`).
- Merge feito pelo autor depois da aprovação; apague a branch depois.

## 12. Segurança e segredos

- O arquivo `.env` **nunca** vai para o Git. Só o `.env.example` (sem valores reais) é versionado.
- Nunca imprima, registre em log, cole em chat ou em issue o valor de uma chave.
- Se uma chave vazar, gere uma nova imediatamente e avise a equipe.
- Antes de cada commit, confira `git status` e veja se não há `.env` na lista.

## 13. Checklist de pronto (Definition of Done)

Uma tarefa só está pronta quando:

- [ ] Segue os nomes e o vocabulário deste guia
- [ ] Respeita o contrato em `docs/contratos.md` (entradas e saídas)
- [ ] Tem docstring e type hints
- [ ] Tem testes que passam (`pytest`), sem chamar o LLM
- [ ] `ruff check .` não aponta problemas
- [ ] Nenhum segredo no commit
- [ ] Pull Request aprovado por outra pessoa
- [ ] Documentação atualizada, se algo mudou de contrato
