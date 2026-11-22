"""Testes do repositório de dados (leitura e gravação atômica dos JSON)."""

from pathlib import Path

import pytest

from mcp_server import repositorio
from mcp_server.repositorio import (
    PASTA_DADOS,
    gravar_estoque,
    gravar_json,
    gravar_pedidos,
    ler_cardapio,
    ler_estoque,
    ler_json,
    ler_pedidos,
    ler_receitas,
)

DADOS_EXEMPLO = {"ingredientes": [{"id": "cafe_graos", "nome": "Café em grãos", "quantidade": 10}]}


def arquivos_na_pasta(pasta: Path) -> list[str]:
    """Lista os nomes dos arquivos da pasta, incluindo os ocultos (temporários começam com '.')."""
    return sorted(p.name for p in pasta.iterdir())


# --- leitura e gravação ---


def test_gravar_e_ler_devolve_os_mesmos_dados(tmp_path: Path) -> None:
    caminho = tmp_path / "estoque.json"
    gravar_json(caminho, DADOS_EXEMPLO)
    assert ler_json(caminho) == DADOS_EXEMPLO


def test_gravar_usa_utf8_indentacao_2_e_quebra_de_linha_final(tmp_path: Path) -> None:
    caminho = tmp_path / "estoque.json"
    gravar_json(caminho, {"nome": "Café"})
    assert caminho.read_bytes() == '{\n  "nome": "Café"\n}\n'.encode("utf-8")


def test_gravar_substitui_o_conteudo_anterior(tmp_path: Path) -> None:
    caminho = tmp_path / "estoque.json"
    gravar_json(caminho, {"versao": 1})
    gravar_json(caminho, {"versao": 2})
    assert ler_json(caminho) == {"versao": 2}


def test_gravar_nao_deixa_arquivo_temporario(tmp_path: Path) -> None:
    gravar_json(tmp_path / "estoque.json", DADOS_EXEMPLO)
    assert arquivos_na_pasta(tmp_path) == ["estoque.json"]


@pytest.mark.parametrize("nome", ["cardapio", "estoque", "receitas", "pedidos"])
def test_regravar_os_dados_semente_nao_muda_nenhum_byte(tmp_path: Path, nome: str) -> None:
    # Garante que o servidor pode regravar os arquivos sem gerar diferenças no Git.
    original = PASTA_DADOS / f"{nome}.json"
    copia = tmp_path / f"{nome}.json"
    gravar_json(copia, ler_json(original))
    assert copia.read_bytes() == original.read_bytes()


# --- atomicidade: falhas no meio da gravação ---


def gravar_original(tmp_path: Path) -> Path:
    """Cria um estoque.json com conteúdo conhecido e devolve o caminho."""
    caminho = tmp_path / "estoque.json"
    gravar_json(caminho, {"versao": "original"})
    return caminho


def troca_com_falha(origem: object, destino: object) -> None:
    """Substitui os.replace nos testes, simulando uma falha na troca dos arquivos."""
    raise OSError("disco cheio")


def test_falha_na_troca_mantem_o_original_e_apaga_o_temporario(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caminho = gravar_original(tmp_path)
    monkeypatch.setattr(repositorio.os, "replace", troca_com_falha)
    with pytest.raises(OSError):
        gravar_json(caminho, {"versao": "nova"})

    assert ler_json(caminho) == {"versao": "original"}
    assert arquivos_na_pasta(tmp_path) == ["estoque.json"]


def test_falha_ao_escrever_no_disco_mantem_o_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caminho = gravar_original(tmp_path)

    def fsync_com_falha(descritor: int) -> None:
        raise OSError("falha de escrita")

    monkeypatch.setattr(repositorio.os, "fsync", fsync_com_falha)
    with pytest.raises(OSError):
        gravar_json(caminho, {"versao": "nova"})

    assert ler_json(caminho) == {"versao": "original"}
    assert arquivos_na_pasta(tmp_path) == ["estoque.json"]


def test_dado_que_nao_vira_json_nao_cria_nem_altera_arquivo(tmp_path: Path) -> None:
    caminho = gravar_original(tmp_path)
    with pytest.raises(TypeError):
        gravar_json(caminho, {"versao": {"conjunto", "nao", "vira", "json"}})

    assert ler_json(caminho) == {"versao": "original"}
    assert arquivos_na_pasta(tmp_path) == ["estoque.json"]


def test_falha_quando_o_destino_ainda_nao_existe_nao_deixa_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(repositorio.os, "replace", troca_com_falha)
    with pytest.raises(OSError):
        gravar_json(tmp_path / "novo.json", {"a": 1})
    assert arquivos_na_pasta(tmp_path) == []


# --- leitura dos arquivos semente ---


def test_ler_os_arquivos_semente() -> None:
    assert len(ler_cardapio()) == 10
    assert "cappuccino" in ler_receitas()
    assert {"id": "leite_aveia", "quantidade": 400}.items() <= next(
        i for i in ler_estoque() if i["id"] == "leite_aveia"
    ).items()
    assert ler_pedidos() == []


def test_gravar_estoque_e_pedidos_usam_o_formato_dos_arquivos(tmp_path: Path) -> None:
    ingredientes = [{"id": "gelo", "nome": "Gelo", "unidade": "g", "quantidade": 5}]
    pedidos = [{"pedido_id": "P-0001", "itens": []}]
    gravar_estoque(ingredientes, tmp_path)
    gravar_pedidos(pedidos, tmp_path)

    assert ler_json(tmp_path / "estoque.json") == {"ingredientes": ingredientes}
    assert ler_estoque(tmp_path) == ingredientes
    assert ler_pedidos(tmp_path) == pedidos
