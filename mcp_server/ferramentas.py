"""Ferramentas da cafeteria, como funções puras.

As funções recebem os dados já carregados e devolvem a resposta no formato do
contrato ({"ok": ..., "dados": ...}). Não leem arquivos nem dependem do servidor,
por isso o servidor MCP e o stub do cliente podem reaproveitá-las.
"""

from copy import deepcopy


def resposta_ok(dados: dict) -> dict:
    """Monta a resposta de sucesso no formato do contrato."""
    return {"ok": True, "dados": dados}


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
