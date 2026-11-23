"""Ferramentas da cafeteria, como funções puras.

As funções recebem os dados já carregados e devolvem a resposta no formato do
contrato ({"ok": ..., "dados": ...}). Não leem arquivos nem dependem do servidor,
por isso o servidor MCP e o stub do cliente podem reaproveitá-las.
"""

from copy import deepcopy


def resposta_ok(dados: dict) -> dict:
    """Monta a resposta de sucesso no formato do contrato."""
    return {"ok": True, "dados": dados}


def resposta_erro(codigo: str, mensagem: str) -> dict:
    """Monta a resposta de erro de negócio no formato do contrato."""
    return {"ok": False, "erro": {"codigo": codigo, "mensagem": mensagem}}


def tem_opcao_sem_lactose(produto: dict) -> bool:
    """Diz se o produto é sem lactose ou fica sem lactose com alguma personalização."""
    if produto["sem_lactose"]:
        return True
    return any(p.get("torna_sem_lactose", False) for p in produto["personalizacoes"])


def e_compativel(produto: dict, filtros: dict) -> bool:
    """Diz se o produto atende a todos os filtros informados (filtro None é ignorado)."""
    temperatura = filtros.get("temperatura")
    if temperatura is not None and produto["temperatura"] != temperatura:
        return False

    categoria = filtros.get("categoria")
    if categoria is not None and produto["categoria"] != categoria:
        return False

    doce = filtros.get("doce")
    if doce is not None and produto["doce"] != doce:
        return False

    # Só "sem_lactose=True" restringe: "False" significa que o cliente não pediu isso,
    # e não que ele quer um produto com lactose.
    if filtros.get("sem_lactose") is True and not tem_opcao_sem_lactose(produto):
        return False

    preco_maximo = filtros.get("preco_maximo_centavos")
    if preco_maximo is not None and produto["preco_centavos"] > preco_maximo:
        return False

    return True


def consultar_cardapio(produtos: list[dict], filtros: dict | None = None) -> dict:
    """Filtra o cardápio pelos filtros informados. Sem filtros, devolve todos os produtos.

    Filtros aceitos (todos opcionais, combinados com E): temperatura, sem_lactose,
    doce, categoria e preco_maximo_centavos.
    """
    filtros = filtros or {}
    compativeis = [deepcopy(p) for p in produtos if e_compativel(p, filtros)]
    return resposta_ok({"produtos": compativeis})


# --- verificar_estoque ---


def e_quantidade_valida(quantidade: object) -> bool:
    """Diz se a quantidade é um inteiro maior que zero (bool e número fracionado não valem)."""
    return isinstance(quantidade, int) and not isinstance(quantidade, bool) and quantidade > 0


def validar_item(item: object, receitas: dict) -> dict | None:
    """Devolve a resposta de erro do primeiro problema do item, ou None se ele for válido."""
    if not isinstance(item, dict) or not isinstance(item.get("produto_id"), str):
        return resposta_erro("PEDIDO_INVALIDO", "Cada item precisa de um produto_id em texto.")

    produto_id = item["produto_id"]
    if produto_id not in receitas:
        return resposta_erro("PRODUTO_INEXISTENTE", f"O produto '{produto_id}' não existe.")

    if not e_quantidade_valida(item.get("quantidade")):
        mensagem = f"A quantidade de '{produto_id}' precisa ser um número inteiro maior que zero."
        return resposta_erro("QUANTIDADE_INVALIDA", mensagem)

    personalizacoes = item.get("personalizacoes", [])
    if not isinstance(personalizacoes, list):
        return resposta_erro("PEDIDO_INVALIDO", "As personalizações precisam ser uma lista.")

    disponiveis = receitas[produto_id]["personalizacoes"]
    for personalizacao in personalizacoes:
        if personalizacao not in disponiveis:
            mensagem = f"O produto '{produto_id}' não tem a personalização '{personalizacao}'."
            return resposta_erro("PEDIDO_INVALIDO", mensagem)

    return None


def aplicar_acoes(ingredientes: dict[str, int], acoes: list[dict]) -> dict[str, int]:
    """Aplica as ações de uma personalização (substituir, adicionar, remover) a uma receita."""
    resultado = dict(ingredientes)
    for acao in acoes:
        ingrediente = acao["ingrediente"]
        match acao["acao"]:
            case "substituir":
                if ingrediente in resultado:
                    quantidade = resultado.pop(ingrediente)
                    resultado[acao["por"]] = resultado.get(acao["por"], 0) + quantidade
            case "adicionar":
                resultado[ingrediente] = resultado.get(ingrediente, 0) + acao["quantidade"]
            case "remover":
                resultado.pop(ingrediente, None)
            case desconhecida:
                raise ValueError(f"Ação de receita desconhecida: {desconhecida}")
    return resultado


def consumo_do_item(item: dict, receitas: dict) -> dict[str, int]:
    """Calcula quanto de cada ingrediente um item do pedido consome (receita x quantidade)."""
    receita = receitas[item["produto_id"]]
    ingredientes = {i["ingrediente"]: i["quantidade"] for i in receita["ingredientes"]}

    # dict.fromkeys tira repetições mantendo a ordem: a mesma personalização vale uma vez.
    for personalizacao in dict.fromkeys(item.get("personalizacoes", [])):
        ingredientes = aplicar_acoes(ingredientes, receita["personalizacoes"][personalizacao])

    return {nome: qtd * item["quantidade"] for nome, qtd in ingredientes.items()}


def consumo_do_pedido(itens: list[dict], receitas: dict) -> dict[str, int]:
    """Soma o consumo de ingredientes de todos os itens do pedido."""
    total: dict[str, int] = {}
    for item in itens:
        for ingrediente, quantidade in consumo_do_item(item, receitas).items():
            total[ingrediente] = total.get(ingrediente, 0) + quantidade
    return total


def calcular_faltas(consumo: dict[str, int], estoque: list[dict]) -> list[dict]:
    """Compara o consumo com o estoque e lista o que falta, no formato do contrato."""
    por_id = {ingrediente["id"]: ingrediente for ingrediente in estoque}
    faltas = []
    for ingrediente, necessario in consumo.items():
        if ingrediente not in por_id:
            raise ValueError(f"Ingrediente '{ingrediente}' da receita não existe no estoque.")
        disponivel = por_id[ingrediente]["quantidade"]
        if necessario > disponivel:
            faltas.append(
                {
                    "ingrediente": ingrediente,
                    "faltam": necessario - disponivel,
                    "unidade": por_id[ingrediente]["unidade"],
                }
            )
    return faltas


def verificar_estoque(itens: list[dict], receitas: dict, estoque: list[dict]) -> dict:
    """Verifica se há ingredientes para o pedido inteiro. Não altera nada.

    Devolve {"suficiente": bool, "faltas": [{ingrediente, faltam, unidade}]} ou um erro
    PRODUTO_INEXISTENTE, QUANTIDADE_INVALIDA ou PEDIDO_INVALIDO.
    """
    if not isinstance(itens, list) or not itens:
        return resposta_erro("PEDIDO_INVALIDO", "O pedido precisa ter pelo menos um item.")

    for item in itens:
        erro = validar_item(item, receitas)
        if erro is not None:
            return erro

    faltas = calcular_faltas(consumo_do_pedido(itens, receitas), estoque)
    return resposta_ok({"suficiente": not faltas, "faltas": faltas})
