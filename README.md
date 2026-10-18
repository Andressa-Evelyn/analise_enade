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

## Perfil dos concluintes

O script `src/perfil.py` caracteriza os concluintes quanto a sexo, idade, renda familiar, situação de trabalho, tipo de escola no ensino médio e escolaridade dos pais na edição mais recente com Ciência da Computação e microdados publicados, o ENADE 2021 (o de 2024 ainda não consta no portal do INEP). Ele lê o ZIP `data/raw/microdados_enade_2021.zip`, baixado de `https://download.inep.gov.br/microdados/microdados_enade_2021.zip`. Com o ambiente da seção anterior ativado:

```bash
python src/perfil.py
```

Os cursos de Ciência da Computação (`CO_GRUPO=4004`) são divididos em quatro grupos: **Unifor** (`CO_IES=29`, `CO_CURSO=2209`), **CE privadas** e **CE públicas** (demais cursos com `CO_UF_CURSO=23`, separados por `CO_CATEGAD`: 1 a 3 públicas, 4 e 5 privadas) e **Brasil** (todos os cursos do grupo, incluindo a Unifor). O grupo de cada estudante vem do `CO_CURSO`, ligando cada arquivo de variável ao arquivo de identificação (`arq1`).

| Variável | Arquivo | Origem | Categorias |
| -------- | ------- | ------ | ---------- |
| `TP_SEXO` | `arq5` | Registro administrativo | M = Masculino; F = Feminino |
| `NU_IDADE` | `arq6` | Receita Federal, idade em 14/11/2021 | Agrupada em até 22, 23–24, 25–29, 30–39 e 40 ou mais |
| `QE_I04` | `arq10` | Questionário do Estudante | Escolaridade do pai: A nenhuma; B fundamental 1º ao 5º ano; C fundamental 6º ao 9º ano; D ensino médio; E graduação; F pós-graduação |
| `QE_I05` | `arq11` | Questionário do Estudante | Escolaridade da mãe, com as mesmas categorias de `QE_I04` |
| `QE_I08` | `arq14` | Questionário do Estudante | A até 1,5 SM; B 1,5–3; C 3–4,5; D 4,5–6; E 6–10; F 10–30; G acima de 30 (SM de R$ 1.100,00) |
| `QE_I10` | `arq16` | Questionário do Estudante | A não trabalha; B eventualmente; C até 20 h; D 21–39 h; E 40 h ou mais (exceto estágio e bolsas) |
| `QE_I17` | `arq23` | Questionário do Estudante | A todo em escola pública; B todo em privada; C todo no exterior; D maior parte em pública; E maior parte em privada; F parte no Brasil e parte no exterior |

Cuidados adotados:

- O microdado de 2021 registra a Unifor com `CO_CATEGAD=2` (Pública Estadual), mas ela é privada sem fins lucrativos. O script não usa essa categoria para a Unifor, que forma um grupo próprio, evitando classificá-la como pública.
- Sexo e idade cobrem todos os 94 inscritos da Unifor; as variáveis do Questionário do Estudante consideram apenas os 81 que responderam. Os percentuais são calculados sobre quem respondeu.
- Os arquivos são anonimizados e separados por variável, então não é possível cruzar variáveis de um mesmo estudante (por exemplo, renda × nota ou escola × escolaridade dos pais). As comparações são agregadas por grupo de cursos.
- O grupo "CE privadas" reúne poucas instituições, e uma delas concentra 58 dos 94 concluintes; diferenças em relação a esse grupo devem ser lidas com cautela.

### Resultados (ENADE 2021)

**Sexo** (n: Unifor 94, CE privadas 94, CE públicas 301, Brasil 12.730)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Masculino | 93,6% | 91,5% | 86,0% | 89,4% |
| Feminino | 6,4% | 8,5% | 14,0% | 10,6% |

**Idade**

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Média | 26,1 | 27,4 | 25,3 | 25,3 |
| Mediana | 25 | 25 | 24 | 24 |
| Desvio padrão | 4,0 | 5,9 | 3,6 | 4,6 |
| Q1–Q3 | 23,2–27 | 24–29 | 23–26 | 22–27 |
| Até 22 anos | 8,5% | 10,6% | 16,6% | 28,5% |
| 23 a 24 anos | 30,9% | 26,6% | 34,6% | 27,2% |
| 25 a 29 anos | 45,7% | 39,4% | 39,5% | 31,1% |
| 30 a 39 anos | 12,8% | 18,1% | 8,6% | 11,3% |
| 40 anos ou mais | 2,1% | 5,3% | 0,7% | 1,7% |

**Renda familiar – QE_I08** (respondentes: Unifor 81, CE privadas 74, CE públicas 281, Brasil 11.118)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Até 1,5 SM | 6,2% | 5,4% | 18,9% | 8,9% |
| 1,5 a 3 SM | 22,2% | 20,3% | 31,7% | 22,5% |
| 3 a 4,5 SM | 22,2% | 12,2% | 17,4% | 19,0% |
| 4,5 a 6 SM | 22,2% | 13,5% | 16,0% | 16,0% |
| 6 a 10 SM | 18,5% | 13,5% | 9,6% | 19,2% |
| 10 a 30 SM | 8,6% | 33,8% | 5,7% | 12,6% |
| Acima de 30 SM | 0,0% | 1,4% | 0,7% | 1,8% |

**Situação de trabalho – QE_I10** (mesmos respondentes da renda)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Não trabalha | 28,4% | 18,9% | 24,9% | 26,9% |
| Trabalha eventualmente | 4,9% | 1,4% | 6,4% | 4,5% |
| Até 20 h semanais | 4,9% | 2,7% | 2,8% | 3,7% |
| 21 a 39 h semanais | 8,6% | 6,8% | 6,8% | 10,5% |
| 40 h semanais ou mais | 53,1% | 70,3% | 59,1% | 54,3% |

**Tipo de escola no ensino médio – QE_I17** (respondentes: Unifor 81, CE privadas 74, CE públicas 281, Brasil 11.117)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Todo em escola pública | 28,4% | 28,4% | 65,1% | 56,8% |
| Maior parte em pública | 1,2% | 1,4% | 2,1% | 2,7% |
| Maior parte em privada | 6,2% | 4,1% | 2,1% | 4,1% |
| Todo em escola privada | 64,2% | 66,2% | 30,6% | 35,9% |
| Todo no exterior | 0,0% | 0,0% | 0,0% | 0,2% |
| Parte no Brasil e parte no exterior | 0,0% | 0,0% | 0,0% | 0,3% |

**Escolaridade do pai – QE_I04** (respondentes: Unifor 81, CE privadas 74, CE públicas 281, Brasil 11.118)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Nenhuma | 2,5% | 2,7% | 7,8% | 2,9% |
| Fundamental: 1º ao 5º ano | 12,3% | 5,4% | 26,0% | 13,1% |
| Fundamental: 6º ao 9º ano | 11,1% | 16,2% | 17,1% | 13,6% |
| Ensino médio | 39,5% | 36,5% | 33,8% | 38,6% |
| Graduação | 24,7% | 23,0% | 10,7% | 22,7% |
| Pós-graduação | 9,9% | 16,2% | 4,6% | 9,1% |

**Escolaridade da mãe – QE_I05** (respondentes: Unifor 81, CE privadas 74, CE públicas 281, Brasil 11.116)

| | Unifor | CE privadas | CE públicas | Brasil |
| - | -----: | ----------: | ----------: | -----: |
| Nenhuma | 3,7% | 0,0% | 3,2% | 1,1% |
| Fundamental: 1º ao 5º ano | 7,4% | 5,4% | 17,1% | 8,9% |
| Fundamental: 6º ao 9º ano | 4,9% | 12,2% | 15,7% | 11,5% |
| Ensino médio | 39,5% | 40,5% | 37,0% | 39,3% |
| Graduação | 25,9% | 29,7% | 14,2% | 25,5% |
| Pós-graduação | 18,5% | 12,2% | 12,8% | 13,7% |

### Interpretação

- **Sexo:** o curso é predominantemente masculino (93,6%; 6 mulheres entre 94 concluintes), com a menor participação feminina entre os grupos comparados.
- **Idade:** os concluintes da Unifor terminam o curso mais velhos que a média nacional e que os das públicas do Ceará (média de 26,1 anos; 76,6% entre 23 e 29). Só 8,5% concluem com até 22 anos, contra 28,5% no Brasil, o que sugere conclusão mais longa que o período regular.
- **Renda:** perfil de classe média, concentrado entre 1,5 e 10 SM. A faixa mediana é de 3 a 4,5 SM; 28,4% têm renda familiar de até 3 SM, 44,4% de 3 a 6 SM e 27,2% acima de 6 SM. A renda é maior que a das públicas do Ceará (50,5% até 3 SM) e menor que a das demais privadas do estado (48,6% acima de 6 SM).
- **Trabalho:** 71,6% trabalham, e 53,1% cumprem 40 horas semanais ou mais, proporção semelhante à nacional (54,3%) e menor que a dos demais grupos do Ceará.
- **Escola no ensino médio:** 70,4% cursaram o ensino médio todo ou a maior parte em escola privada (64,2% todo em privada) e 29,6% em escola pública. A distribuição é praticamente igual à das demais privadas do Ceará e o oposto da observada nas públicas (67,3% vindos de escola pública) e no Brasil (59,5%).
- **Escolaridade dos pais:** as mães são mais escolarizadas que os pais. 44,4% das mães têm curso superior (25,9% graduação e 18,5% pós-graduação, a maior proporção de pós entre os grupos), contra 34,6% dos pais. Para ambos, o nível mais comum é o ensino médio (39,5%). Ainda assim, cerca de dois em cada três pais (65,4%) e mais da metade das mães (55,6%) não têm curso superior; 25,9% dos pais e 16,0% das mães estudaram no máximo até o ensino fundamental. Os níveis são próximos aos das demais privadas e da média nacional e bem superiores aos das públicas do Ceará (15,3% dos pais e 27,0% das mães com superior).
- **Perfil típico:** homem de cerca de 25 anos, vindo de escola privada, de família com renda entre 3 e 6 salários mínimos e pais com ensino médio ou superior (mais frequentemente a mãe), que trabalha em tempo integral. A combinação de jornada integral e conclusão tardia é relevante para planejar a preparação para o ENADE, pois limita o tempo de estudo disponível. São dados descritivos de uma edição e não permitem atribuir causas.

Os resultados ficam em `data/processed/perfil_2021/`: `idade_resumo.csv`, `sexo.csv`, `faixa_etaria.csv`, `renda_familiar.csv`, `situacao_trabalho.csv`, `tipo_escola_medio.csv`, `escolaridade_pai.csv` e `escolaridade_mae.csv` (contagens `n` e percentuais `%` por grupo), além de um gráfico de barras `.png` para cada distribuição.

## Comparação do perfil com outras instituições do Ceará

O script `src/comparacao_perfil.py` testa se o perfil dos concluintes da Unifor difere do perfil dos concluintes dos demais cursos de Ciência da Computação do Ceará no ENADE 2021. Ele reutiliza o ZIP e os filtros de `src/perfil.py`:

```bash
python src/comparacao_perfil.py
```

A Unifor é comparada com três grupos: **CE privadas** (94 concluintes, 5 IES), **CE públicas** (301 concluintes, 3 IES) e **CE demais** (todos os 395 concluintes do estado, exceto a Unifor). Testes usados:

| Variável | Teste | Medida de efeito |
| -------- | ----- | ---------------- |
| Sexo | Exato de Fisher (tabela 2×2) | V de Cramér |
| Idade | Mann-Whitney (bilateral) | Correlação rank-biserial (positiva = Unifor mais velha) |
| Renda familiar | Qui-quadrado, em três faixas: até 3 SM, 3 a 6 SM, acima de 6 SM | V de Cramér |
| Situação de trabalho | Qui-quadrado, em três faixas: não trabalha, menos de 40 h, 40 h ou mais | V de Cramér |
| Escola no ensino médio | Exato de Fisher, em pública (todo ou maior parte) × privada (todo ou maior parte) | V de Cramér |
| Escolaridade do pai e da mãe | Qui-quadrado, em três faixas: até fundamental, ensino médio, superior (graduação ou pós) | V de Cramér |

As variáveis do questionário foram agrupadas para que nenhuma frequência esperada ficasse abaixo de 5 (a menor foi 11,0). O ensino médio no exterior ficou fora do teste de escola por ser raro (nenhum caso no Ceará). São 21 testes, então os valores-p também foram ajustados pelo método de Holm para controlar comparações múltiplas. O nível de significância é 5%.

### Indicadores por grupo

| | Unifor | CE privadas | CE públicas | CE demais |
| - | -----: | ----------: | ----------: | --------: |
| Concluintes | 94 | 94 | 301 | 395 |
| Feminino | 6,4% | 8,5% | 14,0% | 12,7% |
| Idade média / mediana | 26,1 / 25 | 27,4 / 25 | 25,3 / 24 | 25,8 / 25 |
| Respondentes do questionário | 81 | 74 | 281 | 355 |
| Renda até 3 SM | 28,4% | 25,7% | 50,5% | 45,4% |
| Renda de 3 a 6 SM | 44,4% | 25,7% | 33,5% | 31,8% |
| Renda acima de 6 SM | 27,2% | 48,6% | 16,0% | 22,8% |
| Não trabalha | 28,4% | 18,9% | 24,9% | 23,7% |
| Trabalha menos de 40 h | 18,5% | 10,8% | 16,0% | 14,9% |
| Trabalha 40 h ou mais | 53,1% | 70,3% | 59,1% | 61,4% |
| Ensino médio em escola pública | 29,6% | 29,7% | 67,3% | 59,4% |
| Ensino médio em escola privada | 70,4% | 70,3% | 32,7% | 40,6% |
| Pai até fundamental | 25,9% | 24,3% | 50,9% | 45,4% |
| Pai com ensino médio | 39,5% | 36,5% | 33,8% | 34,4% |
| Pai com superior | 34,6% | 39,2% | 15,3% | 20,3% |
| Mãe até fundamental | 16,0% | 17,6% | 35,9% | 32,1% |
| Mãe com ensino médio | 39,5% | 40,5% | 37,0% | 37,7% |
| Mãe com superior | 44,4% | 41,9% | 27,0% | 30,1% |

### Resultados dos testes

| Variável | Comparação | p | p (Holm) | Efeito |
| -------- | ---------- | -: | -------: | -----: |
| Sexo | Unifor × CE privadas | 0,782 | 1,000 | V = 0,04 |
| Sexo | Unifor × CE públicas | 0,069 | 0,757 | V = 0,10 |
| Sexo | Unifor × CE demais | 0,104 | 0,939 | V = 0,08 |
| Idade | Unifor × CE privadas | 0,314 | 1,000 | r = −0,08 |
| Idade | Unifor × CE públicas | **0,024** | 0,292 | r = 0,15 |
| Idade | Unifor × CE demais | 0,144 | 1,000 | r = 0,10 |
| Renda familiar | Unifor × CE privadas | **0,013** | 0,179 | V = 0,24 |
| Renda familiar | Unifor × CE públicas | **0,001** | **0,024** | V = 0,19 |
| Renda familiar | Unifor × CE demais | **0,018** | 0,228 | V = 0,14 |
| Trabalho | Unifor × CE privadas | 0,088 | 0,878 | V = 0,18 |
| Trabalho | Unifor × CE públicas | 0,630 | 1,000 | V = 0,05 |
| Trabalho | Unifor × CE demais | 0,385 | 1,000 | V = 0,07 |
| Escola no ensino médio | Unifor × CE privadas | 1,000 | 1,000 | V = 0,00 |
| Escola no ensino médio | Unifor × CE públicas | **< 0,001** | **< 0,001** | V = 0,32 |
| Escola no ensino médio | Unifor × CE demais | **< 0,001** | **< 0,001** | V = 0,23 |
| Escolaridade do pai | Unifor × CE privadas | 0,837 | 1,000 | V = 0,05 |
| Escolaridade do pai | Unifor × CE públicas | **< 0,001** | **< 0,001** | V = 0,24 |
| Escolaridade do pai | Unifor × CE demais | **0,002** | **0,034** | V = 0,17 |
| Escolaridade da mãe | Unifor × CE privadas | 0,941 | 1,000 | V = 0,03 |
| Escolaridade da mãe | Unifor × CE públicas | **< 0,001** | **0,015** | V = 0,20 |
| Escolaridade da mãe | Unifor × CE demais | **0,007** | 0,101 | V = 0,15 |

Em negrito, os valores abaixo de 0,05.

### Indicadores por instituição

O microdado não traz o nome das instituições, por isso elas aparecem pelo `CO_IES`.

| CO_IES | Grupo | Concluintes | Feminino | Idade média | Renda até 3 SM | Renda acima de 6 SM | Trabalha | 40 h ou mais | EM em escola pública | Pai com superior | Mãe com superior |
| -----: | ----- | ----------: | -------: | ----------: | -------------: | ------------------: | -------: | -----------: | -------------------: | ---------------: | ---------------: |
| 1807 | CE públicas | 136 | 18,4% | 26,3 | 51,1% | 15,6% | 77,8% | 63,0% | 65,9% | 11,9% | 21,5% |
| 583 | CE públicas | 99 | 12,1% | 24,1 | 46,4% | 21,6% | 71,1% | 55,7% | 64,9% | 24,7% | 30,9% |
| **29** | **Unifor** | **94** | **6,4%** | **26,1** | **28,4%** | **27,2%** | **71,6%** | **53,1%** | **29,6%** | **34,6%** | **44,4%** |
| 95 | CE públicas | 66 | 7,6% | 25,0 | 57,1% | 6,1% | 75,5% | 55,1% | 75,5% | 6,1% | 34,7% |
| 555 | CE privadas | 58 | 8,6% | 28,0 | 18,4% | 65,8% | 68,4% | 60,5% | 7,9% | 60,5% | 60,5% |
| 1819 | CE privadas | 19 | 5,3% | 27,2 | 15,8% | 31,6% | 100,0% | 89,5% | 42,1% | 15,8% | 21,1% |
| 1658 | CE privadas | 10 | 10,0% | 26,6 | 50,0% | 30,0% | 100,0% | 80,0% | 60,0% | 30,0% | 40,0% |
| 1059 | CE privadas | 4 | 0,0% | 23,5 | 100,0% | 0,0% | 50,0% | 25,0% | 75,0% | 0,0% | 0,0% |
| 448 | CE privadas | 3 | 33,3% | 26,0 | 0,0% | 66,7% | 100,0% | 100,0% | 66,7% | 0,0% | 0,0% |

### Interpretação

- **Origem escolar e familiar: igual às privadas, oposta às públicas.** Em tipo de escola e escolaridade dos pais, a Unifor é praticamente idêntica às demais privadas do Ceará (p ≥ 0,84; efeitos próximos de zero). Em relação às públicas, as diferenças são as mais fortes de toda a análise e se mantêm após a correção de Holm: 70,4% dos concluintes da Unifor vieram de escola privada, contra 32,7% nas públicas (V = 0,32, o maior efeito); 34,6% dos pais e 44,4% das mães têm curso superior, contra 15,3% e 27,0%. Comparada com o conjunto do estado (CE demais), a Unifor também se distingue na escola e na escolaridade do pai.
- **Renda: intermediária.** A Unifor difere de todos os grupos na renda familiar, mas em direções opostas. Em relação às públicas, sua renda é **mais alta** (28,4% até 3 SM contra 50,5%), diferença que se mantém após a correção (p de Holm = 0,024). Em relação às demais privadas, é **mais baixa** (27,2% acima de 6 SM contra 48,6%), mas essa diferença deixa de ser significativa com a correção, e o grupo de privadas é puxado pela IES 555 (65,8% acima de 6 SM). A Unifor tem a distribuição mais concentrada na faixa de 3 a 6 SM (44,4%).
- **Sexo não difere.** A Unifor tem a menor proporção feminina entre as maiores instituições (6,4%), mas nenhum teste é significativo. A baixa presença de mulheres é uma característica da área no Ceará como um todo (12,7% nos demais cursos). Com só 6 mulheres na Unifor, o teste tem pouco poder para detectar diferenças pequenas.
- **Idade difere pouco.** Os concluintes da Unifor são um pouco mais velhos que os das públicas (mediana de 25 contra 24 anos; p = 0,024), mas o efeito é pequeno (r = 0,15) e não resiste à correção de Holm.
- **Trabalho não difere.** Cerca de 70% a 80% dos concluintes trabalham em todas as instituições, e a maioria trabalha 40 h ou mais. A Unifor tem a menor proporção de jornada integral entre as maiores IES (53,1%), mas sem significância estatística.
- **Conclusão:** em sexo, idade e situação de trabalho, o perfil da Unifor **não difere** do restante do Ceará: predominantemente homens, por volta dos 25 anos, que trabalham em tempo integral. As diferenças estão na **origem socioeconômica**. Em escola de ensino médio e escolaridade dos pais, a Unifor se alinha às demais privadas e se distancia claramente das públicas. Na renda, fica entre as públicas (mais baixa) e as demais privadas (mais alta).

Limitações: os grupos de comparação são pequenos (sobretudo as privadas, com 4 de 5 IES abaixo de 20 concluintes), os dados são de uma única edição e os testes indicam associação, não causa. As variáveis do questionário dependem de quem respondeu (86% dos inscritos da Unifor).

Os resultados ficam em `data/processed/perfil_2021/`: `comparacao_ceara_testes.csv` (estatísticas, valores-p brutos e ajustados, efeitos e menor frequência esperada), `comparacao_ceara_grupos.csv` e `comparacao_ceara_por_ies.csv`.
