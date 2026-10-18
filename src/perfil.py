from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DIRETORIO_RAIZ = Path(__file__).resolve().parents[1]
DIRETORIO_DADOS_BRUTOS = DIRETORIO_RAIZ / "data" / "raw"
DIRETORIO_DADOS_PROCESSADOS = DIRETORIO_RAIZ / "data" / "processed" / "perfil_2021"

# Edição mais recente com Ciência da Computação e microdados publicados pelo INEP.
ANO = 2021
CODIGO_GRUPO = "4004"  # Ciência da Computação (Bacharelado)
CODIGO_IES_UNIFOR = "29"
CODIGO_CURSO_UNIFOR = "2209"
CODIGO_UF_CEARA = "23"
# O microdado de 2021 registra a Unifor com CO_CATEGAD=2 (Pública Estadual), mas ela é
# privada sem fins lucrativos; por isso a categoria da Unifor é corrigida abaixo.
CATEGORIAS_PUBLICAS = {"1", "2", "3"}

# Número do arquivo de microdados que contém cada variável (dicionário 2021).
ARQUIVO_POR_VARIAVEL = {
    "TP_SEXO": 5,
    "NU_IDADE": 6,
    "QE_I04": 10,
    "QE_I05": 11,
    "QE_I08": 14,
    "QE_I10": 16,
    "QE_I17": 23,
}

ROTULOS_SEXO = {"M": "Masculino", "F": "Feminino"}
ROTULOS_RENDA = {
    "A": "Até 1,5 SM",
    "B": "1,5 a 3 SM",
    "C": "3 a 4,5 SM",
    "D": "4,5 a 6 SM",
    "E": "6 a 10 SM",
    "F": "10 a 30 SM",
    "G": "Acima de 30 SM",
}
ROTULOS_TRABALHO = {
    "A": "Não trabalha",
    "B": "Trabalha eventualmente",
    "C": "Até 20 h semanais",
    "D": "21 a 39 h semanais",
    "E": "40 h semanais ou mais",
}
ROTULOS_ESCOLARIDADE = {
    "A": "Nenhuma",
    "B": "Fundamental: 1º ao 5º ano",
    "C": "Fundamental: 6º ao 9º ano",
    "D": "Ensino médio",
    "E": "Graduação",
    "F": "Pós-graduação",
}
ROTULOS_ESCOLA = {
    "A": "Todo em pública",
    "D": "Maior parte em pública",
    "E": "Maior parte em privada",
    "B": "Todo em privada",
    "C": "Todo no exterior",
    "F": "Parte no Brasil e parte no exterior",
}
FAIXAS_IDADE = [0, 22, 24, 29, 39, 200]
ROTULOS_FAIXAS_IDADE = ["Até 22", "23 a 24", "25 a 29", "30 a 39", "40 ou mais"]
GRUPOS = ["Unifor", "CE privadas", "CE públicas", "Brasil"]


def localizar_membro(arquivo_zip: zipfile.ZipFile, numero_arquivo: int) -> str:
    """Encontra dentro do ZIP o arquivo de microdados indicado pelo número."""
    padrao = re.compile(rf"(?:^|/)microdados{ANO}_arq{numero_arquivo}\.txt$", re.IGNORECASE)
    correspondencias = [nome for nome in arquivo_zip.namelist() if padrao.search(nome)]
    if len(correspondencias) != 1:
        raise FileNotFoundError(
            f"Esperava um arquivo microdados{ANO}_arq{numero_arquivo}.txt em "
            f"{arquivo_zip.filename}; encontrados: {correspondencias}"
        )
    return correspondencias[0]


def ler_tabela(arquivo_zip: zipfile.ZipFile, numero_arquivo: int) -> pd.DataFrame:
    """Lê uma tabela CSV contida no ZIP de microdados, com colunas e códigos limpos."""
    with arquivo_zip.open(localizar_membro(arquivo_zip, numero_arquivo)) as objeto_arquivo:
        tabela = pd.read_csv(objeto_arquivo, sep=";", dtype="string", encoding="latin-1", low_memory=False)
    tabela.columns = tabela.columns.str.strip().str.replace('"', "", regex=False)
    for coluna in tabela.columns:
        tabela[coluna] = tabela[coluna].str.strip().str.replace('"', "", regex=False)
    return tabela


def mapear_grupos_curso(identificacao: pd.DataFrame) -> pd.Series:
    """Associa cada curso de Ciência da Computação ao seu grupo de comparação."""
    cursos = identificacao.loc[identificacao["CO_GRUPO"] == CODIGO_GRUPO].drop_duplicates("CO_CURSO").set_index("CO_CURSO")
    eh_unifor = (cursos["CO_IES"] == CODIGO_IES_UNIFOR) & (cursos.index == CODIGO_CURSO_UNIFOR)
    eh_ceara = (cursos["CO_UF_CURSO"] == CODIGO_UF_CEARA) & ~eh_unifor
    eh_publica = cursos["CO_CATEGAD"].isin(CATEGORIAS_PUBLICAS)
    grupos = pd.Series(pd.NA, index=cursos.index, dtype="string")
    grupos[eh_unifor] = "Unifor"
    grupos[eh_ceara & eh_publica] = "CE públicas"
    grupos[eh_ceara & ~eh_publica] = "CE privadas"
    if not eh_unifor.any():
        raise ValueError(f"Curso {CODIGO_CURSO_UNIFOR} da Unifor não encontrado no grupo {CODIGO_GRUPO}.")
    return grupos


def carregar_variavel(arquivo_zip: zipfile.ZipFile, variavel: str, grupos_curso: pd.Series) -> pd.DataFrame:
    """Lê uma variável de perfil, mantendo só os cursos de Ciência da Computação."""
    tabela = ler_tabela(arquivo_zip, ARQUIVO_POR_VARIAVEL[variavel])
    tabela = tabela.loc[tabela["CO_CURSO"].isin(grupos_curso.index), ["CO_CURSO", variavel]].copy()
    tabela["grupo"] = tabela["CO_CURSO"].map(grupos_curso)
    return tabela


def distribuir(tabela: pd.DataFrame, coluna: str, rotulos: dict[str, str] | list[str]) -> pd.DataFrame:
    """Calcula a distribuição percentual de uma variável categórica em cada grupo."""
    ordem = list(rotulos.values()) if isinstance(rotulos, dict) else rotulos
    categorias = tabela[coluna].map(rotulos) if isinstance(rotulos, dict) else tabela[coluna]
    linhas = {}
    for grupo in GRUPOS:
        selecao = categorias[tabela["grupo"] == grupo] if grupo != "Brasil" else categorias
        contagem = selecao.dropna().value_counts().reindex(ordem, fill_value=0)
        linhas[(grupo, "n")] = contagem
        linhas[(grupo, "%")] = 100 * contagem / contagem.sum()
    return pd.DataFrame(linhas)


def resumir_idade(idades: pd.DataFrame) -> pd.DataFrame:
    """Calcula estatísticas descritivas da idade em cada grupo."""
    linhas = []
    for grupo in GRUPOS:
        valores = idades.loc[idades["grupo"] == grupo, "NU_IDADE"] if grupo != "Brasil" else idades["NU_IDADE"]
        valores = valores.dropna()
        linhas.append(
            {
                "grupo": grupo,
                "n": len(valores),
                "media": valores.mean(),
                "mediana": valores.median(),
                "desvio_padrao": valores.std(),
                "minimo": valores.min(),
                "q1": valores.quantile(0.25),
                "q3": valores.quantile(0.75),
                "maximo": valores.max(),
            }
        )
    return pd.DataFrame(linhas)


def gerar_grafico(distribuicao: pd.DataFrame, titulo: str, nome_arquivo: str) -> None:
    """Gera gráfico de barras agrupadas com os percentuais de cada grupo."""
    if plt is None:
        return
    percentuais = distribuicao.xs("%", axis=1, level=1)
    figura, eixo = plt.subplots(figsize=(10, 5))
    percentuais.plot.bar(ax=eixo, color=["#197a78", "#d9822b", "#7b6bb0", "#9a9a9a"], width=0.8)
    eixo.set(title=titulo, xlabel="", ylabel="% dos respondentes")
    eixo.tick_params(axis="x", rotation=25)
    eixo.legend(title="")
    figura.tight_layout()
    figura.savefig(DIRETORIO_DADOS_PROCESSADOS / nome_arquivo, dpi=160)
    plt.close(figura)


def imprimir_distribuicao(titulo: str, distribuicao: pd.DataFrame) -> None:
    """Exibe no terminal os percentuais e o total de respondentes de cada grupo."""
    percentuais = distribuicao.xs("%", axis=1, level=1).round(1)
    totais = distribuicao.xs("n", axis=1, level=1).sum()
    print(f"\n{titulo}")
    print(percentuais.to_string())
    print("Respondentes: " + ", ".join(f"{grupo}={int(total)}" for grupo, total in totais.items()))


def executar_analise() -> None:
    """Calcula o perfil dos concluintes por sexo, idade, renda, trabalho, escola e escolaridade dos pais."""
    caminho_zip = DIRETORIO_DADOS_BRUTOS / f"microdados_enade_{ANO}.zip"
    if not caminho_zip.exists():
        raise FileNotFoundError(f"ZIP do ENADE {ANO} não encontrado em {caminho_zip}.")

    DIRETORIO_DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        grupos_curso = mapear_grupos_curso(ler_tabela(arquivo_zip, 1))
        sexo = carregar_variavel(arquivo_zip, "TP_SEXO", grupos_curso)
        idade = carregar_variavel(arquivo_zip, "NU_IDADE", grupos_curso)
        renda = carregar_variavel(arquivo_zip, "QE_I08", grupos_curso)
        trabalho = carregar_variavel(arquivo_zip, "QE_I10", grupos_curso)
        escola = carregar_variavel(arquivo_zip, "QE_I17", grupos_curso)
        escolaridade_pai = carregar_variavel(arquivo_zip, "QE_I04", grupos_curso)
        escolaridade_mae = carregar_variavel(arquivo_zip, "QE_I05", grupos_curso)

    idade["NU_IDADE"] = pd.to_numeric(idade["NU_IDADE"], errors="coerce")
    idade["faixa"] = pd.cut(idade["NU_IDADE"], FAIXAS_IDADE, labels=ROTULOS_FAIXAS_IDADE).astype("string")

    distribuicoes = {
        "sexo": ("Sexo", distribuir(sexo, "TP_SEXO", ROTULOS_SEXO)),
        "faixa_etaria": ("Faixa etária", distribuir(idade, "faixa", ROTULOS_FAIXAS_IDADE)),
        "renda_familiar": ("Renda familiar (QE_I08)", distribuir(renda, "QE_I08", ROTULOS_RENDA)),
        "situacao_trabalho": ("Situação de trabalho (QE_I10)", distribuir(trabalho, "QE_I10", ROTULOS_TRABALHO)),
        "tipo_escola_medio": ("Tipo de escola no ensino médio (QE_I17)", distribuir(escola, "QE_I17", ROTULOS_ESCOLA)),
        "escolaridade_pai": ("Escolaridade do pai (QE_I04)", distribuir(escolaridade_pai, "QE_I04", ROTULOS_ESCOLARIDADE)),
        "escolaridade_mae": ("Escolaridade da mãe (QE_I05)", distribuir(escolaridade_mae, "QE_I05", ROTULOS_ESCOLARIDADE)),
    }
    resumo_idade = resumir_idade(idade)
    resumo_idade.to_csv(DIRETORIO_DADOS_PROCESSADOS / "idade_resumo.csv", index=False)
    print(f"ENADE {ANO} – Ciência da Computação: perfil dos concluintes")
    print("\nIdade (anos)")
    print(resumo_idade.round(1).to_string(index=False))

    for nome, (titulo, distribuicao) in distribuicoes.items():
        distribuicao.to_csv(DIRETORIO_DADOS_PROCESSADOS / f"{nome}.csv")
        imprimir_distribuicao(titulo, distribuicao)
        gerar_grafico(distribuicao, f"{titulo} dos concluintes de Ciência da Computação ({ANO})", f"{nome}.png")

    print(
        "\nSexo e idade vêm de registros administrativos de todos os inscritos; as demais "
        "variáveis vêm do Questionário do Estudante e consideram só quem respondeu. "
        "Os arquivos são anonimizados e não podem ser cruzados entre si por estudante."
    )


def principal(argumentos: Iterable[str] | None = None) -> int:
    """Interpreta argumentos da linha de comando e inicia a análise."""
    analisador = argparse.ArgumentParser(description="Analisa o perfil dos concluintes de Ciência da Computação da Unifor no ENADE.")
    analisador.parse_args(argumentos)
    try:
        executar_analise()
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
