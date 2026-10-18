"""Passo 1 da seção 5.4 (percepção dos estudantes): resumo por questão, grupo e edição.

Lê o CSV gerado por extrair_percepcao.py (não precisa de data/raw) e grava
data/processed/percepcao/percepcao_resumo_por_grupo.csv.

Escala do ENADE (QE_I27 a QE_I68): 1 (discordo totalmente) a 6 (concordo totalmente).
O código 7 é "não sei responder" e o 8 é "não se aplica"; os dois ficam fora da média
e das porcentagens de concordância/discordância e são reportados à parte.
"""

from __future__ import annotations

import sys

import pandas as pd

from extrair_percepcao import DIRETORIO_SAIDA_PADRAO, RESPOSTA_EM_BRANCO

ARQUIVO_CONTAGENS = DIRETORIO_SAIDA_PADRAO / "percepcao_contagens_por_curso.csv"
ARQUIVO_RESUMO = DIRETORIO_SAIDA_PADRAO / "percepcao_resumo_por_grupo.csv"

NOTAS_ESCALA = ["1", "2", "3", "4", "5", "6"]
NAO_SEI = "7"
NAO_SE_APLICA = "8"
ORDEM_RESPOSTAS = [*NOTAS_ESCALA, NAO_SEI, NAO_SE_APLICA, RESPOSTA_EM_BRANCO]

GRUPOS_CEARA_E_UNIFOR = ["Unifor", "CE privadas", "CE públicas"]
GRUPO_BRASIL = "Brasil"  # todos os cursos de Ciência da Computação, incluindo a Unifor


def carregar_contagens() -> pd.DataFrame:
    """Lê as contagens por curso, questão e resposta geradas por extrair_percepcao.py."""
    if not ARQUIVO_CONTAGENS.is_file():
        raise FileNotFoundError(
            f"Não achei {ARQUIVO_CONTAGENS}. Rode antes: python src/extrair_percepcao.py"
        )
    return pd.read_csv(
        ARQUIVO_CONTAGENS,
        usecols=["ano", "questao", "grupo", "resposta", "n"],
        dtype={"questao": "string", "grupo": "string", "resposta": "string"},
    )


def somar_por_grupo(contagens: pd.DataFrame) -> pd.DataFrame:
    """Soma as contagens dos cursos de cada grupo e cria o grupo Brasil (todos os cursos)."""
    ceara_e_unifor = contagens.loc[contagens["grupo"].isin(GRUPOS_CEARA_E_UNIFOR)]
    brasil = contagens.assign(grupo=GRUPO_BRASIL)
    base = pd.concat([ceara_e_unifor, brasil], ignore_index=True)
    return base.groupby(["ano", "grupo", "questao", "resposta"], as_index=False)["n"].sum()


def montar_resumo(somas: pd.DataFrame) -> pd.DataFrame:
    """Calcula, por ano, grupo e questão, as contagens e os indicadores de percepção."""
    tabela = somas.pivot_table(
        index=["ano", "grupo", "questao"], columns="resposta", values="n", aggfunc="sum", fill_value=0
    ).reindex(columns=ORDEM_RESPOSTAS, fill_value=0)

    notas = tabela[NOTAS_ESCALA]
    n_validos = notas.sum(axis=1)
    denominador = n_validos.where(n_validos > 0)  # evita divisão por zero
    n_respondeu = n_validos + tabela[NAO_SEI] + tabela[NAO_SE_APLICA]

    resumo = pd.DataFrame(
        {
            "n_inscritos": tabela.sum(axis=1),
            "n_validos": n_validos,
            "n_nao_sei": tabela[NAO_SEI],
            "n_nao_se_aplica": tabela[NAO_SE_APLICA],
            "n_em_branco": tabela[RESPOSTA_EM_BRANCO],
            "media": (notas * [int(nota) for nota in NOTAS_ESCALA]).sum(axis=1) / denominador,
            "pct_concordancia": notas[["4", "5", "6"]].sum(axis=1) / denominador * 100,
            "pct_discordancia": notas[["1", "2", "3"]].sum(axis=1) / denominador * 100,
            "pct_nao_sei_ou_nao_se_aplica": (tabela[NAO_SEI] + tabela[NAO_SE_APLICA])
            / n_respondeu.where(n_respondeu > 0)
            * 100,
        }
    ).reset_index()

    resumo["numero_questao"] = resumo["questao"].str.replace("QE_I", "", regex=False).astype(int)
    resumo = resumo.sort_values(["ano", "numero_questao", "grupo"]).reset_index(drop=True)
    colunas_decimais = ["media", "pct_concordancia", "pct_discordancia", "pct_nao_sei_ou_nao_se_aplica"]
    resumo[colunas_decimais] = resumo[colunas_decimais].round(2)
    return resumo


def imprimir_conferencia(resumo: pd.DataFrame) -> None:
    """Mostra no terminal um resumo curto para conferência rápida."""
    print(f"Linhas no resumo: {len(resumo)}")
    for (ano, grupo), parte in resumo.groupby(["ano", "grupo"]):
        print(
            f"  {ano} | {grupo:<12} | {len(parte)} questões | "
            f"respondentes válidos por questão: mínimo {int(parte['n_validos'].min())}, "
            f"máximo {int(parte['n_validos'].max())}"
        )


def principal() -> int:
    try:
        resumo = montar_resumo(somar_por_grupo(carregar_contagens()))
    except (FileNotFoundError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    resumo.to_csv(ARQUIVO_RESUMO, index=False)
    imprimir_conferencia(resumo)
    print(f"\nArquivo gerado: {ARQUIVO_RESUMO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
