"""Passo 2 da seção 5.4 (percepção dos estudantes): ranking das questões da Unifor.

Lê data/processed/percepcao/percepcao_resumo_por_grupo.csv (gerado por percepcao.py) e o
dicionário do INEP em data/processed/percepcao/documentacao/2021 (texto das questões).

Gera, em data/processed/percepcao/:
- percepcao_ranking_unifor.csv: as 42 questões ordenadas da melhor para a pior média, por edição;
- percepcao_ranking_unifor_<ano>.png: gráfico com as 5 melhores e as 5 piores questões.
"""

from __future__ import annotations

import re
import sys
import textwrap

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from extrair_percepcao import DIRETORIO_SAIDA_PADRAO
from percepcao import ARQUIVO_RESUMO

ARQUIVO_RANKING = DIRETORIO_SAIDA_PADRAO / "percepcao_ranking_unifor.csv"
DIRETORIO_DICIONARIO = DIRETORIO_SAIDA_PADRAO / "documentacao" / "2021"
ABA_VARIAVEIS = "DICIONÁRIO DE VARIÁVEIS"
PADRAO_QUESTAO = re.compile(r"QE_I\d+")

GRUPO_FOCO = "Unifor"
QUANTIDADE_DESTAQUE = 5
LIMITE_NAO_SEI = 25.0  # % de "não sei"/"não se aplica" a partir do qual a média merece cautela
COR_MELHORES = "#2e7d32"
COR_PIORES = "#c62828"

COLUNAS_RANKING = [
    "ano",
    "posicao",
    "questao",
    "texto",
    "media",
    "pct_concordancia",
    "pct_discordancia",
    "n_validos",
    "pct_nao_sei_ou_nao_se_aplica",
]


def carregar_resumo() -> pd.DataFrame:
    if not ARQUIVO_RESUMO.is_file():
        raise FileNotFoundError(f"Não achei {ARQUIVO_RESUMO}. Rode antes: python src/percepcao.py")
    return pd.read_csv(ARQUIVO_RESUMO)


def carregar_textos_questoes() -> dict[str, str]:
    """Lê o texto de cada questão no dicionário de variáveis do INEP (o texto é igual em 2017 e 2021)."""
    arquivos = [
        arquivo
        for arquivo in DIRETORIO_DICIONARIO.glob("*.xlsx")
        if "Dicion" in arquivo.name and not arquivo.name.startswith("~$")
    ]
    if not arquivos:
        raise FileNotFoundError(f"Não achei o dicionário .xlsx de 2021 em {DIRETORIO_DICIONARIO}.")
    tabela = pd.read_excel(arquivos[0], sheet_name=ABA_VARIAVEIS, header=None, dtype=str)
    textos: dict[str, str] = {}
    for codigo, texto in zip(tabela[0], tabela[3]):
        if isinstance(codigo, str) and isinstance(texto, str) and PADRAO_QUESTAO.fullmatch(codigo.strip()):
            textos.setdefault(codigo.strip(), texto.strip())  # a primeira ocorrência é a da pergunta
    return textos


def montar_ranking(resumo: pd.DataFrame, textos: dict[str, str]) -> pd.DataFrame:
    """Ordena as questões da Unifor da maior para a menor média, em cada edição."""
    unifor = resumo.loc[resumo["grupo"] == GRUPO_FOCO].copy()
    unifor["texto"] = unifor["questao"].map(textos).fillna("(texto não encontrado)")
    unifor = unifor.sort_values(["ano", "media", "numero_questao"], ascending=[True, False, True])
    unifor["posicao"] = unifor.groupby("ano").cumcount() + 1
    return unifor[COLUNAS_RANKING].reset_index(drop=True)


def imprimir_destaques(ranking: pd.DataFrame) -> None:
    for ano, parte in ranking.groupby("ano"):
        print(f"\n=== {GRUPO_FOCO} {ano}: {QUANTIDADE_DESTAQUE} melhores e {QUANTIDADE_DESTAQUE} piores ===")
        for rotulo, bloco in (("Melhores", parte.head(QUANTIDADE_DESTAQUE)), ("Piores", parte.tail(QUANTIDADE_DESTAQUE))):
            print(f"{rotulo}:")
            for linha in bloco.itertuples():
                print(f"  {linha.posicao:>2}. {linha.questao}  média {linha.media:.2f}  (n={linha.n_validos})")


def desenhar_grafico(parte: pd.DataFrame, ano: int):
    """Barras horizontais com as melhores (verde) e as piores (vermelho) questões da edição."""
    melhores = parte.head(QUANTIDADE_DESTAQUE)
    piores = parte.tail(QUANTIDADE_DESTAQUE)
    destaque = pd.concat([melhores, piores])
    cores = [COR_MELHORES] * len(melhores) + [COR_PIORES] * len(piores)
    rotulos = [f"{linha.questao}: " + textwrap.fill(linha.texto, width=62) for linha in destaque.itertuples()]
    posicoes = list(range(len(destaque)))[::-1]  # a melhor questão fica no topo

    figura, eixo = plt.subplots(figsize=(13, 8))
    eixo.barh(posicoes, destaque["media"], color=cores)
    eixo.set_yticks(posicoes)
    eixo.set_yticklabels(rotulos, fontsize=8)
    eixo.set_xlim(0, 6.9)
    eixo.set_xlabel("Média das respostas (1 = discordo totalmente, 6 = concordo totalmente)")
    eixo.set_title(f"Percepção dos concluintes de Ciência da Computação da Unifor, ENADE {ano}\n"
                   f"{QUANTIDADE_DESTAQUE} questões mais bem avaliadas e {QUANTIDADE_DESTAQUE} mais mal avaliadas")
    for posicao, linha in zip(posicoes, destaque.itertuples()):
        cautela = "*" if linha.pct_nao_sei_ou_nao_se_aplica >= LIMITE_NAO_SEI else ""
        eixo.text(linha.media + 0.05, posicao, f"{linha.media:.2f} (n={linha.n_validos}){cautela}", va="center", fontsize=8)
    figura.text(
        0.01,
        0.01,
        f"n = respondentes com nota de 1 a 6. * = {LIMITE_NAO_SEI:.0f}% ou mais responderam "
        '"não sei" ou "não se aplica"; a média vale só para quem avaliou.',
        fontsize=8,
    )
    figura.tight_layout(rect=(0, 0.03, 1, 1))
    return figura


def principal() -> int:
    if plt is None:
        print("Erro: matplotlib não está instalado. Rode: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    try:
        ranking = montar_ranking(carregar_resumo(), carregar_textos_questoes())
    except (FileNotFoundError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    ranking.to_csv(ARQUIVO_RANKING, index=False)
    imprimir_destaques(ranking)
    for ano, parte in ranking.groupby("ano"):
        caminho = DIRETORIO_SAIDA_PADRAO / f"percepcao_ranking_unifor_{ano}.png"
        figura = desenhar_grafico(parte, int(ano))
        figura.savefig(caminho, dpi=150)
        plt.close(figura)
        print(f"Gráfico gerado: {caminho}")
    print(f"\nArquivo gerado: {ARQUIVO_RANKING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
