"""Seção 5.5 do plano de trabalho: participação e engajamento dos estudantes no ENADE.

Responde às duas perguntas do plano de trabalho para Ciência da Computação da Unifor:
1. Qual a proporção de estudantes inscritos que compareceram e tiveram participação válida?
2. Quantas provas foram entregues em branco ou com apenas parte das questões respondidas?

Todas as análises e visualizações comparam a Unifor de forma agregada com as demais IES do
Ceará e do Brasil, separadas por rede (pública, privada e junção das duas):
- Unifor
- CE públicas (IES públicas do Ceará)
- CE privadas (demais IES privadas do Ceará, exceto Unifor)
- CE geral (junção de públicas + privadas do Ceará, exceto Unifor)
- Brasil públicas (IES públicas do Brasil)
- Brasil privadas (IES privadas do Brasil, exceto Unifor)
- Brasil geral (junção de públicas + privadas do Brasil, exceto Unifor)

Gera em data/processed/participacao/:
- participacao_historico_unifor.csv: série histórica 2005–2021 da Unifor;
- participacao_resumo_grupos.csv: série comparativa 2008–2021 para todos os 7 grupos agregados;
- participacao_detalhe_componentes_grupos.csv: preenchimento completo, parcial e em branco de cada
  caderno da prova (Objetiva FG, Objetiva CE, Discursiva FG, Discursiva CE) por grupo (2017 e 2021);
- participacao_testes_comparacao.csv: testes Exato de Fisher com V de Cramér e correção de Holm
  comparando a Unifor contra os 6 grupos de referência (CE e Brasil: públicas, privadas e geral);
- participacao_impacto_notas_grupos.csv: impacto de deixar discursivas em branco nas notas médias
  (NT_GER, NT_FG, NT_CE) na Unifor e em cada grupo agregado do CE e do Brasil;
- Gráficos .png comparativos entre a Unifor e os grupos agregados do CE e do Brasil.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import BinaryIO, Iterable

import numpy as np
import pandas as pd
from scipy import stats

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DIRETORIO_RAIZ = Path(__file__).resolve().parents[1]
DIRETORIO_DADOS_BRUTOS = DIRETORIO_RAIZ / "data" / "raw"
DIRETORIO_DADOS_BRUTOS_ALTERNATIVO = DIRETORIO_RAIZ.parent / "raw"
DIRETORIO_SAIDA = DIRETORIO_RAIZ / "data" / "processed" / "participacao"

ANOS_HISTORICO_UNIFOR = (2005, 2008, 2011, 2014, 2017, 2021)
ANOS_COMPARACAO_GRUPOS = (2008, 2011, 2014, 2017, 2021)
ANOS_RECENTES = (2017, 2021)
ANOS_AMOSTRAIS = {2005, 2008}

CODIGO_IES_UNIFOR = "29"
CODIGO_CURSO_UNIFOR = "2209"
CODIGO_UF_CEARA = "23"
CATEGORIAS_PUBLICAS = {"1", "2", "3"}

CODIGO_GRUPO_POR_ANO = {
    2005: "40",
    2008: "40",
    2011: "4004",
    2014: "4004",
    2017: "4004",
    2021: "4004",
}
CODIGO_SUBAREA_POR_ANO = {2008: "4001"}

COLUNAS_ARQ1 = [
    "CO_CURSO",
    "CO_IES",
    "CO_CATEGAD",
    "CO_GRUPO",
    "CO_SUBAREA",
    "CO_MUNIC_CURSO",
    "CO_UF_CURSO",
    "TP_INSCRICAO",
    "PESO_AMOSTRA",
]

COLUNAS_DISCURSIVAS_PADRAO = ["TP_SFG_D1", "TP_SFG_D2", "TP_SCE_D1", "TP_SCE_D2", "TP_SCE_D3"]
COLUNAS_PRESENCA = ["TP_PRES", "TP_PR_GER", "TP_PR_OB_FG", "TP_PR_DI_FG", "TP_PR_OB_CE", "TP_PR_DI_CE"]
COLUNAS_VETORES = ["DS_VT_GAB_OFG_FIN", "DS_VT_GAB_OCE_FIN", "DS_VT_ESC_OFG", "DS_VT_ACE_OFG", "DS_VT_ESC_OCE", "DS_VT_ACE_OCE"]
COLUNAS_NOTAS = ["NT_GER", "NT_FG", "NT_OBJ_FG", "NT_DIS_FG", "NT_CE", "NT_OBJ_CE", "NT_DIS_CE"]

NIVEL_SIGNIFICANCIA = 0.05

# Os 7 grupos agregados (Unifor + CE púb/priv/geral + Brasil púb/priv/geral; Unifor excluída de privadas e geral)
GRUPOS_AGREGADOS = [
    "Unifor",
    "CE públicas",
    "CE privadas",
    "CE geral",
    "Brasil públicas",
    "Brasil privadas",
    "Brasil geral",
]

# Recorte focado apenas no Ceará (Unifor excluída de CE privadas e CE geral)
GRUPOS_CEARA = [
    "Unifor",
    "CE públicas",
    "CE privadas",
    "CE geral",
]

CORES_7_GRUPOS = [
    "#197a78",  # Unifor (verde-azulado escuro)
    "#5c4d9a",  # CE públicas (roxo escuro)
    "#d9822b",  # CE privadas (laranja)
    "#8c6bb1",  # CE geral (lilás/roxo médio)
    "#2b5c8f",  # Brasil públicas (azul)
    "#e0a858",  # Brasil privadas (amarelo-terra)
    "#7f7f7f",  # Brasil geral (cinza)
]


def normalizar_coluna(nome: str) -> str:
    """Remove espaços e aspas do nome de uma coluna."""
    return nome.strip().replace('"', "")


def limpar_codigo(serie: pd.Series) -> pd.Series:
    """Padroniza códigos textuais, removendo espaços e aspas excedentes."""
    return serie.fillna("").astype(str).str.strip().str.replace('"', "", regex=False)


class FonteMicrodados:
    """Leitura unificada de arquivo ZIP ou pasta extraída de microdados de uma edição."""

    def __init__(self, caminho: Path, ano: int) -> None:
        self.caminho = caminho
        self.ano = ano
        self.padrao = re.compile(rf"(?:^|/)microdados{ano}_arq(\d+)\.txt$", re.IGNORECASE)
        self.zip: zipfile.ZipFile | None = None
        if caminho.is_file():
            self.zip = zipfile.ZipFile(caminho)
            self._itens = {i.filename: i for i in self.zip.infolist() if not i.is_dir()}
        elif caminho.is_dir():
            arquivos = sorted((p for p in caminho.rglob("*") if p.is_file()), key=lambda p: p.as_posix())
            self._itens = {p.relative_to(caminho).as_posix(): p for p in arquivos}
        else:
            raise FileNotFoundError(f"Fonte de microdados não encontrada: {caminho}")

    def fechar(self) -> None:
        if self.zip is not None:
            self.zip.close()

    def localizar_arq(self, numero: int) -> str:
        for nome in self._itens:
            correspondencia = self.padrao.search(nome)
            if correspondencia and int(correspondencia.group(1)) == numero:
                return nome
        raise FileNotFoundError(f"Arquivo microdados{self.ano}_arq{numero}.txt não encontrado em {self.caminho}.")

    def abrir(self, nome: str) -> BinaryIO:
        item = self._itens[nome]
        return self.zip.open(item) if self.zip is not None else item.open("rb")


def localizar_fonte_ano(ano: int, diretorio_preferido: Path | None = None) -> Path:
    """Procura o ZIP ou a pasta da edição em data/raw ou ../raw."""
    prefixo = f"microdados_enade_{ano}"
    diretorios_busca = []
    if diretorio_preferido is not None:
        diretorios_busca.append(diretorio_preferido)
    diretorios_busca.extend([DIRETORIO_DADOS_BRUTOS, DIRETORIO_DADOS_BRUTOS_ALTERNATIVO])

    candidatas: list[Path] = []
    vistos: set[Path] = set()
    for base in diretorios_busca:
        if not base.exists():
            continue
        base_resolvida = base.resolve()
        if base_resolvida in vistos:
            continue
        vistos.add(base_resolvida)
        for item in sorted(base_resolvida.iterdir()):
            if item.name.lower().startswith(prefixo) and (item.is_dir() or item.suffix.lower() == ".zip"):
                candidatas.append(item)

    zips = [c for c in candidatas if c.is_file()]
    pastas = [c for c in candidatas if c.is_dir()]
    escolhidas = zips or pastas
    if not escolhidas:
        raise FileNotFoundError(
            f"Não foi encontrada fonte de microdados para {ano} em {DIRETORIO_DADOS_BRUTOS} nem em {DIRETORIO_DADOS_BRUTOS_ALTERNATIVO}."
        )
    return escolhidas[0]


def ler_tabela_filtrada(fonte: FonteMicrodados, numero_arq: int, colunas_desejadas: Iterable[str]) -> pd.DataFrame:
    """Lê apenas as colunas disponíveis de um arquivo de microdados."""
    membro = fonte.localizar_arq(numero_arq)
    with fonte.abrir(membro) as arq:
        cabecalho_bruto = pd.read_csv(arq, sep=";", nrows=0, encoding="latin-1").columns.tolist()
    mapa_colunas = {normalizar_coluna(col): col for col in cabecalho_bruto}
    colunas_presentes = [mapa_colunas[c] for c in colunas_desejadas if c in mapa_colunas]

    with fonte.abrir(membro) as arq:
        tabela = pd.read_csv(
            arq,
            sep=";",
            dtype="string",
            encoding="latin-1",
            usecols=colunas_presentes,
            low_memory=False,
        )
    tabela.columns = [normalizar_coluna(c) for c in tabela.columns]
    for col in tabela.columns:
        tabela[col] = limpar_codigo(tabela[col])
    return tabela


def classificar_cursos_edicao(arq1: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Filtra os cursos de Ciência da Computação da edição e classifica por UF e rede (pública vs. privada)."""
    grupo_alvo = CODIGO_GRUPO_POR_ANO[ano]
    mascara = arq1["CO_GRUPO"] == grupo_alvo
    if ano in CODIGO_SUBAREA_POR_ANO and "CO_SUBAREA" in arq1.columns:
        mascara &= arq1["CO_SUBAREA"] == CODIGO_SUBAREA_POR_ANO[ano]
    if ano in ANOS_AMOSTRAIS and "TP_INSCRICAO" in arq1.columns:
        mascara &= arq1["TP_INSCRICAO"] == "0"

    colunas_metadados = [c for c in ["CO_CURSO", "CO_IES", "CO_CATEGAD", "CO_UF_CURSO", "CO_MUNIC_CURSO"] if c in arq1.columns]
    cursos = arq1.loc[mascara, colunas_metadados].drop_duplicates("CO_CURSO").set_index("CO_CURSO")

    eh_unifor = (cursos["CO_IES"] == CODIGO_IES_UNIFOR) & (cursos.index == CODIGO_CURSO_UNIFOR)
    if not eh_unifor.any():
        raise ValueError(f"Curso de Ciência da Computação da Unifor (CO_CURSO={CODIGO_CURSO_UNIFOR}) não encontrado em {ano}.")

    eh_ceara = (cursos["CO_UF_CURSO"] == CODIGO_UF_CEARA) & ~eh_unifor
    # A Unifor é registrada com CO_CATEGAD=2 em algumas edições, mas é privada sem fins lucrativos;
    # garantimos que ela nunca entre como pública.
    eh_publica = cursos["CO_CATEGAD"].isin(CATEGORIAS_PUBLICAS) & ~eh_unifor

    cursos["rede"] = np.where(eh_publica, "Pública", "Privada")
    cursos["eh_unifor"] = eh_unifor
    cursos["eh_ceara_demais"] = eh_ceara
    return cursos


def selecionar_grupo_agregado(df: pd.DataFrame, nome_grupo: str) -> pd.DataFrame:
    """Filtra o DataFrame de estudantes para um dos 7 grupos agregados de análise."""
    if nome_grupo == "Unifor":
        return df.loc[df["eh_unifor"]]
    if nome_grupo == "CE públicas":
        return df.loc[df["eh_ceara_demais"] & (df["rede"] == "Pública")]
    if nome_grupo == "CE privadas":
        return df.loc[df["eh_ceara_demais"] & (df["rede"] == "Privada")]
    if nome_grupo == "CE geral":
        return df.loc[df["eh_ceara_demais"]]
    if nome_grupo == "Brasil públicas":
        return df.loc[~df["eh_unifor"] & (df["rede"] == "Pública")]
    if nome_grupo == "Brasil privadas":
        return df.loc[~df["eh_unifor"] & (df["rede"] == "Privada")]
    if nome_grupo == "Brasil geral":
        return df.loc[~df["eh_unifor"]]
    raise ValueError(f"Grupo desconhecido: {nome_grupo}")


def contar_questoes_objetivas_em_branco(
    vetor_escolha: pd.Series,
    vetor_acerto: pd.Series,
    vetor_gabarito: pd.Series | None = None,
) -> tuple[pd.Series, pd.Series]:
    """Conta quantas questões objetivas aplicáveis ao curso foram deixadas em branco ('.') por estudante."""
    esc_lista = vetor_escolha.fillna("").astype(str).tolist()
    ace_lista = vetor_acerto.fillna("").astype(str).tolist()
    gab_lista = vetor_gabarito.fillna("").astype(str).tolist() if vetor_gabarito is not None else [""] * len(esc_lista)

    brancos = np.zeros(len(esc_lista), dtype=int)
    aplicaveis = np.zeros(len(esc_lista), dtype=int)
    codigos_acerto_validos = {"0", "1", "8", "9"}

    for idx, (esc, ace, gab) in enumerate(zip(esc_lista, ace_lista, gab_lista)):
        limite = min(len(esc), len(ace)) if len(ace) > 0 else len(esc)
        qtd_branco = 0
        qtd_aplicavel = 0
        for pos in range(limite):
            c_ace = ace[pos] if pos < len(ace) else ""
            c_gab = gab[pos] if pos < len(gab) else ""
            if c_ace in codigos_acerto_validos and c_gab not in {"N", " "}:
                qtd_aplicavel += 1
                if esc[pos] == ".":
                    qtd_branco += 1
        brancos[idx] = qtd_branco
        aplicaveis[idx] = qtd_aplicavel

    return pd.Series(brancos, index=vetor_escolha.index), pd.Series(aplicaveis, index=vetor_escolha.index)


def carregar_dados_participacao_ano(ano: int, diretorio_bruto: Path | None = None) -> pd.DataFrame:
    """Carrega e enriquece os registros de presença e participação no exame para um ano."""
    caminho_fonte = localizar_fonte_ano(ano, diretorio_bruto)
    fonte = FonteMicrodados(caminho_fonte, ano)
    try:
        arq1 = ler_tabela_filtrada(fonte, 1, COLUNAS_ARQ1)
        cursos = classificar_cursos_edicao(arq1, ano)

        colunas_arq3 = [
            "CO_CURSO",
            "TP_INSCRICAO",
            "PESO_AMOSTRA",
            *COLUNAS_PRESENCA,
            *COLUNAS_VETORES,
            *COLUNAS_DISCURSIVAS_PADRAO,
            *COLUNAS_NOTAS,
        ]
        arq3 = ler_tabela_filtrada(fonte, 3, colunas_arq3)
    finally:
        fonte.fechar()

    arq3 = arq3.loc[arq3["CO_CURSO"].isin(cursos.index)].copy()
    if ano in ANOS_AMOSTRAIS and "TP_INSCRICAO" in arq3.columns:
        arq3 = arq3.loc[arq3["TP_INSCRICAO"] == "0"].copy()

    arq3["ano"] = ano
    arq3["CO_IES"] = arq3["CO_CURSO"].map(cursos["CO_IES"])
    arq3["CO_UF_CURSO"] = arq3["CO_CURSO"].map(cursos["CO_UF_CURSO"])
    arq3["rede"] = arq3["CO_CURSO"].map(cursos["rede"])
    arq3["eh_unifor"] = arq3["CO_CURSO"].map(cursos["eh_unifor"]).astype(bool)
    arq3["eh_ceara_demais"] = arq3["CO_CURSO"].map(cursos["eh_ceara_demais"]).astype(bool)

    if "PESO_AMOSTRA" in arq3.columns:
        arq3["peso"] = pd.to_numeric(arq3["PESO_AMOSTRA"], errors="coerce").fillna(1.0)
    else:
        arq3["peso"] = 1.0

    for col_nota in COLUNAS_NOTAS:
        if col_nota in arq3.columns:
            arq3[col_nota] = pd.to_numeric(arq3[col_nota], errors="coerce")

    brancos_ofg, aplicaveis_ofg = contar_questoes_objetivas_em_branco(
        arq3["DS_VT_ESC_OFG"],
        arq3["DS_VT_ACE_OFG"],
        arq3.get("DS_VT_GAB_OFG_FIN"),
    )
    brancos_oce, aplicaveis_oce = contar_questoes_objetivas_em_branco(
        arq3["DS_VT_ESC_OCE"],
        arq3["DS_VT_ACE_OCE"],
        arq3.get("DS_VT_GAB_OCE_FIN"),
    )
    arq3["n_obj_fg_branco"] = brancos_ofg
    arq3["n_obj_fg_aplicaveis"] = aplicaveis_ofg
    arq3["n_obj_ce_branco"] = brancos_oce
    arq3["n_obj_ce_aplicaveis"] = aplicaveis_oce
    arq3["n_obj_total_branco"] = arq3["n_obj_fg_branco"] + arq3["n_obj_ce_branco"]
    arq3["n_obj_total_aplicaveis"] = arq3["n_obj_fg_aplicaveis"] + arq3["n_obj_ce_aplicaveis"]

    cols_disc_presentes = [c for c in COLUNAS_DISCURSIVAS_PADRAO if c in arq3.columns]
    if cols_disc_presentes:
        matriz_disc_branco = pd.DataFrame({c: arq3[c] == "333" for c in cols_disc_presentes})
        matriz_disc_valida = pd.DataFrame({c: arq3[c] == "555" for c in cols_disc_presentes})
        arq3["n_disc_branco_5q"] = matriz_disc_branco.sum(axis=1)
        arq3["n_disc_valida_5q"] = matriz_disc_valida.sum(axis=1)
    else:
        arq3["n_disc_branco_5q"] = 0
        arq3["n_disc_valida_5q"] = 0

    arq3["presente_valido"] = arq3["TP_PRES"] == "555"
    arq3["ausente"] = arq3["TP_PRES"].isin({"222", "444"})
    arq3["outros_presenca"] = ~(arq3["presente_valido"] | arq3["ausente"])

    arq3["prova_valida_geral"] = arq3["presente_valido"] & (arq3["TP_PR_GER"] == "555")
    arq3["prova_em_branco_geral"] = arq3["presente_valido"] & (arq3["TP_PR_GER"] == "333")

    arq3["obj_fg_em_branco"] = arq3["presente_valido"] & (arq3["TP_PR_OB_FG"] == "333")
    arq3["obj_ce_em_branco"] = arq3["presente_valido"] & (arq3["TP_PR_OB_CE"] == "333")
    arq3["dis_fg_em_branco"] = arq3["presente_valido"] & (arq3["TP_PR_DI_FG"] == "333")
    arq3["dis_ce_em_branco"] = arq3["presente_valido"] & (arq3["TP_PR_DI_CE"] == "333")
    arq3["alguma_discursiva_bloco_branco"] = arq3["dis_fg_em_branco"] | arq3["dis_ce_em_branco"]
    arq3["ambas_discursivas_bloco_branco"] = arq3["dis_fg_em_branco"] & arq3["dis_ce_em_branco"]

    arq3["alguma_obj_em_branco"] = arq3["presente_valido"] & (arq3["n_obj_total_branco"] > 0)

    if ano == 2005:
        arq3["alguma_disc_questao_branco"] = arq3["alguma_discursiva_bloco_branco"]
    else:
        arq3["alguma_disc_questao_branco"] = arq3["presente_valido"] & (
            (arq3["n_disc_branco_5q"] > 0) | arq3["alguma_discursiva_bloco_branco"]
        )

    alguma_questao_branco = arq3["alguma_obj_em_branco"] | arq3["alguma_disc_questao_branco"]
    arq3["prova_parcial"] = arq3["prova_valida_geral"] & alguma_questao_branco
    arq3["prova_completa"] = arq3["prova_valida_geral"] & ~alguma_questao_branco

    return arq3


def resumir_subconjunto(df: pd.DataFrame, ano: int, grupo: str) -> dict:
    """Calcula todas as métricas de presença, provas em branco e respostas parciais de um grupo agregado."""
    n_inscritos = len(df)
    n_presentes = int(df["presente_valido"].sum())
    n_ausentes = int(df["ausente"].sum())
    n_outros_pres = int(df["outros_presenca"].sum())

    presentes = df.loc[df["presente_valido"]]
    n_prova_valida = int(presentes["prova_valida_geral"].sum())
    n_prova_branco_geral = int(presentes["prova_em_branco_geral"].sum())

    n_obj_fg_branco = int(presentes["obj_fg_em_branco"].sum())
    n_obj_ce_branco = int(presentes["obj_ce_em_branco"].sum())
    n_dis_fg_branco = int(presentes["dis_fg_em_branco"].sum())
    n_dis_ce_branco = int(presentes["dis_ce_em_branco"].sum())
    n_alguma_dis_bloco_branco = int(presentes["alguma_discursiva_bloco_branco"].sum())
    n_ambas_dis_bloco_branco = int(presentes["ambas_discursivas_bloco_branco"].sum())

    n_alguma_obj_branco = int(presentes["alguma_obj_em_branco"].sum())
    n_alguma_disc_q_branco = int(presentes["alguma_disc_questao_branco"].sum())
    n_prova_parcial = int(presentes["prova_parcial"].sum())
    n_prova_completa = int(presentes["prova_completa"].sum())

    denom_insc = n_inscritos if n_inscritos > 0 else np.nan
    pct_presentes_insc = 100.0 * n_presentes / denom_insc
    pct_ausentes_insc = 100.0 * n_ausentes / denom_insc
    pct_outros_insc = 100.0 * n_outros_pres / denom_insc
    pct_participacao_valida_insc = 100.0 * n_prova_valida / denom_insc

    denom_pres = n_presentes if n_presentes > 0 else np.nan
    return {
        "ano": ano,
        "grupo": grupo,
        "n_cursos": int(df["CO_CURSO"].nunique()),
        "n_ies": int(df["CO_IES"].nunique()),
        "n_inscritos": n_inscritos,
        "n_presentes": n_presentes,
        "n_ausentes": n_ausentes,
        "n_outros_presenca": n_outros_pres,
        "pct_presentes_inscritos": round(pct_presentes_insc, 2),
        "pct_ausentes_inscritos": round(pct_ausentes_insc, 2),
        "pct_outros_inscritos": round(pct_outros_insc, 2),
        "n_participacao_valida": n_prova_valida,
        "pct_participacao_valida_inscritos": round(pct_participacao_valida_insc, 2),
        "pct_participacao_valida_presentes": round(100.0 * n_prova_valida / denom_pres, 2),
        "n_prova_branco_geral": n_prova_branco_geral,
        "pct_prova_branco_presentes": round(100.0 * n_prova_branco_geral / denom_pres, 2),
        "n_obj_fg_branco": n_obj_fg_branco,
        "pct_obj_fg_branco_presentes": round(100.0 * n_obj_fg_branco / denom_pres, 2),
        "n_obj_ce_branco": n_obj_ce_branco,
        "pct_obj_ce_branco_presentes": round(100.0 * n_obj_ce_branco / denom_pres, 2),
        "n_dis_fg_branco": n_dis_fg_branco,
        "pct_dis_fg_branco_presentes": round(100.0 * n_dis_fg_branco / denom_pres, 2),
        "n_dis_ce_branco": n_dis_ce_branco,
        "pct_dis_ce_branco_presentes": round(100.0 * n_dis_ce_branco / denom_pres, 2),
        "n_alguma_dis_bloco_branco": n_alguma_dis_bloco_branco,
        "pct_alguma_dis_bloco_branco_presentes": round(100.0 * n_alguma_dis_bloco_branco / denom_pres, 2),
        "n_ambas_dis_bloco_branco": n_ambas_dis_bloco_branco,
        "pct_ambas_dis_bloco_branco_presentes": round(100.0 * n_ambas_dis_bloco_branco / denom_pres, 2),
        "n_alguma_obj_questao_branco": n_alguma_obj_branco,
        "pct_alguma_obj_questao_branco_presentes": round(100.0 * n_alguma_obj_branco / denom_pres, 2),
        "n_alguma_disc_questao_branco": n_alguma_disc_q_branco,
        "pct_alguma_disc_questao_branco_presentes": round(100.0 * n_alguma_disc_q_branco / denom_pres, 2),
        "n_prova_parcial": n_prova_parcial,
        "pct_prova_parcial_presentes": round(100.0 * n_prova_parcial / denom_pres, 2),
        "n_prova_completa": n_prova_completa,
        "pct_prova_completa_presentes": round(100.0 * n_prova_completa / denom_pres, 2),
    }


def detalhar_componentes_por_grupo(dados_por_ano: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Detalha por caderno (Objetivas e Discursivas) o preenchimento completo, parcial e em branco nos 7 grupos."""
    linhas = []
    for ano in ANOS_RECENTES:
        df_ano = dados_por_ano[ano]
        for grupo in GRUPOS_AGREGADOS:
            sub = selecionar_grupo_agregado(df_ano, grupo)
            pres = sub.loc[sub["presente_valido"]]
            n_pres = len(pres)
            if n_pres == 0:
                continue

            obj_fg_branco = int((pres["TP_PR_OB_FG"] == "333").sum())
            obj_fg_parcial = int(((pres["TP_PR_OB_FG"] == "555") & (pres["n_obj_fg_branco"] > 0)).sum())
            obj_fg_comp = n_pres - obj_fg_branco - obj_fg_parcial

            obj_ce_branco = int((pres["TP_PR_OB_CE"] == "333").sum())
            obj_ce_parcial = int(((pres["TP_PR_OB_CE"] == "555") & (pres["n_obj_ce_branco"] > 0)).sum())
            obj_ce_comp = n_pres - obj_ce_branco - obj_ce_parcial

            dis_fg_qtd = (pres["TP_SFG_D1"] == "333").astype(int) + (pres["TP_SFG_D2"] == "333").astype(int)
            dis_fg_branco = int((pres["TP_PR_DI_FG"] == "333").sum())
            dis_fg_parcial = int(((pres["TP_PR_DI_FG"] == "555") & (dis_fg_qtd == 1)).sum())
            dis_fg_comp = n_pres - dis_fg_branco - dis_fg_parcial

            dis_ce_qtd = (
                (pres["TP_SCE_D1"] == "333").astype(int)
                + (pres["TP_SCE_D2"] == "333").astype(int)
                + (pres["TP_SCE_D3"] == "333").astype(int)
            )
            dis_ce_branco = int((pres["TP_PR_DI_CE"] == "333").sum())
            dis_ce_parcial = int(((pres["TP_PR_DI_CE"] == "555") & (dis_ce_qtd.isin([1, 2]))).sum())
            dis_ce_comp = n_pres - dis_ce_branco - dis_ce_parcial

            for comp_nome, comp, parc, branc in [
                ("Objetiva de Formação Geral (8 questões)", obj_fg_comp, obj_fg_parcial, obj_fg_branco),
                ("Objetiva Específica de Computação (27 questões)", obj_ce_comp, obj_ce_parcial, obj_ce_branco),
                ("Discursiva de Formação Geral (2 questões)", dis_fg_comp, dis_fg_parcial, dis_fg_branco),
                ("Discursiva Específica de Computação (3 questões)", dis_ce_comp, dis_ce_parcial, dis_ce_branco),
            ]:
                linhas.append(
                    {
                        "ano": ano,
                        "grupo": grupo,
                        "componente": comp_nome,
                        "n_presentes": n_pres,
                        "n_completo": comp,
                        "pct_completo": round(100.0 * comp / n_pres, 2),
                        "n_parcial": parc,
                        "pct_parcial": round(100.0 * parc / n_pres, 2),
                        "n_em_branco": branc,
                        "pct_em_branco": round(100.0 * branc / n_pres, 2),
                    }
                )
    return pd.DataFrame(linhas)


def v_de_cramer(tabela_2x2: np.ndarray, qui_quadrado: float) -> float:
    """Calcula o V de Cramér para uma tabela 2x2."""
    total = tabela_2x2.sum()
    return float(np.sqrt(qui_quadrado / total)) if total > 0 else 0.0


def corrigir_holm(valores_p: pd.Series) -> pd.Series:
    """Ajusta uma série de valores-p pelo método sequencial de Holm-Bonferroni."""
    ordem = valores_p.sort_values().index
    quantidade = len(valores_p)
    ajustados = (valores_p.loc[ordem] * np.arange(quantidade, 0, -1)).cummax().clip(upper=1.0)
    return ajustados.reindex(valores_p.index)


def executar_testes_comparacao(dados_por_ano: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Compara a Unifor com os 6 grupos agregados (CE e Brasil: públicas, privadas e geral) em 2017 e 2021."""
    grupos_referencia = [g for g in GRUPOS_AGREGADOS if g != "Unifor"]

    indicadores = [
        ("Presença no exame (entre inscritos)", "todos", "presente_valido"),
        ("Discursiva de Formação Geral em branco (entre presentes)", "presentes", "dis_fg_em_branco"),
        ("Discursiva Específica em branco (entre presentes)", "presentes", "dis_ce_em_branco"),
        ("Algum caderno discursivo em branco (entre presentes)", "presentes", "alguma_discursiva_bloco_branco"),
        ("Prova parcial ou em branco (entre presentes)", "presentes", "nao_completa"),
    ]

    linhas = []
    for ano in ANOS_RECENTES:
        df = dados_por_ano[ano].copy()
        df["nao_completa"] = ~df["prova_completa"]
        unifor_todos = selecionar_grupo_agregado(df, "Unifor")
        unifor_pres = unifor_todos.loc[unifor_todos["presente_valido"]]

        for nome_comp in grupos_referencia:
            outro_todos = selecionar_grupo_agregado(df, nome_comp)
            outro_pres = outro_todos.loc[outro_todos["presente_valido"]]

            for rotulo_ind, base_tipo, coluna_bool in indicadores:
                u_base = unifor_todos if base_tipo == "todos" else unifor_pres
                o_base = outro_todos if base_tipo == "todos" else outro_pres

                u_sim = int(u_base[coluna_bool].sum())
                u_nao = len(u_base) - u_sim
                o_sim = int(o_base[coluna_bool].sum())
                o_nao = len(o_base) - o_sim

                contingencia = np.array([[u_sim, u_nao], [o_sim, o_nao]])
                qui2, _, _, esperados = stats.chi2_contingency(contingencia, correction=False)
                _, valor_p_fisher = stats.fisher_exact(contingencia)
                efeito = v_de_cramer(contingencia, float(qui2))

                pct_u = 100.0 * u_sim / len(u_base) if len(u_base) > 0 else np.nan
                pct_o = 100.0 * o_sim / len(o_base) if len(o_base) > 0 else np.nan

                linhas.append(
                    {
                        "ano": ano,
                        "indicador": rotulo_ind,
                        "comparacao": f"Unifor x {nome_comp}",
                        "teste": "Exato de Fisher",
                        "n_unifor": len(u_base),
                        "ocorrencias_unifor": u_sim,
                        "pct_unifor": round(pct_u, 2),
                        "n_grupo": len(o_base),
                        "ocorrencias_grupo": o_sim,
                        "pct_grupo": round(pct_o, 2),
                        "diferenca_pp": round(pct_u - pct_o, 2),
                        "qui_quadrado": round(float(qui2), 4),
                        "valor_p": round(float(valor_p_fisher), 6),
                        "v_cramer": round(efeito, 3),
                        "menor_esperado": round(float(esperados.min()), 2),
                    }
                )

    tabela_testes = pd.DataFrame(linhas)
    tabela_testes["valor_p_holm"] = (
        tabela_testes.groupby("ano")["valor_p"].transform(corrigir_holm).round(6)
    )
    tabela_testes["significativo_holm_5pct"] = tabela_testes["valor_p_holm"] < NIVEL_SIGNIFICANCIA
    return tabela_testes


def calcular_impacto_notas_grupos(dados_por_ano: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Compara as notas médias segundo o preenchimento das discursivas nos grupos do Ceará (Unifor excluída de privadas e geral)."""
    linhas = []
    for ano in ANOS_COMPARACAO_GRUPOS:
        df_ano = dados_por_ano[ano]
        for grupo in GRUPOS_CEARA:
            sub_grupo = selecionar_grupo_agregado(df_ano, grupo)
            pres = sub_grupo.loc[sub_grupo["presente_valido"]].copy()
            if pres.empty:
                continue

            for rotulo, mascara in [
                ("Respondeu aos dois cadernos discursivos", ~pres["alguma_discursiva_bloco_branco"]),
                ("Deixou ao menos um caderno discursivo em branco", pres["alguma_discursiva_bloco_branco"]),
                ("Todos os presentes com nota válida", pd.Series(True, index=pres.index)),
            ]:
                sub = pres.loc[mascara]
                if sub.empty or sub["NT_GER"].dropna().empty:
                    continue
                pesos = sub["peso"].to_numpy(dtype=float)
                v_ger = sub["NT_GER"].notna()
                v_fg = sub["NT_FG"].notna()
                v_ce = sub["NT_CE"].notna()
                linhas.append(
                    {
                        "ano": ano,
                        "grupo": grupo,
                        "situacao_discursiva": rotulo,
                        "n_estudantes": len(sub),
                        "media_nt_ger": round(float(np.average(sub.loc[v_ger, "NT_GER"], weights=pesos[v_ger])), 2),
                        "mediana_nt_ger": round(float(sub["NT_GER"].median()), 2),
                        "media_nt_formacao_geral": round(float(np.average(sub.loc[v_fg, "NT_FG"], weights=pesos[v_fg])), 2),
                        "media_nt_especifica": round(float(np.average(sub.loc[v_ce, "NT_CE"], weights=pesos[v_ce])), 2),
                    }
                )
    return pd.DataFrame(linhas)


def gerar_grafico_barras_7grupos(
    tabela_percentuais: pd.DataFrame,
    titulo: str,
    rotulo_y: str,
    nome_arquivo: str,
    rotacao_x: int = 0,
) -> None:
    """Gera gráfico de barras agrupadas para os 7 grupos agregados (Unifor, CE púb/priv/geral, BR púb/priv/geral)."""
    if plt is None:
        return
    figura, eixo = plt.subplots(figsize=(11.8, 5.3))
    tabela_percentuais[GRUPOS_AGREGADOS].plot.bar(ax=eixo, color=CORES_7_GRUPOS, width=0.82)
    eixo.set(title=titulo, xlabel="", ylabel=rotulo_y)
    eixo.tick_params(axis="x", rotation=rotacao_x)
    eixo.legend(title="", ncol=2, fontsize=8.5)
    figura.tight_layout()
    figura.savefig(DIRETORIO_SAIDA / nome_arquivo, dpi=160)
    plt.close(figura)


def gerar_graficos(
    resumo_grupos: pd.DataFrame,
    detalhe_componentes: pd.DataFrame,
    impacto_notas: pd.DataFrame,
) -> None:
    """Gera as visualizações comparativas (com Brasil em presença/comparação/discursivas e foco no Ceará nas demais)."""
    if plt is None:
        print("Matplotlib não disponível; gráficos não foram gerados.", file=sys.stderr)
        return

    # 1. Presença e Comparação geral nos 7 grupos (Ceará + Brasil) em 2017 e 2021
    for ano in ANOS_RECENTES:
        recorte = (
            resumo_grupos.loc[resumo_grupos["ano"] == ano]
            .set_index("grupo")
            .reindex(GRUPOS_AGREGADOS)
        )

        # 1a. Situação de presença (Presentes vs Ausentes) nos 7 grupos
        dist_presenca = pd.DataFrame(
            {
                g: [
                    float(recorte.loc[g, "pct_presentes_inscritos"]),
                    float(recorte.loc[g, "pct_ausentes_inscritos"]),
                ]
                for g in GRUPOS_AGREGADOS
            },
            index=["Presente com resultado válido", "Ausente"],
        )
        gerar_grafico_barras_7grupos(
            dist_presenca,
            f"Situação de presença dos concluintes por rede e recorte geográfico ({ano})",
            "% dos inscritos",
            f"situacao_presenca_{ano}.png",
            rotacao_x=0,
        )

        # 1b. Preenchimento da prova e cadernos discursivos em branco nos 7 grupos (sem siglas FG/CE da prova)
        dist_engajamento = pd.DataFrame(
            {
                g: [
                    float(recorte.loc[g, "pct_prova_completa_presentes"]),
                    float(recorte.loc[g, "pct_prova_parcial_presentes"]),
                    float(recorte.loc[g, "pct_dis_fg_branco_presentes"]),
                    float(recorte.loc[g, "pct_dis_ce_branco_presentes"]),
                    float(recorte.loc[g, "pct_alguma_dis_bloco_branco_presentes"]),
                ]
                for g in GRUPOS_AGREGADOS
            },
            index=[
                "Prova 100%\nrespondida",
                "Prova\nparcial",
                "Discursiva Formação Geral\ntoda em branco",
                "Discursiva Específica\ntoda em branco",
                "Algum caderno discursivo\ntodo em branco",
            ],
        )
        gerar_grafico_barras_7grupos(
            dist_engajamento,
            f"Grau de preenchimento da prova e discursivas em branco entre os presentes ({ano})",
            "% dos presentes",
            f"participacao_comparacao_grupos_{ano}.png",
            rotacao_x=0,
        )

    # 2. Evolução histórica comparativa (2008–2021) focada apenas no Ceará: Unifor vs CE (públicas, privadas e geral)
    anos_comp = sorted(resumo_grupos["ano"].unique())
    estilos_evolucao_ce = [
        ("Unifor", "#197a78", "-", "o", 2.5),
        ("CE públicas", "#5c4d9a", "--", "s", 2.0),
        ("CE privadas", "#d9822b", "--", "^", 2.0),
        ("CE geral", "#8c6bb1", "-", "D", 2.1),
    ]
    figura, eixos = plt.subplots(1, 2, figsize=(13, 5.2))
    for grupo, cor, estilo_linha, marcador, espessura in estilos_evolucao_ce:
        sub = resumo_grupos.loc[resumo_grupos["grupo"] == grupo].set_index("ano").reindex(anos_comp)
        eixos[0].plot(
            anos_comp,
            sub["pct_presentes_inscritos"],
            label=grupo,
            color=cor,
            linestyle=estilo_linha,
            marker=marcador,
            linewidth=espessura,
        )
        eixos[1].plot(
            anos_comp,
            sub["pct_alguma_dis_bloco_branco_presentes"],
            label=grupo,
            color=cor,
            linestyle=estilo_linha,
            marker=marcador,
            linewidth=espessura,
        )

    eixos[0].set(
        title="Evolução da taxa de presença (2008–2021)",
        xlabel="Edição ENADE",
        ylabel="% dos inscritos presentes",
        ylim=(55, 100),
    )
    eixos[0].set_xticks(anos_comp)

    eixos[1].set(
        title="Evolução de cadernos discursivos em branco (2008–2021)",
        xlabel="Edição ENADE",
        ylabel="% dos presentes com ≥ 1 caderno discursivo em branco",
        ylim=(0, 70),
    )
    eixos[1].set_xticks(anos_comp)

    handles, rotulos_leg = eixos[0].get_legend_handles_labels()
    figura.legend(handles, rotulos_leg, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.04), fontsize=9.5)
    figura.suptitle("Evolução comparativa no Ceará: Unifor vs. CE públicas, CE privadas e CE geral", fontsize=11.5, y=0.98)
    figura.tight_layout(rect=(0, 0.05, 1, 0.93))
    figura.savefig(DIRETORIO_SAIDA / "participacao_evolucao_comparativa.png", dpi=160, bbox_inches="tight")
    plt.close(figura)

    # 3. Comparação do preenchimento dos cadernos discursivos nos 7 grupos (Ceará + Brasil) em 2021
    det_2021 = detalhe_componentes.loc[detalhe_componentes["ano"] == 2021]
    if not det_2021.empty:
        figura, eixos = plt.subplots(1, 2, figsize=(13.2, 5.4), sharey=True)
        cadernos_foco = [
            "Discursiva de Formação Geral (2 questões)",
            "Discursiva Específica de Computação (3 questões)",
        ]
        pos = np.arange(len(GRUPOS_AGREGADOS))[::-1]
        for idx, caderno in enumerate(cadernos_foco):
            parte = (
                det_2021.loc[det_2021["componente"] == caderno]
                .set_index("grupo")
                .reindex(GRUPOS_AGREGADOS)
            )
            comp = parte["pct_completo"].to_numpy()
            parc = parte["pct_parcial"].to_numpy()
            branc = parte["pct_em_branco"].to_numpy()

            eixos[idx].barh(pos, comp, color="#197a78", label="Todas respondidas")
            eixos[idx].barh(pos, parc, left=comp, color="#d9822b", label="Respondida parcialmente")
            eixos[idx].barh(pos, branc, left=comp + parc, color="#c62828", label="Caderno inteiro em branco")
            eixos[idx].set_yticks(pos)
            if idx == 0:
                eixos[idx].set_yticklabels(GRUPOS_AGREGADOS, fontsize=9.5)
            eixos[idx].set_xlim(0, 102)
            eixos[idx].set_xlabel("% dos presentes")
            eixos[idx].set_title(caderno, fontsize=10.5)

        handles, rotulos_leg = eixos[0].get_legend_handles_labels()
        figura.legend(handles, rotulos_leg, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04), fontsize=9.5)
        figura.suptitle(
            "Preenchimento dos cadernos discursivos por grupo de comparação (ENADE 2021)",
            fontsize=11.5,
            y=0.98,
        )
        figura.tight_layout(rect=(0, 0.05, 1, 0.92))
        figura.savefig(DIRETORIO_SAIDA / "participacao_preenchimento_discursivas_2021.png", dpi=160, bbox_inches="tight")
        plt.close(figura)

    # 4. Impacto de deixar discursivas em branco na nota geral (NT_GER) focado apenas no Ceará em 2021
    imp_2021 = impacto_notas.loc[impacto_notas["ano"] == 2021]
    if not imp_2021.empty:
        piv = (
            imp_2021.pivot(index="grupo", columns="situacao_discursiva", values="media_nt_ger")
            .reindex(GRUPOS_CEARA)
        )
        colunas_ordem = [
            "Respondeu aos dois cadernos discursivos",
            "Todos os presentes com nota válida",
            "Deixou ao menos um caderno discursivo em branco",
        ]
        piv = piv.reindex(columns=colunas_ordem)
        figura, eixo = plt.subplots(figsize=(10.2, 5.0))
        piv.plot.bar(ax=eixo, color=["#197a78", "#9a9a9a", "#c62828"], width=0.76)
        eixo.set(
            title="Nota geral média (NT_GER) segundo o preenchimento das discursivas no Ceará (ENADE 2021)",
            xlabel="",
            ylabel="Nota geral média (NT_GER)",
        )
        eixo.tick_params(axis="x", rotation=0)
        eixo.legend(title="")
        figura.tight_layout()
        figura.savefig(DIRETORIO_SAIDA / "participacao_impacto_notas_grupos_2021.png", dpi=160)
        plt.close(figura)


def executar_analise(diretorio_bruto: Path | None = None) -> None:
    """Executa toda a análise da seção 5.5, salva CSVs e gera gráficos."""
    DIRETORIO_SAIDA.mkdir(parents=True, exist_ok=True)

    dados_por_ano: dict[int, pd.DataFrame] = {}
    for ano in ANOS_HISTORICO_UNIFOR:
        dados_por_ano[ano] = carregar_dados_participacao_ano(ano, diretorio_bruto)

    # 1. Histórico da Unifor (2005–2021)
    linhas_unifor = [
        resumir_subconjunto(selecionar_grupo_agregado(dados_por_ano[ano], "Unifor"), ano, "Unifor")
        for ano in ANOS_HISTORICO_UNIFOR
    ]
    historico_unifor = pd.DataFrame(linhas_unifor)
    historico_unifor.to_csv(DIRETORIO_SAIDA / "participacao_historico_unifor.csv", index=False)

    # 2. Resumo comparativo para os 7 grupos agregados (2008–2021)
    linhas_grupos = []
    for ano in ANOS_COMPARACAO_GRUPOS:
        df_ano = dados_por_ano[ano]
        for grupo in GRUPOS_AGREGADOS:
            linhas_grupos.append(resumir_subconjunto(selecionar_grupo_agregado(df_ano, grupo), ano, grupo))
    resumo_grupos = pd.DataFrame(linhas_grupos)
    resumo_grupos.to_csv(DIRETORIO_SAIDA / "participacao_resumo_grupos.csv", index=False)

    # 3. Detalhe de preenchimento completo/parcial/branco por caderno nos 7 grupos (2017 e 2021)
    detalhe_componentes = detalhar_componentes_por_grupo(dados_por_ano)
    detalhe_componentes.to_csv(DIRETORIO_SAIDA / "participacao_detalhe_componentes_grupos.csv", index=False)

    # 4. Testes estatísticos da Unifor contra os 6 grupos de referência (2017 e 2021)
    testes_comparacao = executar_testes_comparacao(dados_por_ano)
    testes_comparacao.to_csv(DIRETORIO_SAIDA / "participacao_testes_comparacao.csv", index=False)

    # 5. Impacto nas notas segundo o preenchimento das discursivas nos 7 grupos (2008–2021)
    impacto_notas = calcular_impacto_notas_grupos(dados_por_ano)
    impacto_notas.to_csv(DIRETORIO_SAIDA / "participacao_impacto_notas_grupos.csv", index=False)

    # 6. Gráficos
    gerar_graficos(resumo_grupos, detalhe_componentes, impacto_notas)

    cols_grp = [
        "ano",
        "grupo",
        "n_cursos",
        "n_ies",
        "n_inscritos",
        "n_presentes",
        "pct_presentes_inscritos",
        "pct_dis_fg_branco_presentes",
        "pct_dis_ce_branco_presentes",
        "pct_alguma_dis_bloco_branco_presentes",
        "pct_prova_parcial_presentes",
        "pct_prova_completa_presentes",
    ]
    print("=== Comparação entre os 7 grupos agregados (2017 e 2021) ===")
    print(resumo_grupos.loc[resumo_grupos["ano"].isin(ANOS_RECENTES), cols_grp].to_string(index=False))

    print("\n=== Testes estatísticos (Unifor vs. 6 grupos agregados em 2017 e 2021) ===")
    cols_testes = [
        "ano",
        "indicador",
        "comparacao",
        "pct_unifor",
        "pct_grupo",
        "diferenca_pp",
        "valor_p",
        "valor_p_holm",
        "v_cramer",
    ]
    print(testes_comparacao[cols_testes].to_string(index=False))

    print("\n=== Impacto do preenchimento das discursivas na nota geral (2021) ===")
    print(impacto_notas.loc[impacto_notas["ano"] == 2021].to_string(index=False))
    print(f"\nArquivos e gráficos salvos em: {DIRETORIO_SAIDA}")


def principal(argumentos: Iterable[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(
        description="Analisa a participação e a entrega de provas/questões em branco no ENADE (seção 5.5)."
    )
    analisador.add_argument(
        "--bruto",
        type=Path,
        default=None,
        help="Pasta onde estão os microdados brutos (padrão: data/raw ou ../raw).",
    )
    opcoes = analisador.parse_args(list(argumentos) if argumentos is not None else None)
    try:
        executar_analise(opcoes.bruto)
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
