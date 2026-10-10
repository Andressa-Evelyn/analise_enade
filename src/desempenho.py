from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DIRETORIO_RAIZ = Path(__file__).resolve().parents[1]
DIRETORIO_DADOS_BRUTOS = DIRETORIO_RAIZ / "data" / "raw"
DIRETORIO_DADOS_PROCESSADOS = DIRETORIO_RAIZ / "data" / "processed"

# Códigos históricos confirmados nos dicionários oficiais de cada edição.
CODIGO_IES_ALVO = "29"  # Unifor
CODIGO_MUNICIPIO_ALVO = "2304400"  # Fortaleza
CODIGO_GRUPO_POR_ANO = {
    2005: "40",  # Computação; the Unifor course code identifies CC
    2008: "40",  # Computação; subarea 4001 is Bacharelado em Ciência da Computação
    2011: "4004",  # Computação (Bacharelado)
    2014: "4004",  # Ciência da Computação (Bacharelado)
    2017: "4004",  # Ciência da Computação (Bacharelado)
    2021: "4004",  # Ciência da Computação (Bacharelado)
}
CODIGO_CURSO_POR_ANO = {ano: "2209" for ano in CODIGO_GRUPO_POR_ANO}
CODIGO_SUBAREA_POR_ANO = {2008: "4001"}
ANOS_COM_TIPO_INSCRICAO = {2005, 2008}
COLUNAS_NOTAS = ["NT_GER", "NT_FG", "NT_CE"]
ROTULOS_NOTAS = {
    "NT_GER": "Nota geral",
    "NT_FG": "Formação geral",
    "NT_CE": "Componente específico",
}


def localizar_arquivo_zip(ano: int) -> Path | None:
    """Localiza o único arquivo ZIP de microdados ENADE para o ano informado."""
    correspondencias = sorted(DIRETORIO_DADOS_BRUTOS.glob(f"microdados_enade_{ano}*.zip"))
    if len(correspondencias) > 1:
        raise ValueError(f"Mais de um ZIP encontrado para {ano}: {correspondencias}")
    return correspondencias[0] if correspondencias else None


def localizar_membro(arquivo_zip: zipfile.ZipFile, ano: int, numero_arquivo: int) -> str:
    """Encontra dentro do ZIP o arquivo de microdados indicado pelo ano e número."""
    padrao = re.compile(rf"(?:^|/)microdados{ano}_arq{numero_arquivo}\.txt$", re.IGNORECASE)
    correspondencias = [nome for nome in arquivo_zip.namelist() if padrao.search(nome)]
    if len(correspondencias) != 1:
        raise FileNotFoundError(
            f"Esperava um arquivo microdados{ano}_arq{numero_arquivo}.txt em "
            f"{arquivo_zip.filename}; encontrados: {correspondencias}"
        )
    return correspondencias[0]


def ler_tabela(arquivo_zip: zipfile.ZipFile, ano: int, numero_arquivo: int) -> pd.DataFrame:
    """Lê uma tabela CSV contida no ZIP de microdados da edição."""
    membro = localizar_membro(arquivo_zip, ano, numero_arquivo)
    with arquivo_zip.open(membro) as objeto_arquivo:
        tabela = pd.read_csv(
            objeto_arquivo,
            sep=";",
            dtype="string",
            encoding="latin-1",
            low_memory=False,
        )
    tabela.columns = tabela.columns.str.strip().str.replace('"', "", regex=False)
    return tabela


def limpar_codigo(serie: pd.Series) -> pd.Series:
    """Padroniza códigos textuais, removendo espaços e aspas excedentes."""
    return serie.astype("string").str.strip().str.replace('"', "", regex=False)


def criar_filtro_curso_alvo(identificacao: pd.DataFrame, ano: int) -> pd.Series:
    """Monta o filtro para localizar Ciência da Computação da Unifor na edição."""
    codigo_grupo = CODIGO_GRUPO_POR_ANO.get(ano)
    if codigo_grupo is None:
        raise ValueError(
            f"O código CO_GRUPO da Ciência da Computação para {ano} ainda precisa "
            "ser confirmado no dicionário dessa edição."
        )

    filtros = (
        (limpar_codigo(identificacao["CO_IES"]) == CODIGO_IES_ALVO)
        & (limpar_codigo(identificacao["CO_MUNIC_CURSO"]) == CODIGO_MUNICIPIO_ALVO)
        & (limpar_codigo(identificacao["CO_GRUPO"]) == codigo_grupo)
        & (limpar_codigo(identificacao["CO_CURSO"]) == CODIGO_CURSO_POR_ANO[ano])
    )
    codigo_subarea = CODIGO_SUBAREA_POR_ANO.get(ano)
    if codigo_subarea is not None:
        filtros &= limpar_codigo(identificacao["CO_SUBAREA"]) == codigo_subarea
    if ano in ANOS_COM_TIPO_INSCRICAO:
        filtros &= limpar_codigo(identificacao["TP_INSCRICAO"]) == "0"
    return filtros


def identificar_cursos_alvo(identificacao: pd.DataFrame, ano: int) -> set[str]:
    """Retorna os códigos de curso que atendem aos filtros da Unifor."""
    filtros = criar_filtro_curso_alvo(identificacao, ano)
    cursos = set(limpar_codigo(identificacao.loc[filtros, "CO_CURSO"]).dropna())
    if not cursos:
        raise ValueError(
            f"Nenhum curso corresponde aos filtros de Unifor/CC em {ano}. "
            "Confira CO_IES, CO_MUNIC_CURSO e CO_GRUPO no dicionário da edição."
        )
    return cursos


def carregar_notas(caminho_zip: Path, ano: int) -> tuple[pd.DataFrame, set[str], int]:
    """Carrega, filtra e converte as notas da Unifor para tipos numéricos."""
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        identificacao = ler_tabela(arquivo_zip, ano, 1)
        notas = ler_tabela(arquivo_zip, ano, 3)

    cursos = identificar_cursos_alvo(identificacao, ano)
    mascara_alvo = criar_filtro_curso_alvo(identificacao, ano)
    registros_identificados = int(mascara_alvo.sum())
    notas["CO_CURSO"] = limpar_codigo(notas["CO_CURSO"])
    notas = notas.loc[notas["CO_CURSO"].isin(cursos)].copy()
    if ano in ANOS_COM_TIPO_INSCRICAO:
        notas = notas.loc[limpar_codigo(notas["TP_INSCRICAO"]) == "0"].copy()

    for coluna in COLUNAS_NOTAS:
        if coluna not in notas:
            raise KeyError(f"A coluna {coluna} não existe no arquivo de notas de {ano}.")
        notas[coluna] = pd.to_numeric(notas[coluna], errors="coerce")

    notas = notas.dropna(subset=COLUNAS_NOTAS, how="all")
    if notas.empty:
        raise ValueError(f"Não há notas válidas para o curso da Unifor em {ano}.")
    return notas, cursos, registros_identificados


def quantil_ponderado(valores: np.ndarray, pesos: np.ndarray, quantil: float) -> float:
    """Calcula um quantil considerando o peso de cada observação."""
    ordem = np.argsort(valores)
    valores_ordenados = valores[ordem]
    pesos_acumulados = np.cumsum(pesos[ordem])
    return float(valores_ordenados[np.searchsorted(pesos_acumulados, quantil * pesos_acumulados[-1], side="left")])


def resumir_notas(notas: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Calcula estatísticas descritivas das notas de cada componente."""
    linhas = []
    tem_pesos = "PESO_AMOSTRA" in notas
    pesos = pd.to_numeric(notas["PESO_AMOSTRA"], errors="coerce") if tem_pesos else None
    for coluna in COLUNAS_NOTAS:
        validos = notas[coluna].notna()
        valores = notas.loc[validos, coluna].to_numpy(dtype=float)
        if tem_pesos:
            validos &= pesos.gt(0)
            valores_selecionados = notas.loc[validos, coluna].to_numpy(dtype=float)
            pesos_selecionados = pesos.loc[validos].to_numpy(dtype=float)
            peso_total = pesos_selecionados.sum()
            media = float(np.average(valores_selecionados, weights=pesos_selecionados))
            desvio_padrao = float(np.sqrt(np.average((valores_selecionados - media) ** 2, weights=pesos_selecionados)))
            q1, mediana, q3 = [
                quantil_ponderado(valores_selecionados, pesos_selecionados, quantil)
                for quantil in (0.25, 0.5, 0.75)
            ]
            quantidade = len(valores_selecionados)
        else:
            valores_selecionados = valores
            peso_total = float(len(valores))
            media = float(np.mean(valores))
            desvio_padrao = float(np.std(valores, ddof=1)) if len(valores) > 1 else 0.0
            q1, mediana, q3 = np.quantile(valores, [0.25, 0.5, 0.75])
            quantidade = len(valores)

        linhas.append(
            {
                "ano": ano,
                "variavel": coluna,
                "componente": ROTULOS_NOTAS[coluna],
                "n": quantidade,
                "peso_total": peso_total,
                "media": media,
                "desvio_padrao": desvio_padrao,
                "minimo": float(np.min(valores_selecionados)),
                "q1": float(q1),
                "mediana": float(mediana),
                "q3": float(q3),
                "maximo": float(np.max(valores_selecionados)),
            }
        )
    return pd.DataFrame(linhas)


def calcular_acertos_por_questao(notas: pd.DataFrame, coluna_vetor: str, componente: str) -> pd.DataFrame:
    """Calcula quantidade e taxa de acertos para cada posição do vetor de respostas."""
    if coluna_vetor not in notas:
        return pd.DataFrame(columns=["componente", "questao", "n_validas", "acertos", "peso_validas", "acertos_ponderados", "taxa_acerto"])

    vetores = notas[coluna_vetor].dropna().astype(str).str.replace('"', "", regex=False)
    pesos = pd.to_numeric(notas["PESO_AMOSTRA"], errors="coerce").fillna(0) if "PESO_AMOSTRA" in notas else None
    respostas_por_questao: dict[int, list[tuple[int, float]]] = {}
    for indice, vetor in vetores.items():
        peso = float(pesos.loc[indice]) if pesos is not None else 1.0
        if peso <= 0:
            continue
        for posicao, valor in enumerate(vetor.strip(), start=1):
            if valor in {"0", "1"}:
                respostas_por_questao.setdefault(posicao, []).append((int(valor), peso))

    linhas = []
    for posicao, respostas in sorted(respostas_por_questao.items()):
        acertos = sum(resposta for resposta, _ in respostas)
        peso_validas = sum(peso for _, peso in respostas)
        acertos_ponderados = sum(resposta * peso for resposta, peso in respostas)
        linhas.append(
            {
                "componente": componente,
                "questao": f"{componente}_{posicao:02d}",
                "n_validas": len(respostas),
                "acertos": acertos,
                "peso_validas": peso_validas,
                "acertos_ponderados": acertos_ponderados,
                "taxa_acerto": acertos_ponderados / peso_validas,
            }
        )
    return pd.DataFrame(linhas)


def gerar_graficos(notas: pd.DataFrame, resumo: pd.DataFrame, acertos_por_questao: pd.DataFrame, ano: int, diretorio_saida: Path) -> None:
    """Gera histogramas de notas e gráficos das menores taxas de acerto."""
    if plt is None:
        print("Matplotlib não instalado; gráficos não foram gerados. Instale requirements.txt.")
        return

    for coluna in COLUNAS_NOTAS:
        valores = notas[coluna].dropna()
        if valores.empty:
            continue
        figura, eixo = plt.subplots(figsize=(8, 4.5))
        pesos = pd.to_numeric(notas.loc[valores.index, "PESO_AMOSTRA"], errors="coerce").fillna(0) if "PESO_AMOSTRA" in notas else None
        eixo.hist(valores, bins=10, weights=pesos, color="#197a78", edgecolor="white")
        rotulo_eixo_y = "Frequência ponderada" if pesos is not None else "Número de estudantes"
        eixo.set(title=f"{ROTULOS_NOTAS[coluna]} dos concluintes ({ano})", xlabel="Nota", ylabel=rotulo_eixo_y)
        figura.tight_layout()
        figura.savefig(diretorio_saida / f"distribuicao_{coluna.lower()}_{ano}.png", dpi=160)
        plt.close(figura)

    for componente in ("OFG", "OCE"):
        questoes_componente = acertos_por_questao.loc[acertos_por_questao["componente"] == componente].nsmallest(8, "taxa_acerto")
        if questoes_componente.empty:
            continue
        figura, eixo = plt.subplots(figsize=(9, 4.5))
        eixo.bar(questoes_componente["questao"], questoes_componente["taxa_acerto"], color="#d9822b")
        eixo.set(title=f"Menores taxas de acerto: {componente} ({ano})", ylabel="Taxa de acerto", ylim=(0, 1))
        eixo.tick_params(axis="x", rotation=35)
        figura.tight_layout()
        figura.savefig(diretorio_saida / f"menores_acertos_{componente.lower()}_{ano}.png", dpi=160)
        plt.close(figura)


def listar_edicoes_disponiveis() -> list[tuple[int, Path]]:
    """Lista as edições configuradas que possuem ZIP de microdados disponível."""
    edicoes = []
    for ano in sorted(CODIGO_GRUPO_POR_ANO):
        arquivo_zip = localizar_arquivo_zip(ano)
        if arquivo_zip:
            edicoes.append((ano, arquivo_zip))
    return edicoes


def executar_analise() -> None:
    """Processa as edições disponíveis, salva tabelas e gera gráficos."""
    edicoes_encontradas = listar_edicoes_disponiveis()
    edicoes = [
        (ano, arquivo_zip)
        for ano, arquivo_zip in edicoes_encontradas
        if ano in CODIGO_GRUPO_POR_ANO
    ]
    if not edicoes_encontradas:
        raise FileNotFoundError(
            f"Nenhum ZIP ENADE de uma edição configurada foi encontrado em {DIRETORIO_DADOS_BRUTOS}."
        )
    if not edicoes:
        raise ValueError("Não há edição com CO_GRUPO confirmado configurado no script.")

    DIRETORIO_DADOS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    resumos = []
    tabelas_acertos = []
    for ano, arquivo_zip in edicoes:
        notas, cursos, registros_identificados = carregar_notas(arquivo_zip, ano)
        resumo = resumir_notas(notas, ano)
        acertos_por_questao = pd.concat(
            [
                calcular_acertos_por_questao(notas, "DS_VT_ACE_OFG", "OFG"),
                calcular_acertos_por_questao(notas, "DS_VT_ACE_OCE", "OCE"),
            ],
            ignore_index=True,
        )
        resumos.append(resumo)
        tabelas_acertos.append(acertos_por_questao.assign(ano=ano))

        diretorio_saida = DIRETORIO_DADOS_PROCESSADOS / f"desempenho_{ano}"
        diretorio_saida.mkdir(parents=True, exist_ok=True)
        resumo.to_csv(diretorio_saida / "resumo_notas.csv", index=False)
        acertos_por_questao.to_csv(diretorio_saida / "acertos_por_questao.csv", index=False)
        gerar_graficos(notas, resumo, acertos_por_questao, ano, diretorio_saida)

        print(
            f"\nENADE {ano}: {registros_identificados} registros identificados; "
            f"{len(notas)} com ao menos uma nota; cursos: {', '.join(sorted(cursos))}"
        )
        print(resumo[["componente", "n", "media", "mediana", "desvio_padrao", "q1", "q3"]].round(2).to_string(index=False))
        print("\nQuestões objetivas com menores taxas de acerto:")
        if acertos_por_questao.empty:
            print("Não há vetores binários de acerto disponíveis nesta edição.")
        else:
            print(
                acertos_por_questao.sort_values("taxa_acerto")
                .groupby("componente", group_keys=False)
                .head(5)[["questao", "n_validas", "acertos", "taxa_acerto"]]
                .to_string(index=False, formatters={"taxa_acerto": "{:.1%}".format})
            )

    resumo_consolidado = pd.concat(resumos, ignore_index=True)
    acertos_consolidados = pd.concat(tabelas_acertos, ignore_index=True)
    resumo_consolidado.to_csv(DIRETORIO_DADOS_PROCESSADOS / "desempenho_resumo_edicoes.csv", index=False)
    acertos_consolidados.to_csv(DIRETORIO_DADOS_PROCESSADOS / "desempenho_acertos_edicoes.csv", index=False)

    anos_presentes = sorted(ano for ano, _ in edicoes)
    if len(anos_presentes) > 1:
        medias = resumo_consolidado.pivot(index="variavel", columns="ano", values="media")
        linhas_comparacao = []
        for coluna in COLUNAS_NOTAS:
            for indice, ano in enumerate(anos_presentes):
                ano_anterior = anos_presentes[indice - 1] if indice > 0 else None
                linhas_comparacao.append(
                    {
                        "ano": ano,
                        "componente": ROTULOS_NOTAS[coluna],
                        "media": medias.loc[coluna, ano],
                        "edicao_anterior": ano_anterior,
                        "variacao_ano_anterior": (
                            medias.loc[coluna, ano] - medias.loc[coluna, ano_anterior]
                            if ano_anterior is not None
                            else pd.NA
                        ),
                        "variacao_desde_primeira_edicao": medias.loc[coluna, ano]
                        - medias.loc[coluna, anos_presentes[0]],
                    }
                )
        comparacao = pd.DataFrame(linhas_comparacao)
        comparacao.to_csv(DIRETORIO_DADOS_PROCESSADOS / "desempenho_historico_variacao.csv", index=False)
        print("\nMédias por edição e variação em relação à edição anterior:")
        print(comparacao.round(2).to_string(index=False))

        if plt is not None:
            figura, eixo = plt.subplots(figsize=(10, 5.5))
            for coluna in COLUNAS_NOTAS:
                eixo.plot(
                    anos_presentes,
                    [medias.loc[coluna, ano] for ano in anos_presentes],
                    marker="o",
                    label=ROTULOS_NOTAS[coluna],
                )
            eixo.set(title="Evolução das notas médias da Ciência da Computação (Unifor)", xlabel="Edição ENADE", ylabel="Nota média")
            eixo.set_xticks(anos_presentes)
            eixo.legend()
            figura.tight_layout()
            figura.savefig(DIRETORIO_DADOS_PROCESSADOS / "desempenho_evolucao_medias.png", dpi=160)
            plt.close(figura)

    edicao_2024_ausente = localizar_arquivo_zip(2024) is None
    if edicao_2024_ausente:
        print("\nENADE 2024 ainda não incluído: o ZIP não está em data/raw e seus códigos precisam ser validados antes de processar.")

    print(
        "\nA taxa por questão considera apenas respostas codificadas como 0 (incorreta) "
        "ou 1 (correta). Os vetores identificam posições da prova, não o conteúdo; "
        "associe-as ao caderno/gabarito antes de nomear os conteúdos."
    )
    if plt is None:
        print("Para gerar figuras, instale as dependências listadas em requirements.txt.")


def principal(argumentos: Iterable[str] | None = None) -> int:
    """Interpreta argumentos da linha de comando e inicia a análise."""
    analisador = argparse.ArgumentParser(description="Analisa desempenho ENADE de Ciência da Computação da Unifor.")
    analisador.parse_args(argumentos)
    try:
        executar_analise()
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
