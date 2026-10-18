from __future__ import annotations

import argparse
import sys
import zipfile
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats

from perfil import (
    ANO,
    CODIGO_GRUPO,
    CODIGO_UF_CEARA,
    DIRETORIO_DADOS_BRUTOS,
    DIRETORIO_DADOS_PROCESSADOS,
    ARQUIVO_POR_VARIAVEL,
    ler_tabela,
    mapear_grupos_curso,
)

NIVEL_SIGNIFICANCIA = 0.05
GRUPOS_COMPARACAO = ["CE privadas", "CE públicas", "CE demais"]

# Categorias agrupadas para que as frequências esperadas dos testes não fiquem pequenas demais.
FAIXAS_RENDA = {"A": "Até 3 SM", "B": "Até 3 SM", "C": "3 a 6 SM", "D": "3 a 6 SM", "E": "Acima de 6 SM", "F": "Acima de 6 SM", "G": "Acima de 6 SM"}
FAIXAS_TRABALHO = {"A": "Não trabalha", "B": "Menos de 40 h", "C": "Menos de 40 h", "D": "Menos de 40 h", "E": "40 h ou mais"}
# Ensino médio no exterior (C e F) fica fora do teste por ser raro.
FAIXAS_ESCOLA = {"A": "Pública", "D": "Pública", "B": "Privada", "E": "Privada"}
FAIXAS_ESCOLARIDADE = {"A": "Até fundamental", "B": "Até fundamental", "C": "Até fundamental", "D": "Ensino médio", "E": "Superior", "F": "Superior"}


def carregar_ceara(arquivo_zip: zipfile.ZipFile) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Lê as variáveis de perfil dos cursos de Ciência da Computação do Ceará."""
    identificacao = ler_tabela(arquivo_zip, 1)
    grupos_curso = mapear_grupos_curso(identificacao)
    cursos = identificacao.loc[
        (identificacao["CO_GRUPO"] == CODIGO_GRUPO) & (identificacao["CO_UF_CURSO"] == CODIGO_UF_CEARA)
    ].drop_duplicates("CO_CURSO").set_index("CO_CURSO")
    cursos["grupo"] = grupos_curso.reindex(cursos.index)

    variaveis = {}
    for variavel, numero_arquivo in ARQUIVO_POR_VARIAVEL.items():
        tabela = ler_tabela(arquivo_zip, numero_arquivo)
        tabela = tabela.loc[tabela["CO_CURSO"].isin(cursos.index), ["CO_CURSO", variavel]].copy()
        tabela["grupo"] = tabela["CO_CURSO"].map(cursos["grupo"])
        tabela["CO_IES"] = tabela["CO_CURSO"].map(cursos["CO_IES"])
        variaveis[variavel] = tabela.dropna(subset=[variavel])
    variaveis["NU_IDADE"]["NU_IDADE"] = pd.to_numeric(variaveis["NU_IDADE"]["NU_IDADE"], errors="coerce")
    variaveis["QE_I08"]["faixa"] = variaveis["QE_I08"]["QE_I08"].map(FAIXAS_RENDA)
    variaveis["QE_I10"]["faixa"] = variaveis["QE_I10"]["QE_I10"].map(FAIXAS_TRABALHO)
    variaveis["QE_I17"]["faixa"] = variaveis["QE_I17"]["QE_I17"].map(FAIXAS_ESCOLA)
    variaveis["QE_I17"] = variaveis["QE_I17"].dropna(subset=["faixa"])
    variaveis["QE_I04"]["faixa"] = variaveis["QE_I04"]["QE_I04"].map(FAIXAS_ESCOLARIDADE)
    variaveis["QE_I05"]["faixa"] = variaveis["QE_I05"]["QE_I05"].map(FAIXAS_ESCOLARIDADE)
    return variaveis, cursos


def selecionar(tabela: pd.DataFrame, grupo: str) -> pd.DataFrame:
    """Filtra o grupo pedido; 'CE demais' reúne todos os cursos do Ceará exceto a Unifor."""
    if grupo == "CE demais":
        return tabela.loc[tabela["grupo"] != "Unifor"]
    return tabela.loc[tabela["grupo"] == grupo]


def v_de_cramer(contingencia: np.ndarray, qui_quadrado: float) -> float:
    """Mede o tamanho do efeito de uma tabela de contingência (0 a 1)."""
    total = contingencia.sum()
    menor_dimensao = min(contingencia.shape) - 1
    return float(np.sqrt(qui_quadrado / (total * menor_dimensao)))


def testar_categorica(tabela: pd.DataFrame, coluna: str, grupo: str, variavel: str) -> dict:
    """Compara a distribuição de uma variável categórica entre a Unifor e um grupo."""
    unifor = tabela.loc[tabela["grupo"] == "Unifor", coluna]
    outro = selecionar(tabela, grupo)[coluna]
    categorias = sorted(set(unifor) | set(outro))
    contingencia = np.array([
        [int((unifor == categoria).sum()) for categoria in categorias],
        [int((outro == categoria).sum()) for categoria in categorias],
    ])
    qui_quadrado, valor_p, _, esperados = stats.chi2_contingency(contingencia, correction=False)
    teste = "Qui-quadrado"
    if contingencia.shape[1] == 2:
        _, valor_p = stats.fisher_exact(contingencia)
        teste = "Exato de Fisher"
    return {
        "variavel": variavel,
        "comparacao": f"Unifor x {grupo}",
        "teste": teste,
        "n_unifor": int(contingencia[0].sum()),
        "n_grupo": int(contingencia[1].sum()),
        "estatistica": qui_quadrado,
        "valor_p": valor_p,
        "efeito": v_de_cramer(contingencia, qui_quadrado),
        "medida_efeito": "V de Cramér",
        "menor_esperado": float(esperados.min()),
    }


def testar_idade(tabela: pd.DataFrame, grupo: str) -> dict:
    """Compara as idades da Unifor e de um grupo pelo teste de Mann-Whitney."""
    unifor = tabela.loc[tabela["grupo"] == "Unifor", "NU_IDADE"].dropna()
    outro = selecionar(tabela, grupo)["NU_IDADE"].dropna()
    estatistica, valor_p = stats.mannwhitneyu(unifor, outro, alternative="two-sided")
    # Correlação rank-biserial: positiva quando a Unifor tende a ter idades maiores.
    efeito = 2 * estatistica / (len(unifor) * len(outro)) - 1
    return {
        "variavel": "Idade",
        "comparacao": f"Unifor x {grupo}",
        "teste": "Mann-Whitney",
        "n_unifor": len(unifor),
        "n_grupo": len(outro),
        "estatistica": float(estatistica),
        "valor_p": float(valor_p),
        "efeito": float(efeito),
        "medida_efeito": "Rank-biserial",
        "menor_esperado": np.nan,
    }


def corrigir_holm(valores_p: pd.Series) -> pd.Series:
    """Ajusta os valores-p pelo método de Holm para controlar comparações múltiplas."""
    ordem = valores_p.sort_values().index
    quantidade = len(valores_p)
    ajustados = (valores_p.loc[ordem] * np.arange(quantidade, 0, -1)).cummax().clip(upper=1)
    return ajustados.reindex(valores_p.index)


def resumir_por_ies(variaveis: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula os principais indicadores de perfil para cada instituição do Ceará."""
    sexo = variaveis["TP_SEXO"].groupby("CO_IES")["TP_SEXO"]
    idade = variaveis["NU_IDADE"].groupby("CO_IES")["NU_IDADE"]
    renda = variaveis["QE_I08"].groupby("CO_IES")["faixa"]
    trabalho = variaveis["QE_I10"].groupby("CO_IES")["faixa"]
    escola = variaveis["QE_I17"].groupby("CO_IES")["faixa"]
    escolaridade_pai = variaveis["QE_I04"].groupby("CO_IES")["faixa"]
    escolaridade_mae = variaveis["QE_I05"].groupby("CO_IES")["faixa"]
    grupo =variaveis["TP_SEXO"].groupby("CO_IES")["grupo"].first().fillna("")
    resumo = pd.DataFrame(
        {
            "grupo": grupo,
            "concluintes": sexo.size(),
            "pct_feminino": sexo.apply(lambda valores: 100 * (valores == "F").mean()),
            "idade_media": idade.mean(),
            "idade_mediana": idade.median(),
            "respondentes_qe": renda.size(),
            "pct_renda_ate_3sm": renda.apply(lambda valores: 100 * (valores == "Até 3 SM").mean()),
            "pct_renda_acima_6sm": renda.apply(lambda valores: 100 * (valores == "Acima de 6 SM").mean()),
            "pct_trabalha": trabalho.apply(lambda valores: 100 * (valores != "Não trabalha").mean()),
            "pct_40h_ou_mais": trabalho.apply(lambda valores: 100 * (valores == "40 h ou mais").mean()),
            "pct_escola_publica": escola.apply(lambda valores: 100 * (valores == "Pública").mean()),
            "pct_pai_superior": escolaridade_pai.apply(lambda valores: 100 * (valores == "Superior").mean()),
            "pct_mae_superior": escolaridade_mae.apply(lambda valores: 100 * (valores == "Superior").mean()),
        }
    )
    return resumo.sort_values("concluintes", ascending=False)


def resumir_por_grupo(variaveis: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula os mesmos indicadores agregados para a Unifor e cada grupo de comparação."""
    linhas = []
    for grupo in ["Unifor", *GRUPOS_COMPARACAO]:
        sexo = selecionar(variaveis["TP_SEXO"], grupo)["TP_SEXO"]
        idade = selecionar(variaveis["NU_IDADE"], grupo)["NU_IDADE"]
        renda = selecionar(variaveis["QE_I08"], grupo)["faixa"]
        trabalho = selecionar(variaveis["QE_I10"], grupo)["faixa"]
        escola = selecionar(variaveis["QE_I17"], grupo)["faixa"]
        escolaridade_pai = selecionar(variaveis["QE_I04"], grupo)["faixa"]
        escolaridade_mae = selecionar(variaveis["QE_I05"], grupo)["faixa"]
        linhas.append(
            {
                "grupo": grupo,
                "concluintes": len(sexo),
                "pct_feminino": 100 * (sexo == "F").mean(),
                "idade_media": idade.mean(),
                "idade_mediana": idade.median(),
                "respondentes_qe": len(renda),
                "pct_renda_ate_3sm": 100 * (renda == "Até 3 SM").mean(),
                "pct_renda_3_a_6sm": 100 * (renda == "3 a 6 SM").mean(),
                "pct_renda_acima_6sm": 100 * (renda == "Acima de 6 SM").mean(),
                "pct_nao_trabalha": 100 * (trabalho == "Não trabalha").mean(),
                "pct_menos_40h": 100 * (trabalho == "Menos de 40 h").mean(),
                "pct_40h_ou_mais": 100 * (trabalho == "40 h ou mais").mean(),
                "pct_escola_publica": 100 * (escola == "Pública").mean(),
                "pct_escola_privada": 100 * (escola == "Privada").mean(),
                "pct_pai_ate_fundamental": 100 * (escolaridade_pai == "Até fundamental").mean(),
                "pct_pai_medio": 100 * (escolaridade_pai == "Ensino médio").mean(),
                "pct_pai_superior": 100 * (escolaridade_pai == "Superior").mean(),
                "pct_mae_ate_fundamental": 100 * (escolaridade_mae == "Até fundamental").mean(),
                "pct_mae_medio": 100 * (escolaridade_mae == "Ensino médio").mean(),
                "pct_mae_superior": 100 * (escolaridade_mae == "Superior").mean(),
            }
        )
    return pd.DataFrame(linhas)


def executar_analise() -> None:
    """Testa se o perfil dos concluintes da Unifor difere dos demais cursos do Ceará."""
    caminho_zip = DIRETORIO_DADOS_BRUTOS / f"microdados_enade_{ANO}.zip"
    if not caminho_zip.exists():
        raise FileNotFoundError(f"ZIP do ENADE {ANO} não encontrado em {caminho_zip}.")
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        variaveis, _ = carregar_ceara(arquivo_zip)

    testes = []
    for grupo in GRUPOS_COMPARACAO:
        testes.append(testar_categorica(variaveis["TP_SEXO"], "TP_SEXO", grupo, "Sexo"))
        testes.append(testar_idade(variaveis["NU_IDADE"], grupo))
        testes.append(testar_categorica(variaveis["QE_I08"], "faixa", grupo, "Renda familiar"))
        testes.append(testar_categorica(variaveis["QE_I10"], "faixa", grupo, "Situação de trabalho"))
        testes.append(testar_categorica(variaveis["QE_I17"], "faixa", grupo, "Escola no ensino médio"))
        testes.append(testar_categorica(variaveis["QE_I04"], "faixa", grupo, "Escolaridade do pai"))
        testes.append(testar_categorica(variaveis["QE_I05"], "faixa", grupo, "Escolaridade da mãe"))
    testes = pd.DataFrame(testes).sort_values(["variavel", "comparacao"], ignore_index=True)
    testes["significativo"] = testes["valor_p"] < NIVEL_SIGNIFICANCIA
    testes["valor_p_holm"] = corrigir_holm(testes["valor_p"])
    testes["significativo_holm"] = testes["valor_p_holm"] < NIVEL_SIGNIFICANCIA

    resumo_grupos = resumir_por_grupo(variaveis)
    resumo_ies = resumir_por_ies(variaveis)

    DIRETORIO_DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    testes.to_csv(DIRETORIO_DADOS_PROCESSADOS / "comparacao_ceara_testes.csv", index=False)
    resumo_grupos.to_csv(DIRETORIO_DADOS_PROCESSADOS / "comparacao_ceara_grupos.csv", index=False)
    resumo_ies.to_csv(DIRETORIO_DADOS_PROCESSADOS / "comparacao_ceara_por_ies.csv")

    print(f"ENADE {ANO} – Perfil da Unifor comparado aos demais cursos de Ciência da Computação do Ceará")
    print("\nIndicadores por grupo")
    print(resumo_grupos.round(1).to_string(index=False))
    print("\nIndicadores por instituição do Ceará (CO_IES)")
    print(resumo_ies.round(1).to_string())
    print(f"\nTestes de diferença (nível de significância {NIVEL_SIGNIFICANCIA})")
    print(
        testes.to_string(
            index=False,
            formatters={
                "estatistica": "{:.2f}".format,
                "valor_p": "{:.4f}".format,
                "valor_p_holm": "{:.4f}".format,
                "efeito": "{:.3f}".format,
                "menor_esperado": "{:.1f}".format,
            },
        )
    )
    print(
        "\nRenda, trabalho e escolaridade dos pais foram agrupados em três faixas e a escola em "
        "pública/privada para os testes. "
        "'CE demais' reúne todos os cursos do Ceará exceto a Unifor."
    )


def principal(argumentos: Iterable[str] | None = None) -> int:
    """Interpreta argumentos da linha de comando e inicia a análise."""
    analisador = argparse.ArgumentParser(description="Compara o perfil dos concluintes da Unifor com os demais cursos de Ciência da Computação do Ceará.")
    analisador.parse_args(argumentos)
    try:
        executar_analise()
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
