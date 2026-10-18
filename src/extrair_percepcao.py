from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import BinaryIO, Iterable

import pandas as pd

from perfil import (
    CODIGO_GRUPO,
    DIRETORIO_DADOS_BRUTOS,
    DIRETORIO_RAIZ,
    mapear_grupos_curso,
)

DIRETORIO_SAIDA_PADRAO = DIRETORIO_RAIZ / "data" / "processed" / "percepcao"
NOME_PACOTE = "entrega_percepcao.zip"
ANOS_PADRAO = [2017, 2021]

# Bloco do Questionário do Estudante sobre o processo formativo (plano de trabalho, seção 6).
# Nos dicionários de 2017 e 2021 essas 42 questões ficam juntas no arquivo arq4.
QE_INICIO = 27
QE_FIM = 68

PADRAO_QUESTAO = re.compile(r"^QE_I(\d+)$")
EXTENSOES_DOCUMENTACAO = {".pdf", ".xlsx", ".xls", ".ods", ".docx", ".doc"}
LIMITE_DOCUMENTO_BYTES = 30 * 1024 * 1024
RESPOSTA_EM_BRANCO = "(em branco)"
TAMANHO_BLOCO = 100_000  # linhas lidas por vez, para não carregar o arquivo inteiro na memória
COLUNAS_CONTAGEM = ["ano", "questao", "CO_CURSO", "CO_IES", "CO_UF_CURSO", "CO_CATEGAD", "grupo", "resposta", "n"]


def padrao_arquivo_dados(ano: int) -> re.Pattern[str]:
    """Expressão que reconhece microdados{ano}_arqN.txt e captura o número N."""
    return re.compile(rf"(?:^|/)microdados{ano}_arq(\d+)\.txt$", re.IGNORECASE)


class FonteMicrodados:
    """Acesso único aos arquivos do INEP de uma edição, em um ZIP ou em uma pasta já extraída."""

    def __init__(self, caminho: Path, ano: int) -> None:
        self.caminho = caminho
        self.ano = ano
        self.padrao = padrao_arquivo_dados(ano)
        self.zip: zipfile.ZipFile | None = None
        if caminho.is_dir():
            arquivos = sorted((p for p in caminho.rglob("*") if p.is_file()), key=lambda p: p.as_posix())
            self._itens = {p.relative_to(caminho).as_posix(): p for p in arquivos}
            self._tamanhos = {nome: p.stat().st_size for nome, p in self._itens.items()}
        elif caminho.is_file():
            self.zip = zipfile.ZipFile(caminho)
            informacoes = [i for i in self.zip.infolist() if not i.is_dir()]
            self._itens = {i.filename: i for i in informacoes}
            self._tamanhos = {i.filename: i.file_size for i in informacoes}
        else:
            raise FileNotFoundError(f"Fonte de microdados não encontrada: {caminho}")

    def fechar(self) -> None:
        if self.zip is not None:
            self.zip.close()

    def nomes(self) -> list[str]:
        """Caminhos relativos de todos os arquivos da fonte."""
        return list(self._itens)

    def tamanho(self, nome: str) -> int:
        return self._tamanhos[nome]

    def abrir(self, nome: str) -> BinaryIO:
        """Abre um arquivo da fonte para leitura binária."""
        item = self._itens[nome]
        return self.zip.open(item) if self.zip is not None else item.open("rb")

    def ler_bytes(self, nome: str) -> bytes:
        with self.abrir(nome) as objeto_arquivo:
            return objeto_arquivo.read()


def localizar_fonte(diretorio_bruto: Path, ano: int) -> Path:
    """Procura o ZIP ou a pasta (ex.: microdados_Enade_2021_LGPD) da edição em data/raw."""
    prefixo = f"microdados_enade_{ano}"
    bases = [diretorio_bruto]
    if diretorio_bruto.is_dir():
        bases += sorted(p for p in diretorio_bruto.iterdir() if p.is_dir() and not p.name.lower().startswith(prefixo))
    candidatas: list[Path] = []
    for base in bases:
        if not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            if item.name.lower().startswith(prefixo) and (item.is_dir() or item.suffix.lower() == ".zip"):
                candidatas.append(item)
    escolhidas = [c for c in candidatas if c.is_dir()] or [c for c in candidatas if c.is_file()]
    if len(escolhidas) > 1:
        raise ValueError(
            f"Mais de uma fonte encontrada para {ano}: {', '.join(str(c) for c in escolhidas)}. "
            "Deixe só uma ou aponte a pasta correta com --bruto."
        )
    if not escolhidas:
        raise FileNotFoundError(
            f"Não achei a pasta nem o ZIP de {ano} (microdados_enade_{ano}*) em {diretorio_bruto}. "
            "Informe onde estão as pastas com --bruto."
        )
    return escolhidas[0]


def normalizar_coluna(nome: str) -> str:
    """Remove espaços e aspas do nome de uma coluna."""
    return nome.strip().replace('"', "")


def limpar_codigo(serie: pd.Series) -> pd.Series:
    """Padroniza códigos textuais, removendo espaços e aspas excedentes."""
    return serie.astype("string").str.strip().str.replace('"', "", regex=False)


def listar_arquivos_dados(fonte: FonteMicrodados) -> dict[int, str]:
    """Mapeia o número de cada arquivo de microdados (arqN) ao seu caminho na fonte."""
    arquivos: dict[int, str] = {}
    for nome in fonte.nomes():
        correspondencia = fonte.padrao.search(nome)
        if correspondencia:
            arquivos[int(correspondencia.group(1))] = nome
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo microdados{fonte.ano}_arqN.txt encontrado em {fonte.caminho}.")
    return arquivos


def ler_cabecalho(fonte: FonteMicrodados, membro: str) -> list[str]:
    """Lê só a linha de cabeçalho de um arquivo de microdados."""
    with fonte.abrir(membro) as objeto_arquivo:
        cabecalho = pd.read_csv(objeto_arquivo, sep=";", nrows=0, encoding="latin-1")
    return [normalizar_coluna(coluna) for coluna in cabecalho.columns]


def ler_identificacao(fonte: FonteMicrodados, arquivos: dict[int, str]) -> pd.DataFrame:
    """Lê a tabela de identificação dos cursos (arq1), com colunas e códigos limpos."""
    if 1 not in arquivos:
        raise FileNotFoundError(f"Arquivo microdados{fonte.ano}_arq1.txt (identificação) não encontrado em {fonte.caminho}.")
    with fonte.abrir(arquivos[1]) as objeto_arquivo:
        tabela = pd.read_csv(objeto_arquivo, sep=";", dtype="string", encoding="latin-1", low_memory=False)
    tabela.columns = [normalizar_coluna(coluna) for coluna in tabela.columns]
    for coluna in tabela.columns:
        tabela[coluna] = limpar_codigo(tabela[coluna])
    return tabela


def localizar_questoes(fonte: FonteMicrodados, arquivos: dict[int, str], inicio: int, fim: int) -> pd.DataFrame:
    """Descobre em qual arquivo está cada questão QE_I do intervalo, lendo os cabeçalhos."""
    linhas = []
    for numero_arquivo, membro in sorted(arquivos.items()):
        for coluna in ler_cabecalho(fonte, membro):
            correspondencia = PADRAO_QUESTAO.match(coluna)
            if correspondencia and inicio <= int(correspondencia.group(1)) <= fim:
                linhas.append(
                    {
                        "ano": fonte.ano,
                        "questao": coluna,
                        "numero_questao": int(correspondencia.group(1)),
                        "arquivo": numero_arquivo,
                        "membro": membro,
                    }
                )
    questoes = pd.DataFrame(linhas, columns=["ano", "questao", "numero_questao", "arquivo", "membro"])
    if questoes.empty:
        raise ValueError(f"Nenhuma coluna QE_I{inicio} a QE_I{fim} foi encontrada nos arquivos de {fonte.caminho}.")
    duplicadas = questoes.loc[questoes["questao"].duplicated(keep=False), "questao"].unique()
    if len(duplicadas):
        raise ValueError(f"Questões presentes em mais de um arquivo: {', '.join(sorted(duplicadas))}.")
    return questoes.sort_values("numero_questao", ignore_index=True)


def montar_cursos(identificacao: pd.DataFrame) -> pd.DataFrame:
    """Lista os cursos de Ciência da Computação com instituição, UF, categoria e grupo de comparação."""
    grupos = mapear_grupos_curso(identificacao)
    cursos = (
        identificacao.loc[identificacao["CO_GRUPO"] == CODIGO_GRUPO]
        .drop_duplicates("CO_CURSO")
        .set_index("CO_CURSO")[["CO_IES", "CO_UF_CURSO", "CO_CATEGAD"]]
        .copy()
    )
    cursos["grupo"] = grupos.reindex(cursos.index).fillna("Outros estados")
    return cursos


def contar_respostas(fonte: FonteMicrodados, membro: str, questoes: list[str], cursos: pd.DataFrame) -> pd.DataFrame:
    """Conta as respostas das questões de um arquivo por curso, lendo o arquivo uma única vez e em blocos."""
    colunas_usadas = {"CO_CURSO", *questoes}
    blocos = []
    with fonte.abrir(membro) as objeto_arquivo:
        leitor = pd.read_csv(
            objeto_arquivo,
            sep=";",
            dtype="string",
            encoding="latin-1",
            usecols=lambda coluna: normalizar_coluna(coluna) in colunas_usadas,
            chunksize=TAMANHO_BLOCO,
        )
        for bloco in leitor:
            bloco.columns = [normalizar_coluna(coluna) for coluna in bloco.columns]
            bloco["CO_CURSO"] = limpar_codigo(bloco["CO_CURSO"])
            bloco = bloco.loc[bloco["CO_CURSO"].isin(cursos.index)]
            if not bloco.empty:
                blocos.append(bloco)
    if not blocos:
        return pd.DataFrame(columns=["questao", "CO_CURSO", "resposta", "n"])
    tabela = pd.concat(blocos, ignore_index=True)
    longa = tabela.melt(id_vars="CO_CURSO", value_vars=questoes, var_name="questao", value_name="resposta")
    respostas = limpar_codigo(longa["resposta"]).fillna("")
    longa["resposta"] = respostas.where(respostas != "", RESPOSTA_EM_BRANCO)
    return longa.groupby(["questao", "CO_CURSO", "resposta"]).size().rename("n").reset_index()


def extrair_documentacao(fonte: FonteMicrodados, diretorio: Path) -> list[Path]:
    """Copia dicionários e questionários (PDF, planilhas) da fonte para uma pasta, ignorando os microdados."""
    diretorio.mkdir(parents=True, exist_ok=True)
    copiados = []
    for nome in fonte.nomes():
        if fonte.padrao.search(nome):
            continue
        extensao = Path(nome).suffix.lower()
        if extensao not in EXTENSOES_DOCUMENTACAO or fonte.tamanho(nome) > LIMITE_DOCUMENTO_BYTES:
            continue
        # Só o nome do arquivo é usado no destino, para nunca escrever fora da pasta de saída.
        destino = diretorio / Path(nome).name
        contador = 1
        while destino.exists():
            destino = diretorio / f"{Path(nome).stem}_{contador}{extensao}"
            contador += 1
        destino.write_bytes(fonte.ler_bytes(nome))
        copiados.append(destino)
    return copiados


def extrair_ano(ano: int, diretorio_bruto: Path, diretorio_saida: Path, inicio: int, fim: int) -> dict:
    """Extrai as contagens de respostas e a documentação de uma edição."""
    caminho = localizar_fonte(diretorio_bruto, ano)
    print(f"\nENADE {ano}: fonte {caminho}")
    fonte = FonteMicrodados(caminho, ano)
    try:
        arquivos = listar_arquivos_dados(fonte)
        cursos = montar_cursos(ler_identificacao(fonte, arquivos))
        questoes = localizar_questoes(fonte, arquivos, inicio, fim)

        contagens = []
        for membro, grupo_questoes in questoes.groupby("membro"):
            lista = list(grupo_questoes["questao"])
            contagens.append(contar_respostas(fonte, membro, lista, cursos))
            print(f"  {len(lista)} questões lidas de {Path(membro).name}")
        contagens = pd.concat(contagens, ignore_index=True).join(cursos, on="CO_CURSO")
        contagens.insert(0, "ano", ano)

        tabela_arquivos = pd.DataFrame(
            [(ano, nome, fonte.tamanho(nome)) for nome in fonte.nomes()],
            columns=["ano", "arquivo_na_fonte", "tamanho_bytes"],
        )
        documentos = extrair_documentacao(fonte, diretorio_saida / "documentacao" / str(ano))
    finally:
        fonte.fechar()
    return {
        "ano": ano,
        "cursos": cursos,
        "questoes": questoes.drop(columns="membro"),
        "contagens": contagens[COLUNAS_CONTAGEM],
        "arquivos": tabela_arquivos,
        "documentos": documentos,
    }


def empacotar_entrega(diretorio_saida: Path, arquivos: list[Path]) -> Path:
    """Reúne os arquivos gerados em um único ZIP pequeno, fácil de anexar."""
    caminho_pacote = diretorio_saida / NOME_PACOTE
    with zipfile.ZipFile(caminho_pacote, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
        for arquivo in arquivos:
            pacote.write(arquivo, arcname=arquivo.relative_to(diretorio_saida).as_posix())
    return caminho_pacote


def imprimir_resumo(resultado: dict, inicio: int, fim: int) -> None:
    """Mostra no terminal o que foi encontrado em uma edição, para conferência rápida."""
    ano = resultado["ano"]
    cursos, questoes, contagens = resultado["cursos"], resultado["questoes"], resultado["contagens"]
    esperadas = set(range(inicio, fim + 1))
    ausentes = sorted(esperadas - set(questoes["numero_questao"]))
    respondentes_unifor = (
        contagens.loc[(contagens["grupo"] == "Unifor") & (contagens["resposta"] != RESPOSTA_EM_BRANCO)]
        .groupby("questao")["n"]
        .sum()
    )
    arquivos_das_questoes = ", ".join(f"arq{numero}" for numero in sorted(questoes["arquivo"].unique()))
    print(f"\n=== ENADE {ano} ===")
    print("Cursos de Ciência da Computação por grupo: " + ", ".join(f"{g}={n}" for g, n in cursos["grupo"].value_counts().items()))
    print(f"Questões encontradas: {len(questoes)} de {len(esperadas)} (em {arquivos_das_questoes})")
    if ausentes:
        print("Questões ausentes (confira o dicionário): " + ", ".join(f"QE_I{numero}" for numero in ausentes))
    if not respondentes_unifor.empty:
        print(f"Respondentes da Unifor por questão: mínimo {int(respondentes_unifor.min())}, máximo {int(respondentes_unifor.max())}")
    print(f"Documentos copiados: {len(resultado['documentos'])}")


def executar_extracao(anos: list[int], diretorio_bruto: Path, diretorio_saida: Path, inicio: int, fim: int) -> None:
    """Extrai as respostas do bloco de percepção para um CSV agregado por curso, com todas as edições pedidas."""
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    resultados = [extrair_ano(ano, diretorio_bruto, diretorio_saida, inicio, fim) for ano in anos]

    caminho_contagens = diretorio_saida / "percepcao_contagens_por_curso.csv"
    caminho_mapa = diretorio_saida / "mapa_questoes_arquivos.csv"
    caminho_lista = diretorio_saida / "lista_arquivos_fonte.csv"
    pd.concat([r["contagens"] for r in resultados], ignore_index=True).to_csv(caminho_contagens, index=False)
    pd.concat([r["questoes"] for r in resultados], ignore_index=True).to_csv(caminho_mapa, index=False)
    pd.concat([r["arquivos"] for r in resultados], ignore_index=True).to_csv(caminho_lista, index=False)
    documentos = [documento for r in resultados for documento in r["documentos"]]
    caminho_pacote = empacotar_entrega(diretorio_saida, [caminho_contagens, caminho_mapa, caminho_lista, *documentos])

    for resultado in resultados:
        imprimir_resumo(resultado, inicio, fim)
    print(f"\nArquivos gerados em {diretorio_saida}")
    print(f"Anexe na conversa o arquivo: {caminho_pacote}")
    print(
        "\nOs arquivos do INEP são anonimizados e separados por variável: as contagens são por curso, "
        "questão e resposta, e não permitem ligar respostas do mesmo estudante."
    )


def principal(argumentos: Iterable[str] | None = None) -> int:
    """Interpreta argumentos da linha de comando e inicia a extração."""
    analisador = argparse.ArgumentParser(
        description="Extrai dos microdados do ENADE as respostas de percepção (QE_I27 a QE_I68) dos cursos de Ciência da Computação."
    )
    analisador.add_argument("--anos", type=int, nargs="+", default=ANOS_PADRAO, help="Edições a extrair (padrão: 2017 2021).")
    analisador.add_argument(
        "--bruto",
        type=Path,
        default=DIRETORIO_DADOS_BRUTOS,
        help="Pasta que contém as edições, em ZIP ou pastas como microdados_Enade_2021_LGPD (padrão: data/raw).",
    )
    analisador.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA_PADRAO)
    analisador.add_argument("--qe-inicio", type=int, default=QE_INICIO)
    analisador.add_argument("--qe-fim", type=int, default=QE_FIM)
    opcoes = analisador.parse_args(argumentos)
    try:
        executar_extracao(sorted(set(opcoes.anos)), opcoes.bruto, opcoes.saida, opcoes.qe_inicio, opcoes.qe_fim)
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
