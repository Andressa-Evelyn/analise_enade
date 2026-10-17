## Objetivo

Produzir análises e visualizações que respondam às necessidades levantadas com a coordenação, comparando os indicadores da Unifor com os dos demais cursos de Ciência da Computação do **Ceará** (instituições públicas e privadas) e com a  **média nacional** .

## Desempenho acadêmico 

O script lê os arquivos de identificação e notas diretamente dos ZIPs em `data/raw`, sem descompactá-los. Para executar:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/desempenho.py
```

Os filtros usam `CO_IES=29`, `CO_MUNIC_CURSO=2304400` (Fortaleza) e `CO_CURSO=2209`. O grupo de área muda conforme o dicionário da edição: `CO_GRUPO=40` em 2005; `CO_GRUPO=40` e `CO_SUBAREA=4001` em 2008; `CO_GRUPO=4004` de 2011 a 2021. Nas edições amostrais de 2005 e 2008, são considerados apenas concluintes (`TP_INSCRICAO=0`) e os resultados são ponderados por `PESO_AMOSTRA`.

| Edição | Identificados | Com nota válida | Nota geral | Formação geral | Componente específico |
| -------- | ------------: | ---------------: | ---------: | ---------------: | ---------------------: |
| 2005     |            31 |               22 |     39,66* |           56,63* |                 34,02* |
| 2008     |            50 |               42 |     40,20* |           53,35* |                 35,82* |
| 2011     |            72 |               49 |      45,18 |            51,87 |                  42,94 |
| 2014     |            43 |               32 |      52,42 |            63,18 |                  48,80 |
| 2017     |            78 |               67 |      46,01 |            52,95 |                  43,68 |
| 2021     |            94 |               67 |      40,61 |            37,07 |                  41,78 |

\* Média ponderada pelo peso amostral do INEP. Os tamanhos `n` são números de registros válidos, não o total de estudantes representado pelos pesos.

Na série disponível, a nota geral sobe de 39,66 em 2005 até o pico de 52,42 em 2014, depois recua para 46,01 em 2017 e 40,61 em 2021. Formação geral cai de 56,63 para 37,07 entre 2005 e 2021; o componente específico sobe de 34,02 para 41,78 no mesmo intervalo, após atingir 48,80 em 2014. A diferença entre 2005 e 2021 é de +0,95 ponto na nota geral, -19,56 em formação geral e +7,75 no componente específico. São edições com grupos diferentes de concluintes e provas de matrizes distintas; a série descreve médias por edição, não acompanha os mesmos estudantes nem permite atribuir causas às variações.

Os itens com menor taxa de acerto foram `OCE_36` em 2005 (13,6%), `OCE_21` e `OCE_26` em 2008 (11,9%), `OCE_23` a `OCE_27` em 2011 (0%), `OCE_04` e `OCE_22` em 2014 (15,6%), `OCE_15` em 2017 (10,4%) e `OCE_26` em 2021 (16,4%). Esses códigos representam posições nos vetores de cada prova, não os nomes dos conteúdos. Para nomear os temas, é necessário associar cada item ao caderno e gabarito daquela edição; números de posições entre provas não identificam necessariamente a mesma questão.

Os resultados e gráficos ficam em `data/processed/`; `desempenho_historico_variacao.csv` contém médias e variações entre edições. A lista oficial de microdados consultada vai até 2023, e não há arquivo ENADE 2024 em `data/raw`; por isso 2024 ainda não entra na série, embora Ciência da Computação tenha sido avaliada nessa edição. Quando o microdado de 2024 estiver disponível, seu dicionário e os filtros do curso deverão ser validados antes de incorporá-lo.

## Análise comparativa do desempenho

A análise comparativa confronta as médias da Unifor com as dos demais cursos de Ciência da Computação do Ceará, separados entre instituições públicas e privadas, e com a média nacional. São consideradas três medidas: nota geral (`NT_GER`), formação geral (`NT_FG`) e componente específico (`NT_CE`).

A comparação abrange as edições de 2008, 2011, 2014, 2017 e 2021. A edição de 2005 foi excluída desta etapa porque o código de área disponível identifica Computação de forma ampla e não permite isolar Ciência da Computação com segurança a partir das variáveis utilizadas. Os filtros de área variam por edição: em 2008, `CO_GRUPO=40` e `CO_SUBAREA=4001`; de 2011 a 2021, `CO_GRUPO=4004`. Em 2008, são considerados os concluintes (`TP_INSCRICAO=0`) e as médias dos cursos são ponderadas por `PESO_AMOSTRA`.

Para tornar os cursos comparáveis, primeiro é calculada a média de cada curso em cada componente. Em seguida, calcula-se a média dessas médias para cada grupo, atribuindo o mesmo peso a cada curso, independentemente do número de participantes. Assim, os resultados representam a média dos cursos, e não a média de todos os estudantes individualmente. A média nacional inclui os cursos da Unifor e os cursos cearenses que também integram os grupos regionais; portanto, não constitui um grupo independente desses conjuntos.

Para facilitar a leitura, as tabelas a seguir apresentam as médias por grupo em cada edição. Os valores estão arredondados para duas casas decimais.

**Nota geral**

| Edição | Unifor | Públicos do Ceará | Privados do Ceará | Brasil |
| --- | ---: | ---: | ---: | ---: |
| 2008 | 40,20 | 40,63 | 35,07 | 34,31 |
| 2011 | 45,18 | 40,35 | 29,99 | 32,48 |
| 2014 | 52,42 | 53,00 | 44,67 | 43,05 |
| 2017 | 46,01 | 48,76 | 40,18 | 41,48 |
| 2021 | 40,61 | 37,75 | 38,75 | 35,36 |

**Formação geral**

| Edição | Unifor | Públicos do Ceará | Privados do Ceará | Brasil |
| --- | ---: | ---: | ---: | ---: |
| 2008 | 53,35 | 52,48 | 48,12 | 51,45 |
| 2011 | 51,87 | 53,96 | 49,21 | 51,34 |
| 2014 | 63,18 | 66,73 | 60,34 | 59,41 |
| 2017 | 52,95 | 57,32 | 50,59 | 53,57 |
| 2021 | 37,07 | 37,55 | 39,99 | 36,76 |

**Componente específico**

| Edição | Unifor | Públicos do Ceará | Privados do Ceará | Brasil |
| --- | ---: | ---: | ---: | ---: |
| 2008 | 35,82 | 36,68 | 30,73 | 28,59 |
| 2011 | 42,94 | 35,80 | 23,56 | 26,17 |
| 2014 | 48,80 | 48,41 | 39,44 | 37,58 |
| 2017 | 43,68 | 45,88 | 36,70 | 37,44 |
| 2021 | 41,78 | 37,79 | 38,31 | 34,88 |

Os resultados indicam que a Unifor apresentou nota geral superior à média nacional em todas as edições analisadas. A diferença foi de aproximadamente 5,88 pontos em 2008, 12,71 em 2011, 9,37 em 2014, 4,52 em 2017 e 5,25 em 2021. Em relação aos demais cursos privados do Ceará, a nota geral da Unifor também foi superior em todas as edições: as diferenças variaram de 1,86 ponto em 2021 a 15,19 em 2011. A comparação com os cursos públicos cearenses foi mais equilibrada: a Unifor ficou ligeiramente abaixo em 2008, 0,44 ponto, e em 2014, 0,58 ponto, mas acima em 2011, 4,83 pontos, em 2017, 2,75 pontos, e em 2021, 2,86 pontos.

Na formação geral, o desempenho da Unifor foi superior à média nacional em 2008, 2011 e 2014, com diferenças de 1,90, 0,52 e 3,78 pontos, respectivamente. Em 2017, ficou 0,62 ponto abaixo da média nacional; em 2021, ficou 0,30 ponto acima. Em comparação com os demais cursos privados do Ceará, a Unifor obteve média superior entre 2008 e 2017, mas inferior em 2021. Frente aos cursos públicos do Ceará, o resultado variou entre as edições, com médias inferiores em 2011, 2014, 2017 e 2021, e superior em 2008.

No componente específico, a Unifor superou a média nacional em todas as edições, com diferenças entre 6,24 e 16,77 pontos. Também apresentou médias superiores às dos demais cursos privados do Ceará em todas as edições. Na comparação com os cursos públicos cearenses, ficou abaixo por 0,85 ponto em 2008, mas acima nas quatro edições seguintes; a diferença foi especialmente expressiva em 2011, quando alcançou 7,14 pontos.

Esses resultados são descritivos e não permitem atribuir causas às diferenças observadas. As edições do ENADE envolvem provas e grupos de participantes distintos, de modo que as variações entre anos não devem ser interpretadas como acompanhamento dos mesmos estudantes. A quantidade de cursos em cada grupo também varia por edição, o que deve ser considerado na interpretação das médias.

### Como executar a análise comparativa

O script lê os arquivos de microdados diretamente dos arquivos ZIP armazenados em `data/raw/`, sem exigir a descompactação manual. Na raiz do repositório, crie e ative um ambiente virtual, instale as dependências e execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/comparativo.py
```

No Windows PowerShell, a ativação do ambiente virtual é:

```powershell
.venv\Scripts\Activate.ps1
```

O script gera os seguintes arquivos em `data/processed/`:

- `comparativo_medias_por_curso.csv`: médias dos três componentes por curso;
- `comparativo_resumo_grupos.csv`: médias e contagens de cursos e instituições por grupo;
- `comparativo_diferencas_unifor.csv`: diferenças entre as médias da Unifor e as de cada grupo;
- `comparativo_notas_2008.png`, `comparativo_notas_2011.png`, `comparativo_notas_2014.png`, `comparativo_notas_2017.png` e `comparativo_notas_2021.png`: gráficos gerados pelo script para apoiar a análise.

