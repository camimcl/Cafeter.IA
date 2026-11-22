"""Leitura e gravação dos arquivos JSON de dados da cafeteria.

A gravação é atômica: o arquivo final fica inteiro com os dados novos ou continua
inteiro com os antigos, nunca pela metade (por exemplo, se o processo cair no meio).
"""

import json
import os
import tempfile
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
INDENTACAO_JSON = 2

ARQUIVO_CARDAPIO = "cardapio.json"
ARQUIVO_RECEITAS = "receitas.json"
ARQUIVO_ESTOQUE = "estoque.json"
ARQUIVO_PEDIDOS = "pedidos.json"


# --- funções genéricas ---


def ler_json(caminho: Path) -> dict:
    """Lê um arquivo JSON em UTF-8 e devolve o conteúdo."""
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def gravar_json(caminho: Path, dados: dict) -> None:
    """Grava o JSON de forma atômica, em UTF-8, com indentação de 2 espaços."""
    # Converte antes de tocar no disco: dado inválido falha sem criar nenhum arquivo.
    texto = json.dumps(dados, ensure_ascii=False, indent=INDENTACAO_JSON) + "\n"

    # O temporário fica na mesma pasta do destino, porque a troca só é atômica no mesmo disco.
    descritor, nome_temporario = tempfile.mkstemp(
        dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp"
    )
    temporario = Path(nome_temporario)
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(texto)
            arquivo.flush()
            os.fsync(arquivo.fileno())  # garante que os bytes saíram da memória para o disco
        os.replace(temporario, caminho)  # troca atômica: o destino nunca fica pela metade
    except BaseException:
        temporario.unlink(missing_ok=True)
        raise


# --- leitura de cada arquivo de dados ---


def ler_cardapio(pasta: Path = PASTA_DADOS) -> list[dict]:
    """Lê a lista de produtos de cardapio.json."""
    return ler_json(pasta / ARQUIVO_CARDAPIO)["produtos"]


def ler_receitas(pasta: Path = PASTA_DADOS) -> dict:
    """Lê as receitas de receitas.json, indexadas pelo id do produto."""
    return ler_json(pasta / ARQUIVO_RECEITAS)["receitas"]


def ler_estoque(pasta: Path = PASTA_DADOS) -> list[dict]:
    """Lê a lista de ingredientes de estoque.json."""
    return ler_json(pasta / ARQUIVO_ESTOQUE)["ingredientes"]


def ler_pedidos(pasta: Path = PASTA_DADOS) -> list[dict]:
    """Lê a lista de pedidos registrados em pedidos.json."""
    return ler_json(pasta / ARQUIVO_PEDIDOS)["pedidos"]


# --- gravação dos arquivos que o servidor altera ---


def gravar_estoque(ingredientes: list[dict], pasta: Path = PASTA_DADOS) -> None:
    """Grava a lista de ingredientes em estoque.json, de forma atômica."""
    gravar_json(pasta / ARQUIVO_ESTOQUE, {"ingredientes": ingredientes})


def gravar_pedidos(pedidos: list[dict], pasta: Path = PASTA_DADOS) -> None:
    """Grava a lista de pedidos em pedidos.json, de forma atômica."""
    gravar_json(pasta / ARQUIVO_PEDIDOS, {"pedidos": pedidos})
