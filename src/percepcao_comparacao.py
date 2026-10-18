"""Passo 3 da seção 5.4 (percepção dos estudantes): a Unifor difere dos outros cursos?

Para cada questão (QE_I27 a QE_I68) e edição, compara as notas de 1 a 6 dos concluintes da Unifor
com as de quatro grupos, usando o teste de Mann-Whitney (bilateral):

- CE privadas: demais cursos privados de Ciência da Computação do Ceará;
- CE públicas: cursos públicos de Ciência da Computação do Ceará;
- CE demais: todos os cursos do Ceará, exceto a Unifor (privadas + públicas);
- Brasil (exceto Unifor): todos os cursos do país, exceto a Unifor.

Os valores-p são ajustados pelo método de Holm, separadamente para cada edição e comparação
(42 testes cada). As respostas 7 ("não sei") e 8 ("não se aplica") ficam fora dos testes.

Lê data/processed/percepcao/percepcao_contagens_por_curso.csv (extrair_percepcao.py) e o dicionário
do INEP (texto das questões). Gera, em data/processed/percepcao/:
- percepcao_comparacao_unifor.csv: uma linha por edição, comparação e questão;
- percepcao_comparacao_ce_demais_<ano>.png: diferença de média entre a Unifor e o restante do Ceará.
"""

from __future__ import annotations

import sys
import textwrap

import numpy as np
import pandas as pd
from scipy import stats

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
except ImportError:
    plt = None

from comparacao_perfil import NIVEL_SIGNIFICANCIA, corrigir_holm
from extrair_percepcao import DIRETORIO_SAIDA_PADRAO
from percepcao import NOTAS_ESCALA, carregar_contagens
from percepcao_ranking import carregar_textos_questoes

ARQUIVO_COMPARACAO = DIRETORIO_SAIDA_PADRAO / "percepcao_comparacao_unifor.csv"

# Grupos de contagem do CSV de extração: Unifor, CE privadas, CE públicas e Outros estados.
COMPARACOES = {
    "CE privadas": ["CE privadas"],
    "CE públicas": ["CE públicas"],
    "CE demais": ["CE privadas", "CE públicas"],
    "Brasil (exceto Unifor)": ["CE privadas", "CE públicas", "Outros estados"],
}
COMPARACAO_GRAFICO = "CE demais"
VALORES_NOTAS = np.arange(1, 7)

COR_MENOR = "#c62828"
COR_MAIOR = "#2e7d32"
COR_SEM_DIFERENCA = "#9e9e9e"


def montar_distribuicoes(contagens: pd.DataFrame) -> pd.DataFrame:
    """Conta, por edição, grupo e questão, quantos estudantes deram cada nota de 1 a 6."""
    validas = contagens.loc[contagens["resposta"].isin(NOTAS_ESCALA)]
    tabela = validas.pivot_table(
        index=["ano", "grupo", "questao"], columns="resposta", values="n", aggfunc="sum", fill_value=0
    )
    return tabela.reindex(columns=NOTAS_ESCALA, fill_value=0)


def somar_grupos(tabela: pd.DataFrame, grupos: list[str]) -> pd.DataFrame:
    """Soma as distribuições dos grupos indicados, por edição e questão."""
    selecao = tabela.loc[tabela.index.get_level_values("grupo").isin(grupos)]
    return selecao.groupby(level=["ano", "questao"]).sum()


def media_e_concordancia(contagem: np.ndarray) -> tuple[float, float]:
    """Média das notas e % de concordância (notas 4 a 6) a partir das contagens das notas 1 a 6."""
    total = contagem.sum()
    return float((contagem * VALORES_NOTAS).sum() / total), float(contagem[3:].sum() / total * 100)


def comparar_questao(contagem_unifor: np.ndarray, contagem_outro: np.ndarray) -> dict:
    """Mann-Whitney entre a Unifor e um grupo, com as contagens das notas expandidas em respostas."""
    notas_unifor = np.repeat(VALORES_NOTAS, contagem_unifor)
    notas_outro = np.repeat(VALORES_NOTAS, contagem_outro)
    media_unifor, concordancia_unifor = media_e_concordancia(contagem_unifor)
    media_outro, concordancia_outro = media_e_concordancia(contagem_outro)
    resultado = stats.mannwhitneyu(notas_unifor, notas_outro, alternative="two-sided", method="asymptotic")
    # Correlação rank-biserial: positiva quando a Unifor tende a dar notas mais altas.
    efeito = 2 * resultado.statistic / (len(notas_unifor) * len(notas_outro)) - 1
    return {
        "n_unifor": len(notas_unifor),
        "n_comparacao": len(notas_outro),
        "media_unifor": media_unifor,
        "media_comparacao": media_outro,
        "diferenca_media": media_unifor - media_outro,
        "pct_concordancia_unifor": concordancia_unifor,
        "pct_concordancia_comparacao": concordancia_outro,
        "diferenca_pct_concordancia": concordancia_unifor - concordancia_outro,
        "estatistica_u": float(resultado.statistic),
        "valor_p": float(resultado.pvalue),
        "efeito_rank_biserial": float(efeito),
    }


def montar_comparacao(contagens: pd.DataFrame, textos: dict[str, str]) -> pd.DataFrame:
    tabela = montar_distribuicoes(contagens)
    unifor = somar_grupos(tabela, ["Unifor"])
    linhas = []
    for nome, grupos in COMPARACOES.items():
        outro = somar_grupos(tabela, grupos)
        for (ano, questao), contagem_unifor in unifor.iterrows():
            if (ano, questao) not in outro.index:
                continue
            contagem_outro = outro.loc[(ano, questao)].to_numpy()
            if contagem_unifor.sum() == 0 or contagem_outro.sum() == 0:
                continue
            linhas.append(
                {
                    "ano": ano,
                    "comparacao": f"Unifor x {nome}",
                    "questao": questao,
                    "numero_questao": int(questao.replace("QE_I", "")),
                    "texto": textos.get(questao, "(texto não encontrado)"),
                    **comparar_questao(contagem_unifor.to_numpy(), contagem_outro),
                }
            )
    resultado = pd.DataFrame(linhas)
    # Holm separado por edição e comparação (42 testes em cada).
    resultado["valor_p_holm"] = resultado.groupby(["ano", "comparacao"])["valor_p"].transform(corrigir_holm)
    significativo = resultado["valor_p_holm"] < NIVEL_SIGNIFICANCIA
    resultado["resultado"] = np.select(
        [significativo & (resultado["efeito_rank_biserial"] < 0), significativo & (resultado["efeito_rank_biserial"] > 0)],
        ["Unifor menor", "Unifor maior"],
        default="Sem diferença significativa",
    )
    resultado = resultado.sort_values(["ano", "comparacao", "numero_questao"]).reset_index(drop=True)
    arredondar = {
        "media_unifor": 2,
        "media_comparacao": 2,
        "diferenca_media": 2,
        "pct_concordancia_unifor": 2,
        "pct_concordancia_comparacao": 2,
        "diferenca_pct_concordancia": 2,
        "efeito_rank_biserial": 3,
        "valor_p": 6,
        "valor_p_holm": 6,
    }
    return resultado.round(arredondar)


def imprimir_conferencia(resultado: pd.DataFrame) -> None:
    print("\nQuestões em que a Unifor difere (Mann-Whitney, Holm a 5%), de 42 por comparação:")
    resumo = resultado.groupby(["ano", "comparacao", "resultado"]).size().unstack(fill_value=0)
    for coluna in ("Unifor menor", "Unifor maior", "Sem diferença significativa"):
        if coluna not in resumo.columns:
            resumo[coluna] = 0
    print(resumo[["Unifor menor", "Unifor maior", "Sem diferença significativa"]].to_string())

    print(f"\nMaiores diferenças de média contra '{COMPARACAO_GRAFICO}':")
    for ano, parte in resultado.loc[resultado["comparacao"] == f"Unifor x {COMPARACAO_GRAFICO}"].groupby("ano"):
        ordenada = parte.sort_values("diferenca_media")
        print(f"  {ano}, Unifor abaixo:")
        for linha in ordenada.head(3).itertuples():
            print(f"    {linha.questao}  {linha.diferenca_media:+.2f}  p Holm = {linha.valor_p_holm:.4f}")
        print(f"  {ano}, Unifor acima:")
        for linha in ordenada.tail(3).iloc[::-1].itertuples():
            print(f"    {linha.questao}  {linha.diferenca_media:+.2f}  p Holm = {linha.valor_p_holm:.4f}")


def desenhar_grafico(parte: pd.DataFrame, ano: int):
    """Barras com a diferença de média (Unifor menos CE demais) das 42 questões, ordenadas."""
    parte = parte.sort_values("diferenca_media", ascending=False).reset_index(drop=True)
    cores = parte["resultado"].map(
        {"Unifor menor": COR_MENOR, "Unifor maior": COR_MAIOR, "Sem diferença significativa": COR_SEM_DIFERENCA}
    )
    rotulos = [f"{linha.questao}: " + textwrap.shorten(linha.texto, width=70, placeholder="…") for linha in parte.itertuples()]
    posicoes = list(range(len(parte)))[::-1]

    figura, eixo = plt.subplots(figsize=(13, 13))
    eixo.barh(posicoes, parte["diferenca_media"], color=cores)
    eixo.set_yticks(posicoes)
    eixo.set_yticklabels(rotulos, fontsize=7)
    eixo.axvline(0, color="black", linewidth=0.8)
    eixo.set_xlabel("Média da Unifor menos média dos demais cursos do Ceará (escala de 1 a 6)")
    eixo.set_title(f"Percepção dos concluintes: Unifor x demais cursos de Ciência da Computação do Ceará, ENADE {ano}")
    eixo.legend(
        handles=[
            Patch(color=COR_MENOR, label="Unifor menor (significativo)"),
            Patch(color=COR_MAIOR, label="Unifor maior (significativo)"),
            Patch(color=COR_SEM_DIFERENCA, label="Sem diferença significativa"),
        ],
        loc="lower right",
        fontsize=8,
    )
    figura.text(
        0.01,
        0.01,
        f"Mann-Whitney com correção de Holm (42 testes), nível de {NIVEL_SIGNIFICANCIA:.0%}. "
        "Respostas 'não sei' e 'não se aplica' ficam fora.",
        fontsize=8,
    )
    figura.tight_layout(rect=(0, 0.02, 1, 1))
    return figura


def principal() -> int:
    try:
        resultado = montar_comparacao(carregar_contagens(), carregar_textos_questoes())
    except (FileNotFoundError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    resultado.to_csv(ARQUIVO_COMPARACAO, index=False)
    print(f"Linhas na comparação: {len(resultado)}")
    imprimir_conferencia(resultado)

    if plt is None:
        print("\nmatplotlib não está instalado; os gráficos não foram gerados.", file=sys.stderr)
    else:
        grafico = resultado.loc[resultado["comparacao"] == f"Unifor x {COMPARACAO_GRAFICO}"]
        for ano, parte in grafico.groupby("ano"):
            caminho = DIRETORIO_SAIDA_PADRAO / f"percepcao_comparacao_ce_demais_{ano}.png"
            figura = desenhar_grafico(parte, int(ano))
            figura.savefig(caminho, dpi=150)
            plt.close(figura)
            print(f"Gráfico gerado: {caminho}")
    print(f"\nArquivo gerado: {ARQUIVO_COMPARACAO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
