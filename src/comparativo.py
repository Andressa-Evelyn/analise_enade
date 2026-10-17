from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DIRETORIO_RAIZ = Path(__file__).resolve().parents[1]
DIRETORIO_DADOS_BRUTOS = DIRETORIO_RAIZ / "data" / "raw"
DIRETORIO_DADOS_PROCESSADOS = DIRETORIO_RAIZ / "data" / "processed"

ANOS_ANALISE = (2008, 2011, 2014, 2017, 2021)
COLUNAS_NOTAS = ["NT_GER", "NT_FG", "NT_CE"]
ROTULOS_NOTAS = {
    "NT_GER": "Nota geral",
    "NT_FG": "Formação geral",
    "NT_CE": "Componente específico",
}

CODIGO_IES_UNIFOR = "29"
CODIGO_UF_CEARA = "23"

# Nos microdados do ENADE, 1, 2 e 3 representam instituições públicas
# (federal, estadual e municipal); 4 e 5 representam instituições privadas.
CATEGORIAS_PUBLICAS = {"1", "2", "3"}
CATEGORIAS_PRIVADAS = {"4", "5"}

# Em 2008, o grupo 40 é Computação e a subárea 4001 é Bacharelado
# em Ciência da Computação. De 2011 em diante, o grupo 4004 identifica
# Ciência da Computação (Bacharelado).
GRUPO_POR_ANO = {
    2008: "40",
    2011: "4004",
    2014: "4004",
    2017: "4004",
    2021: "4004",
}
SUBAREA_POR_ANO = {2008: "4001"}
ANOS_COM_TIPO_INSCRICAO = {2008}


def limpar_codigo(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.strip().str.replace('"', "", regex=False)


def localizar_membro(arquivo_zip: zipfile.ZipFile, ano: int, numero: int) -> str:
    padrao = re.compile(
        rf"(?:^|/)microdados{ano}_arq{numero}\.txt$", re.IGNORECASE
    )
    membros = [nome for nome in arquivo_zip.namelist() if padrao.search(nome)]
    if len(membros) != 1:
        raise FileNotFoundError(
            f"Esperava um arquivo microdados{ano}_arq{numero}.txt em "
            f"{arquivo_zip.filename}; encontrados: {membros}"
        )
    return membros[0]


def ler_colunas(
    arquivo_zip: zipfile.ZipFile, ano: int, numero: int, colunas_desejadas: list[str]
) -> pd.DataFrame:
    membro = localizar_membro(arquivo_zip, ano, numero)

    with arquivo_zip.open(membro) as arquivo:
        cabecalho = pd.read_csv(
            arquivo, sep=";", encoding="latin-1", dtype="string", nrows=0
        ).columns.str.strip().str.replace('"', "", regex=False).tolist()

    colunas = [coluna for coluna in colunas_desejadas if coluna in cabecalho]
    obrigatorias = (
        {"CO_CURSO", *COLUNAS_NOTAS}
        if numero == 3
        else {"CO_CURSO", "CO_GRUPO", "CO_IES", "CO_CATEGAD", "CO_UF_CURSO"}
    )
    ausentes = obrigatorias - set(cabecalho)
    if ausentes:
        raise KeyError(f"Variáveis ausentes em {ano}/arq{numero}: {sorted(ausentes)}")

    with arquivo_zip.open(membro) as arquivo:
        tabela = pd.read_csv(
            arquivo,
            sep=";",
            encoding="latin-1",
            dtype="string",
            usecols=colunas,
            low_memory=False,
        )

    tabela.columns = tabela.columns.str.strip().str.replace('"', "", regex=False)
    for coluna in tabela.columns:
        tabela[coluna] = limpar_codigo(tabela[coluna])
    return tabela


def carregar_edicao(ano: int, caminho_zip: Path) -> pd.DataFrame:
    """Carrega notas e metadados sem presumir que arq1 e arq3 têm a mesma ordem.

    O vínculo é feito por CO_CURSO. Os metadados são reduzidos a uma linha por
    curso, e a função interrompe a análise se um mesmo código tiver informações
    institucionais conflitantes.
    """
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        identificacao = ler_colunas(
            arquivo_zip,
            ano,
            1,
            [
                "CO_CURSO", "CO_GRUPO", "CO_SUBAREA", "CO_IES",
                "CO_CATEGAD", "CO_UF_CURSO", "TP_INSCRICAO",
            ],
        )
        notas = ler_colunas(
            arquivo_zip,
            ano,
            3,
            ["CO_CURSO", *COLUNAS_NOTAS, "TP_INSCRICAO", "PESO_AMOSTRA"],
        )

    # Primeiro, seleciona os cursos elegíveis usando o arquivo de identificação.
    filtro_area = limpar_codigo(identificacao["CO_GRUPO"]) == GRUPO_POR_ANO[ano]
    if ano in SUBAREA_POR_ANO:
        if "CO_SUBAREA" not in identificacao.columns:
            raise KeyError(f"ENADE {ano}: CO_SUBAREA não está disponível.")
        filtro_area &= limpar_codigo(identificacao["CO_SUBAREA"]) == SUBAREA_POR_ANO[ano]

    if ano in ANOS_COM_TIPO_INSCRICAO:
        if "TP_INSCRICAO" not in identificacao.columns:
            raise KeyError(f"ENADE {ano}: TP_INSCRICAO não está disponível.")
        filtro_area &= limpar_codigo(identificacao["TP_INSCRICAO"]) == "0"

    identificacao = identificacao.loc[filtro_area].copy()
    identificacao["CO_CURSO"] = limpar_codigo(identificacao["CO_CURSO"])

    colunas_metadados = [
        "CO_CURSO", "CO_IES", "CO_CATEGAD", "CO_UF_CURSO"
    ]
    for coluna in colunas_metadados[1:]:
        identificacao[coluna] = limpar_codigo(identificacao[coluna])

    # Cada código de curso deve apontar para uma única instituição, categoria e UF.
    metadados = identificacao[colunas_metadados].drop_duplicates()
    conflitos = metadados["CO_CURSO"].duplicated(keep=False)
    if conflitos.any():
        codigos = metadados.loc[conflitos, "CO_CURSO"].drop_duplicates().tolist()
        raise ValueError(
            f"ENADE {ano}: há CO_CURSO com metadados conflitantes: {codigos[:10]}"
        )
    metadados = metadados.drop_duplicates(subset="CO_CURSO")

    if metadados.empty:
        raise ValueError(
            f"ENADE {ano}: nenhum curso encontrado após aplicar os filtros de área."
        )

    # Filtra as notas pelos códigos de curso elegíveis. Não depende da ordem das linhas.
    notas["CO_CURSO"] = limpar_codigo(notas["CO_CURSO"])
    filtro_notas = notas["CO_CURSO"].isin(set(metadados["CO_CURSO"]))
    if ano in ANOS_COM_TIPO_INSCRICAO:
        if "TP_INSCRICAO" not in notas.columns:
            raise KeyError(f"ENADE {ano}: TP_INSCRICAO não está disponível no arq3.")
        filtro_notas &= limpar_codigo(notas["TP_INSCRICAO"]) == "0"

    notas = notas.loc[filtro_notas].copy()
    dados = notas.merge(
        metadados,
        on="CO_CURSO",
        how="inner",
        validate="many_to_one",
    )

    for coluna in COLUNAS_NOTAS:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    if "PESO_AMOSTRA" in dados.columns:
        dados["PESO_AMOSTRA"] = pd.to_numeric(
            dados["PESO_AMOSTRA"], errors="coerce"
        )
    else:
        dados["PESO_AMOSTRA"] = 1.0

    dados["ano"] = ano
    dados = dados.loc[dados["PESO_AMOSTRA"].gt(0)].copy()
    return dados


def calcular_media_curso(dados: pd.DataFrame) -> pd.DataFrame:
    """Calcula uma média por curso; cada curso terá o mesmo peso no grupo."""
    linhas = []
    chaves = ["ano", "CO_IES", "CO_CURSO", "CO_UF_CURSO", "CO_CATEGAD"]

    for identificadores, grupo in dados.groupby(chaves, dropna=False):
        ano, ies, curso, uf, categoria = identificadores
        for coluna in COLUNAS_NOTAS:
            validos = grupo[coluna].notna()
            if not validos.any():
                continue

            valores = grupo.loc[validos, coluna].astype(float)
            pesos = grupo.loc[validos, "PESO_AMOSTRA"].astype(float)
            media = float(np.average(valores, weights=pesos))
            linhas.append(
                {
                    "ano": ano,
                    "CO_IES": ies,
                    "CO_CURSO": curso,
                    "CO_UF_CURSO": uf,
                    "CO_CATEGAD": categoria,
                    "variavel": coluna,
                    "componente": ROTULOS_NOTAS[coluna],
                    "n_estudantes_validos": int(validos.sum()),
                    "media_curso": media,
                }
            )

    return pd.DataFrame(linhas)


def rotular_grupo(linha: pd.Series) -> str | None:
    if linha["CO_IES"] == CODIGO_IES_UNIFOR:
        return "Unifor"
    if linha["CO_UF_CURSO"] == CODIGO_UF_CEARA:
        if linha["CO_CATEGAD"] in CATEGORIAS_PUBLICAS:
            return "Demais cursos públicos do Ceará"
        if linha["CO_CATEGAD"] in CATEGORIAS_PRIVADAS:
            return "Demais cursos privados do Ceará"
        return None
    return "Brasil"


def resumir_grupos(cursos: pd.DataFrame) -> pd.DataFrame:
    cursos = cursos.copy()
    cursos["grupo"] = cursos.apply(rotular_grupo, axis=1)
    cursos = cursos.dropna(subset=["grupo"])

    resumo = (
        cursos.groupby(["ano", "variavel", "componente", "grupo"], as_index=False)
        .agg(
            media=("media_curso", "mean"),
            desvio_padrao_entre_cursos=("media_curso", "std"),
            quantidade_cursos=("CO_CURSO", "nunique"),
            quantidade_instituicoes=("CO_IES", "nunique"),
        )
    )
    return resumo


def criar_diferencas(resumo: pd.DataFrame) -> pd.DataFrame:
    referencia = resumo.loc[
        resumo["grupo"] == "Unifor",
        ["ano", "variavel", "media"],
    ].rename(columns={"media": "media_unifor"})

    comparacao = resumo.merge(referencia, on=["ano", "variavel"], how="left")
    comparacao["diferenca_unifor"] = comparacao["media_unifor"] - comparacao["media"]
    comparacao.loc[comparacao["grupo"] == "Unifor", "diferenca_unifor"] = 0.0
    return comparacao


def gerar_graficos(resumo: pd.DataFrame, diretorio_saida: Path) -> None:
    if plt is None:
        print("Matplotlib não instalado; gráficos não foram gerados.")
        return

    ordem_grupos = [
        "Unifor",
        "Demais cursos públicos do Ceará",
        "Demais cursos privados do Ceará",
        "Brasil",
    ]

    for ano, dados_ano in resumo.groupby("ano"):
        tabela = dados_ano.pivot(index="grupo", columns="componente", values="media")
        tabela = tabela.reindex(ordem_grupos)
        colunas = [ROTULOS_NOTAS[c] for c in COLUNAS_NOTAS]
        tabela = tabela.reindex(columns=colunas)

        figura, eixo = plt.subplots(figsize=(11, 6))
        tabela.plot(kind="bar", ax=eixo)
        eixo.set(
            title=f"ENADE {ano}: comparação das notas médias por curso",
            xlabel="Grupo de comparação",
            ylabel="Média da nota por curso",
        )
        eixo.tick_params(axis="x", rotation=20)
        eixo.legend(title="Componente")
        figura.tight_layout()
        figura.savefig(
            diretorio_saida / f"comparativo_notas_{ano}.png", dpi=160
        )
        plt.close(figura)


def executar_analise() -> None:
    edicoes = []
    for ano in ANOS_ANALISE:
        correspondencias = sorted(
            DIRETORIO_DADOS_BRUTOS.glob(f"microdados_enade_{ano}*.zip")
        )
        if len(correspondencias) > 1:
            raise ValueError(f"Mais de um ZIP encontrado para {ano}: {correspondencias}")
        if correspondencias:
            edicoes.append((ano, correspondencias[0]))

    if not edicoes:
        raise FileNotFoundError(
            f"Nenhum ZIP configurado foi encontrado em {DIRETORIO_DADOS_BRUTOS}."
        )

    DIRETORIO_DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    tabelas_cursos = []

    for ano, caminho_zip in edicoes:
        dados = carregar_edicao(ano, caminho_zip)
        cursos = calcular_media_curso(dados)
        tabelas_cursos.append(cursos)
        print(
            f"ENADE {ano}: {len(dados)} registros no recorte; "
            f"{cursos['CO_CURSO'].nunique()} cursos identificados."
        )

    medias_cursos = pd.concat(tabelas_cursos, ignore_index=True)
    resumo = resumir_grupos(medias_cursos)
    diferencas = criar_diferencas(resumo)

    medias_cursos.to_csv(
        DIRETORIO_DADOS_PROCESSADOS / "comparativo_medias_por_curso.csv",
        index=False,
    )
    resumo.to_csv(
        DIRETORIO_DADOS_PROCESSADOS / "comparativo_resumo_grupos.csv",
        index=False,
    )
    diferencas.to_csv(
        DIRETORIO_DADOS_PROCESSADOS / "comparativo_diferencas_unifor.csv",
        index=False,
    )
    gerar_graficos(resumo, DIRETORIO_DADOS_PROCESSADOS)

    print("\nMédias por grupo:")
    print(
        resumo.sort_values(["ano", "variavel", "grupo"])
        [["ano", "componente", "grupo", "media", "quantidade_cursos", "quantidade_instituicoes"]]
        .round(2)
        .to_string(index=False)
    )
    print("\nDiferenças entre a média da Unifor e a média de cada grupo (pontos):")
    print(
        diferencas.sort_values(["ano", "variavel", "grupo"])
        [["ano", "componente", "grupo", "media_unifor", "media", "diferenca_unifor"]]
        .round(2)
        .to_string(index=False)
    )
    print(
        "\nNota metodológica: a comparação usa a média das médias dos cursos, "
        "atribuindo o mesmo peso a cada curso. Em 2008, a média de cada curso "
        "é ponderada por PESO_AMOSTRA. A edição de 2005 foi excluída porque "
        "CO_GRUPO=40 identifica Computação de forma ampla e não há CO_SUBAREA "
        "disponível no arquivo de identificação para isolar Ciência da Computação."
    )


def principal() -> int:
    try:
        executar_analise()
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
