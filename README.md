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

## Percepção dos estudantes sobre o curso

A análise de percepção usa as respostas dos concluintes ao Questionário do Estudante sobre o processo formativo (`QE_I27` a `QE_I68`, 42 afirmações sobre organização didático-pedagógica, infraestrutura e oportunidades de formação). Ela cobre as edições de 2017 e 2021 do ENADE, a mais recente com Ciência da Computação e microdados publicados e a anterior. O texto das 42 afirmações é idêntico nas duas edições, então elas são comparáveis. Em ambas, as questões ficam juntas no `arq4` dos microdados.

Como ler as respostas: a escala vai de 1 (discordo totalmente) a 6 (concordo totalmente). O código 7 significa "não sei responder" e o 8, "não se aplica". Os códigos 7 e 8 e as respostas em branco ficam fora das médias, das porcentagens e dos testes, e são reportados à parte. A **média** é a média das notas de 1 a 6; a **concordância** é a proporção de notas 4, 5 e 6 entre quem deu nota de 1 a 6.

Os grupos seguem a lógica das seções anteriores: **Unifor**, **CE privadas**, **CE públicas** e **Brasil** (todos os cursos de Ciência da Computação, incluindo a Unifor). Nos testes, a Unifor também é comparada com **CE demais** (todos os cursos do Ceará, exceto a Unifor) e com **Brasil (exceto Unifor)**, para que ela não apareça dos dois lados da comparação.

### Como executar

O `extrair_percepcao.py` lê os ZIPs de 2017 e 2021 em `data/raw` e gera as contagens por curso, questão e resposta. Os três scripts seguintes leem só esse CSV, então não precisam de `data/raw`. Com o ambiente das seções anteriores ativado (no Windows, `.venv\Scripts\Activate.ps1`):

```bash
python -m pip install -r requirements.txt   # inclui openpyxl, usado para ler o dicionário do INEP
python src/extrair_percepcao.py             # só para regenerar as contagens; exige data/raw
python src/percepcao.py                     # resumo por questão, grupo e edição
python src/percepcao_ranking.py             # ranking e gráficos das questões da Unifor
python src/percepcao_comparacao.py          # testes da Unifor contra os demais grupos
```

| Script | O que faz | Saídas em `data/processed/percepcao/` |
| ------ | --------- | ------------------------------------- |
| `extrair_percepcao.py` | Extrai as contagens de respostas por curso e copia a documentação do INEP | `percepcao_contagens_por_curso.csv`, `mapa_questoes_arquivos.csv`, `lista_arquivos_fonte.csv` |
| `percepcao.py` | Calcula média, concordância, discordância e respostas "não sei"/"não se aplica" | `percepcao_resumo_por_grupo.csv` |
| `percepcao_ranking.py` | Ordena as 42 questões da Unifor e desenha as 5 melhores e as 5 piores | `percepcao_ranking_unifor.csv`, `percepcao_ranking_unifor_2017.png`, `percepcao_ranking_unifor_2021.png` |
| `percepcao_comparacao.py` | Compara a Unifor com os outros grupos, questão por questão | `percepcao_comparacao_unifor.csv`, `percepcao_comparacao_ce_demais_2017.png`, `percepcao_comparacao_ce_demais_2021.png` |

Cuidados adotados:

- Os arquivos do INEP são anonimizados e separados por variável. As análises são agregadas por grupo de cursos e não ligam as respostas de um mesmo estudante a outras variáveis, como renda ou nota.
- Cada questão tem um número diferente de respondentes válidos, porque quem não avaliou (em branco, "não sei" ou "não se aplica") sai do cálculo. Os tamanhos estão na tabela abaixo e, por questão, em `n_validos`.
- O texto de cada questão vem do dicionário de variáveis do INEP (`documentacao/2021`).

### Respondentes

| Grupo | 2017: inscritos | 2017: respondentes válidos por questão | 2021: inscritos | 2021: respondentes válidos por questão |
| ----- | --------------: | -------------------------------------: | --------------: | -------------------------------------: |
| Unifor | 78 | 54 a 68 | 94 | 47 a 81 |
| CE privadas | 138 | 89 a 122 | 94 | 48 a 74 |
| CE públicas | 158 | 85 a 150 | 301 | 176 a 277 |
| Brasil | 10.186 | 6.318 a 8.792 | 12.733 | 7.845 a 10.975 |

### Resultados

**Questões mais bem e mais mal avaliadas pela Unifor.** A tabela mostra as 5 melhores e as 5 piores médias de cada edição. A coluna "Não sei / não se aplica" é a porcentagem de respostas 7 e 8 entre quem respondeu à questão.

ENADE 2021:

| Posição | Questão | Tema | Média | Concordância | Respondentes válidos | Não sei / não se aplica |
| ------: | ------- | ---- | ----: | -----------: | -------------------: | ----------------------: |
| 1 | QE_I43 | Atividades de extensão | 5,06 | 87,2% | 78 | 3,7% |
| 2 | QE_I44 | Iniciação científica | 5,03 | 85,0% | 80 | 1,2% |
| 3 | QE_I42 | Dedicação exigida pelo curso | 5,00 | 91,3% | 80 | 1,2% |
| 4 | QE_I32 | Aprender a trabalhar em equipe | 4,89 | 85,2% | 81 | 0,0% |
| 5 | QE_I50 | Estágio supervisionado | 4,79 | 82,9% | 70 | 13,6% |
| 38 | QE_I48 | Atividades práticas suficientes | 3,70 | 60,5% | 81 | 0,0% |
| 39 | QE_I62 | Equipamentos das aulas práticas para a quantidade de estudantes | 3,65 | 57,5% | 80 | 1,2% |
| 40 | QE_I65 | Biblioteca virtual | 3,36 | 46,8% | 47 | 42,0% |
| 41 | QE_I52 | Intercâmbio e estágio no país | 3,30 | 45,9% | 61 | 24,7% |
| 42 | QE_I53 | Intercâmbio e estágio fora do país | 2,47 | 24,1% | 58 | 28,4% |

ENADE 2017:

| Posição | Questão | Tema | Média | Concordância | Respondentes válidos | Não sei / não se aplica |
| ------: | ------- | ---- | ----: | -----------: | -------------------: | ----------------------: |
| 1 | QE_I44 | Iniciação científica | 5,04 | 88,2% | 68 | 0,0% |
| 2 | QE_I36 | Aprender e atualizar-se permanentemente | 4,95 | 87,9% | 66 | 2,9% |
| 3 | QE_I42 | Dedicação exigida pelo curso | 4,87 | 86,8% | 68 | 0,0% |
| 4 | QE_I32 | Aprender a trabalhar em equipe | 4,85 | 89,7% | 68 | 0,0% |
| 5 | QE_I58 | Uso de tecnologias da informação pelos professores | 4,84 | 82,4% | 68 | 0,0% |
| 38 | QE_I48 | Atividades práticas suficientes | 3,39 | 49,3% | 67 | 1,5% |
| 39 | QE_I62 | Equipamentos das aulas práticas para a quantidade de estudantes | 3,39 | 53,7% | 67 | 1,5% |
| 40 | QE_I61 | Condições das salas de aula | 3,25 | 48,5% | 68 | 0,0% |
| 41 | QE_I65 | Biblioteca virtual | 2,85 | 37,0% | 54 | 20,6% |
| 42 | QE_I64 | Biblioteca: referências bibliográficas | 2,77 | 30,7% | 62 | 8,8% |

**Comparação com os outros cursos.** Cada questão foi comparada pelo teste de Mann-Whitney (bilateral) sobre as notas de 1 a 6. Os valores-p foram ajustados pelo método de Holm, separadamente para cada edição e comparação (42 testes em cada), com nível de 5%. O efeito é a correlação rank-biserial: negativa quando a Unifor tende a dar notas mais baixas que o grupo de comparação. A tabela mostra em quantas das 42 questões a Unifor difere. Em nenhuma comparação ela ficou significativamente acima.

| Comparação | 2017: Unifor menor | 2017: sem diferença | 2021: Unifor menor | 2021: sem diferença |
| ---------- | -----------------: | ------------------: | -----------------: | ------------------: |
| Unifor x CE privadas | 41 | 1 | 24 | 18 |
| Unifor x CE públicas | 22 | 20 | 32 | 10 |
| Unifor x CE demais | 35 | 7 | 32 | 10 |
| Unifor x Brasil (exceto Unifor) | 28 | 14 | 23 | 19 |

Em 2021, 22 das 42 questões aparecem como "Unifor menor" nas quatro comparações ao mesmo tempo. As maiores diferenças em relação ao restante do Ceará (CE demais) em 2021 são estas:

| Questão | Tema | Unifor | CE demais | Brasil (exceto Unifor) | Diferença | p (Holm) | Efeito |
| ------- | ---- | -----: | --------: | ---------------------: | --------: | -------: | -----: |
| QE_I65 | Biblioteca virtual | 3,36 | 5,24 | 5,12 | −1,88 | < 0,001 | −0,54 |
| QE_I62 | Equipamentos das aulas práticas | 3,65 | 5,08 | 4,89 | −1,43 | < 0,001 | −0,55 |
| QE_I63 | Ambientes e equipamentos das aulas práticas adequados ao curso | 3,85 | 5,14 | 5,00 | −1,29 | < 0,001 | −0,49 |
| QE_I59 | Quantidade de funcionários de apoio | 3,93 | 5,21 | 4,95 | −1,28 | < 0,001 | −0,48 |
| QE_I64 | Biblioteca: referências bibliográficas | 3,94 | 5,14 | 5,19 | −1,20 | < 0,001 | −0,42 |
| QE_I48 | Atividades práticas suficientes | 3,70 | 4,77 | 4,50 | −1,07 | < 0,001 | −0,45 |
| QE_I61 | Condições das salas de aula | 4,12 | 5,17 | 4,96 | −1,04 | < 0,001 | −0,46 |
| QE_I37 | Relação professor-aluno | 3,90 | 4,90 | 4,52 | −1,00 | < 0,001 | −0,38 |

As 10 questões de 2021 em que a Unifor não difere significativamente de CE demais são, da menor para a maior diferença de média: QE_I43 (extensão, +0,09), QE_I44 (iniciação científica, +0,07), QE_I42 (dedicação, −0,26), QE_I45 (eventos, −0,26), QE_I50 (estágio, −0,29), QE_I46 (representação em órgãos colegiados, −0,34), QE_I36 (aprender e atualizar-se, −0,35), QE_I32 (trabalho em equipe, −0,40), QE_I51 (trabalho de conclusão de curso, −0,45) e QE_I52 (intercâmbio no país, −0,63). Em QE_I52 a diferença é grande, mas o teste, após a correção de Holm, não a distingue do acaso (p = 0,128), com 61 respondentes válidos da Unifor. Em 2017, contra CE demais, as maiores diferenças foram QE_I65 (−2,15), QE_I64 (−2,08) e QE_I61 (−1,96).

**Evolução da Unifor entre 2017 e 2021** (descritiva, sem teste): a média simples das 42 questões passou de 4,13 para 4,24, com alta em 25 questões e queda em 17. Em 2021, a média simples dos demais grupos foi de 4,93 (CE privadas), 4,97 (CE públicas) e 4,78 (Brasil). As maiores altas foram em QE_I64 (biblioteca, de 2,77 para 3,94), QE_I61 (salas de aula, de 3,25 para 4,12), QE_I65 (biblioteca virtual, de 2,85 para 3,36), QE_I68 (refeitório, cantina e banheiros, de 4,12 para 4,62) e QE_I59 (funcionários de apoio, de 3,44 para 3,93). As maiores quedas foram em QE_I53 (intercâmbio fora do país, de 3,95 para 2,47), QE_I52 (intercâmbio no país, de 3,75 para 3,30), QE_I37 (relação professor-aluno, de 4,21 para 3,90) e QE_I31 (consciência ética, de 4,52 para 4,22).

### Interpretação

- **Pontos fortes da Unifor:** iniciação científica, extensão, dedicação exigida pelo curso e trabalho em equipe ficam entre as questões mais bem avaliadas, e iniciação científica, dedicação e trabalho em equipe aparecem entre as 5 melhores nas duas edições. Nessas questões a Unifor tem nota igual à do restante do Ceará (em extensão e iniciação científica em 2021, ligeiramente acima, sem significância); ela não fica à frente.
- **Pontos fracos:** os equipamentos das aulas práticas (QE_I62) e as atividades práticas suficientes (QE_I48) estão entre as 5 piores questões nas duas edições. Os ambientes das aulas práticas (QE_I63) também têm uma das maiores diferenças em relação ao Ceará. Em 2021, essas três questões ficam de 1,07 a 1,43 ponto abaixo de CE demais.
- **Biblioteca virtual:** é a questão com a maior diferença em relação ao Ceará em 2021 (−1,88) e também a de maior proporção de "não sei" ou "não se aplica" (42,0%). A média vale só para 47 respondentes. O dado não permite separar se o recurso é pouco usado, pouco divulgado ou avaliado de forma negativa.
- **Intercâmbio:** é a questão mais mal avaliada em 2021 (2,47 fora do país, 3,30 no país) e piorou desde 2017. As médias também são baixas nos outros grupos (3,2 a 4,0), então é um ponto fraco comum aos cursos, não só da Unifor. Em 2021, 28,4% (fora do país) e 24,7% (no país) dos respondentes marcaram "não sei" ou "não se aplica".
- **Resposta à pergunta do plano de trabalho:** a avaliação dos concluintes da Unifor difere da dos demais cursos do Ceará, e sempre para baixo. Em 2021, a nota é menor em 32 das 42 questões contra CE demais (35 em 2017), e a diferença se concentra em infraestrutura, apoio e atividades práticas.
- **Tendência:** entre 2017 e 2021 a infraestrutura geral melhorou (biblioteca, salas de aula, funcionários de apoio), mas a distância para o Ceará continua grande nesses itens. Como as edições têm grupos diferentes de concluintes, a comparação descreve médias por edição e não acompanha os mesmos estudantes.

Possíveis encaminhamentos para a coordenação (a validar na reunião de apresentação dos resultados):

- Verificar com os estudantes o que está por trás das notas baixas em equipamentos e ambientes das aulas práticas e em atividades práticas, que são os itens com maior diferença em relação aos outros cursos do Ceará.
- Conferir se a biblioteca virtual é divulgada e usada pelos estudantes, já que 42,0% dos respondentes não souberam ou não consideraram o item aplicável.
- Rever como as oportunidades de intercâmbio e de estágio no país e no exterior são apresentadas, pois a nota piorou desde 2017 e a proporção de "não sei" é alta.
- Manter e divulgar o que está bem avaliado (iniciação científica, extensão, trabalho em equipe), que já está no nível do restante do Ceará.

Limitações:

- Os valores-p tratam os estudantes como independentes, mas eles estão agrupados em cursos, e os grupos de comparação do Ceará têm poucos cursos. Por isso, os valores-p tendem a ser otimistas. O tamanho do efeito e a diferença de média ajudam a julgar se a diferença importa na prática.
- O grupo "CE privadas" é pequeno e concentrado em uma instituição (ver a seção de perfil). Diferenças contra ele devem ser lidas com cautela.
- A média de uma questão vale só para quem a avaliou. Questões com muitas respostas "não sei" ou "não se aplica", como QE_I65, QE_I53 e QE_I52, têm menos respondentes válidos e conclusões mais frágeis.
- São dados de percepção de concluintes em duas edições. Eles indicam associação e diferença entre grupos, não causa.

## Participação no exame

A análise de participação responde às perguntas da seção 5.5 do plano de trabalho: **(1)** qual a proporção de estudantes inscritos que compareceram e tiveram participação válida e **(2)** quantas provas foram entregues em branco ou com apenas parte das questões respondidas. Além disso, avalia se a ausência e o preenchimento parcial (sobretudo nas questões discursivas) diferem dos demais cursos do Ceará e do Brasil e qual o seu efeito direto nas notas do curso.

O script `src/participacao.py` lê os arquivos `arq1` (identificação do curso) e `arq3` (presença, vetores de respostas objetivas, situação das questões discursivas e notas) diretamente de `data/raw` (ou `../raw`), aceitando tanto pastas extraídas (`microdados_Enade_<ano>_LGPD`) quanto arquivos `.zip`. Com o ambiente ativado:

```bash
python src/participacao.py
```

### Variáveis utilizadas

Todas as variáveis de participação estão no `arq3` de cada edição, ligadas ao `arq1` por `CO_CURSO`:

| Variável | Descrição no dicionário do INEP | Códigos considerados |
| -------- | ------------------------------- | -------------------- |
| `TP_PRES` | Tipo de presença no ENADE | `555` = Presente com resultado válido; `222` = Ausente; `444` = Ausente por dupla graduação; `334` = Eliminado; `556` / `888` = Resultado desconsiderado pela aplicadora |
| `TP_PR_GER` | Tipo de presença na prova (geral) | `555` = Participação com respostas válidas; `333` = Participação com **prova inteira em branco** (nota zero); `222` = Ausente |
| `TP_PR_OB_FG` e `TP_PR_OB_CE` | Presença nas partes **objetivas** de Formação Geral (FG) e Componente Específico (CE) | `555` = Respostas válidas; `333` = Caderno objetivo inteiro em branco |
| `TP_PR_DI_FG` e `TP_PR_DI_CE` | Presença nas partes **discursivas** de Formação Geral (FG) e Componente Específico (CE) | `555` = Respostas válidas; `333` = Caderno discursivo inteiro em branco (nota zero no componente discursivo) |
| `TP_SFG_D1`, `TP_SFG_D2` e `TP_SCE_D1` a `TP_SCE_D3` | Situação individual das 2 questões discursivas de FG e das 3 de CE (2008 a 2021) | `555` = Questão com resultado válido; `333` = Questão em branco (nota zero); `335` = Resposta nula; `336` = Divergente da temática |
| `DS_VT_ESC_OFG` e `DS_VT_ESC_OCE` | Vetores de escolhas nas questões objetivas de FG (8 itens) e CE (27 itens) | `A` a `E` = alternativa marcada; `.` = **questão em branco**; `*` = múltipla marcação |

Cuidados adotados:

- **Questões aplicáveis nos vetores objetivos (`2005`, `2008` e `2011`):** nas edições mais antigas, o vetor `DS_VT_ESC_OCE` continha posições de outras subáreas ou habilitações de Computação, identificadas por `Z` no vetor de acerto (`DS_VT_ACE_OCE`) ou por `N`/espaço no gabarito (`DS_VT_GAB_OCE_FIN`). O script contabiliza respostas em branco (`.`) apenas nas posições efetivamente aplicáveis a Ciência da Computação (`0`, `1`, `8` ou `9` no vetor de acerto).
- **Classificação do preenchimento da prova entre os presentes (`TP_PRES = 555`):** cada concluinte presente é classificado em três categorias mutuamente exclusivas: **(a) prova totalmente em branco** (`TP_PR_GER = 333`), **(b) prova parcialmente respondida** (`TP_PR_GER = 555`, mas com ao menos uma questão objetiva aplicável com `.` ou uma questão discursiva com código `333`), e **(c) prova 100% respondida** (todas as questões objetivas e discursivas respondidas).
- **Cruzamento com as notas sem violar a anonimização:** como `TP_PR_*` e `NT_*` estão no mesmo registro do `arq3`, é possível comparar diretamente a nota média de quem respondeu às questões discursivas com a de quem as deixou em branco. Nas edições amostrais (`2005` e `2008`), são filtrados apenas concluintes (`TP_INSCRICAO = 0`) e as médias de notas usam `PESO_AMOSTRA`, mantendo correspondência exata com a seção de desempenho acadêmico.

### Série histórica da Unifor (2005 a 2021)

**Presença e participação geral entre os inscritos da Unifor**

| Edição | Inscritos | Presentes (`TP_PRES=555`) | % Presentes | Ausentes (`TP_PRES=222`) | % Ausentes | Com resposta válida (`TP_PR_GER=555`) | Prova inteira em branco (`TP_PR_GER=333`) |
| -----: | --------: | ------------------------: | ----------: | -----------------------: | ---------: | ------------------------------------: | ----------------------------------------: |
| 2005 | 31 | 22 | 71,0% | 9 | 29,0% | 22 (71,0% dos inscritos) | 0 (0,0%) |
| 2008 | 50 | 42 | 84,0% | 8 | 16,0% | 41 (82,0% dos inscritos) | 1 (2,4% dos presentes) |
| 2011 | 72 | 49 | 68,1% | 23 | 31,9% | 48 (66,7% dos inscritos) | 1 (2,0% dos presentes) |
| 2014 | 43 | 32 | 74,4% | 11 | 25,6% | 32 (74,4% dos inscritos) | 0 (0,0%) |
| 2017 | 78 | 67 | 85,9% | 11 | 14,1% | 67 (85,9% dos inscritos) | 0 (0,0%) |
| 2021 | 94 | 67 | 71,3% | 27 | 28,7% | 67 (71,3% dos inscritos) | 0 (0,0%) |

**Provas em branco por componente e preenchimento parcial (percentuais sobre os presentes da Unifor)**

| Edição | Presentes | Objetiva Formação Geral em branco | Objetiva Específica em branco | Discursiva Formação Geral toda em branco | Discursiva Específica toda em branco | Algum caderno discursivo todo em branco | Alguma questão objetiva em branco | Alguma questão discursiva em branco | Prova parcial | Prova 100% respondida |
| -----: | --------: | --------------------------------: | ----------------------------: | ---------------------------------------: | -----------------------------------: | --------------------------------------: | --------------------------------: | ----------------------------------: | ------------: | --------------------: |
| 2005 | 22 | 1 (4,5%) | 3 (13,6%) | 9 (40,9%) | 0 (0,0%) | 9 (40,9%) | 6 (27,3%) | 9 (40,9%)* | 11 (50,0%)* | 11 (50,0%)* |
| 2008 | 42 | 1 (2,4%) | 1 (2,4%) | 18 (42,9%) | 16 (38,1%) | 22 (52,4%) | 9 (21,4%) | 31 (73,8%) | 31 (73,8%) | 10 (23,8%) |
| 2011 | 49 | 1 (2,0%) | 1 (2,0%) | 9 (18,4%) | 15 (30,6%) | 15 (30,6%) | 4 (8,2%) | 49 (100,0%) | 48 (98,0%) | 0 (0,0%) |
| 2014 | 32 | 0 (0,0%) | 0 (0,0%) | 6 (18,8%) | 6 (18,8%) | 8 (25,0%) | 1 (3,1%) | 20 (62,5%) | 20 (62,5%) | 12 (37,5%) |
| 2017 | 67 | 0 (0,0%) | 0 (0,0%) | 17 (25,4%) | 7 (10,4%) | 17 (25,4%) | 0 (0,0%) | 42 (62,7%) | 42 (62,7%) | 25 (37,3%) |
| 2021 | 67 | 0 (0,0%) | 0 (0,0%) | 11 (16,4%) | 8 (11,9%) | 12 (17,9%) | 2 (3,0%) | 42 (62,7%) | 42 (62,7%) | 25 (37,3%) |

\* Em 2005 a prova compartilhava questões discursivas numeradas de `D1` a `D18` entre subáreas de Computação; por isso o indicador discursivo daquela edição usa os cadernos `TP_PR_DI_FG` e `TP_PR_DI_CE`.

**Detalhamento por caderno da prova nas duas últimas edições (Unifor, 2017 e 2021)**

| Edição | Componente da prova | Presentes | Todas respondidas | Respondida parcialmente | Caderno inteiro em branco |
| -----: | ------------------- | --------: | ----------------: | ----------------------: | ------------------------: |
| 2017 | Objetiva de Formação Geral (8 questões) | 67 | 67 (100,0%) | 0 (0,0%) | 0 (0,0%) |
| 2017 | Objetiva Específica de Computação (27 questões) | 67 | 67 (100,0%) | 0 (0,0%) | 0 (0,0%) |
| 2017 | Discursiva de Formação Geral (2 questões) | 67 | 40 (59,7%) | 10 (14,9%) | 17 (25,4%) |
| 2017 | Discursiva Específica de Computação (3 questões) | 67 | 31 (46,3%) | 29 (43,3%) | 7 (10,4%) |
| 2021 | Objetiva de Formação Geral (8 questões) | 67 | 67 (100,0%) | 0 (0,0%) | 0 (0,0%) |
| 2021 | Objetiva Específica de Computação (27 questões) | 67 | 65 (97,0%) | 2 (3,0%) | 0 (0,0%) |
| 2021 | Discursiva de Formação Geral (2 questões) | 67 | 51 (76,1%) | 5 (7,5%) | 11 (16,4%) |
| 2021 | Discursiva Específica de Computação (3 questões) | 67 | 25 (37,3%) | 34 (50,7%) | 8 (11,9%) |

### Comparação agregada com o Ceará e o Brasil por rede (2017 e 2021)

Todas as comparações contrastam a **Unifor** com os demais cursos de Ciência da Computação agregados por rede (**públicas**, **privadas** e **geral** [junção de públicas + privadas]). **Em todos os grupos de privadas e geral, a Unifor é excluída do cálculo** para evitar sobreposição (`data/processed/participacao/participacao_resumo_grupos.csv`):

| Edição | Grupo | Cursos | IES | Inscritos | Presentes | % Presença | Prova geral em branco | Discursiva Formação Geral em branco | Discursiva Específica em branco | Algum caderno discursivo em branco | Prova parcial | Prova 100% respondida |
| -----: | ----- | -----: | --: | --------: | --------: | ---------: | --------------------: | ----------------------------------: | ------------------------------: | ---------------------------------: | ------------: | --------------------: |
| 2017 | **Unifor** | 1 | 1 | 78 | 67 | **85,9%** | 0,0% | **25,4%** | **10,4%** | **25,4%** | **62,7%** | **37,3%** |
| 2017 | CE públicas | 5 | 3 | 158 | 147 | 93,0% | 0,7% | 4,1% | 7,5% | 10,2% | 50,3% | 49,0% |
| 2017 | CE privadas | 4 | 4 | 138 | 121 | 87,7% | 0,0% | 19,0% | 20,7% | 28,9% | 61,2% | 38,8% |
| 2017 | CE geral | 9 | 7 | 296 | 268 | 90,5% | 0,4% | 10,8% | 13,4% | 18,7% | 55,2% | 44,4% |
| 2017 | Brasil públicas | 120 | 86 | 4.262 | 3.784 | 88,8% | 0,2% | 13,2% | 10,4% | 19,5% | 48,7% | 51,1% |
| 2017 | Brasil privadas | 190 | 151 | 5.846 | 4.640 | 79,4% | 0,1% | 9,9% | 26,0% | 30,1% | 63,6% | 36,3% |
| 2017 | Brasil geral | 310 | 237 | 10.108 | 8.424 | 83,3% | 0,2% | 11,4% | 19,0% | 25,3% | 56,9% | 42,9% |
| 2021 | **Unifor** | 1 | 1 | 94 | 67 | **71,3%** | 0,0% | **16,4%** | **11,9%** | **17,9%** | **62,7%** | **37,3%** |
| 2021 | CE públicas | 8 | 3 | 301 | 249 | 82,7% | 0,0% | 15,7% | 19,7% | 26,5% | 72,3% | 27,7% |
| 2021 | CE privadas | 5 | 5 | 94 | 68 | 72,3% | 0,0% | 10,3% | 16,2% | 22,1% | 64,7% | 35,3% |
| 2021 | CE geral | 13 | 8 | 395 | 317 | 80,3% | 0,0% | 14,5% | 18,9% | 25,6% | 70,7% | 29,3% |
| 2021 | Brasil públicas | 124 | 93 | 5.647 | 4.531 | 80,2% | 0,04% | 13,0% | 12,3% | 20,4% | 61,1% | 38,9% |
| 2021 | Brasil privadas | 204 | 153 | 6.992 | 5.395 | 77,2% | 0,1% | 14,0% | 27,0% | 32,0% | 70,9% | 29,0% |
| 2021 | Brasil geral | 328 | 246 | 12.639 | 9.926 | 78,5% | 0,1% | 13,5% | 20,3% | 26,7% | 66,4% | 33,5% |

**Testes estatísticos (Exato de Fisher bilateral, com correção de Holm para 30 comparações por edição):**

| Edição | Indicador | Comparação | Unifor | Grupo | Diferença (p.p.) | p bruto | p (Holm) | V de Cramér |
| -----: | --------- | ---------- | -----: | ----: | ---------------: | ------: | -------: | ----------: |
| 2017 | Discursiva de Formação Geral em branco | Unifor × CE públicas | 25,4% | 4,1% | +21,3 | **< 0,001** | **< 0,001** | 0,32 |
| 2017 | Discursiva de Formação Geral em branco | Unifor × Brasil privadas | 25,4% | 9,9% | +15,5 | **< 0,001** | **0,007** | 0,06 |
| 2017 | Discursiva de Formação Geral em branco | Unifor × Brasil geral | 25,4% | 11,4% | +14,0 | **0,001** | **0,040** | 0,04 |
| 2017 | Discursiva Específica em branco | Unifor × Brasil privadas | 10,4% | 26,0% | −15,5 | **0,003** | 0,076 | 0,04 |
| 2017 | Discursiva de Formação Geral em branco | Unifor × CE geral | 25,4% | 10,8% | +14,6 | **0,005** | 0,119 | 0,17 |
| 2017 | Algum caderno discursivo em branco | Unifor × CE públicas | 25,4% | 10,2% | +15,2 | **0,007** | 0,163 | 0,20 |
| 2017 | Discursiva de Formação Geral em branco | Unifor × Brasil públicas | 25,4% | 13,2% | +12,2 | **0,010** | 0,235 | 0,05 |
| 2017 | Prova parcial ou em branco | Unifor × Brasil públicas | 62,7% | 48,9% | +13,8 | **0,027** | 0,614 | 0,04 |
| 2021 | Discursiva Específica em branco | Unifor × Brasil privadas | 11,9% | 27,0% | −15,1 | **0,005** | 0,151 | 0,04 |
| 2021 | Algum caderno discursivo em branco | Unifor × Brasil privadas | 17,9% | 32,0% | −14,1 | **0,012** | 0,352 | 0,03 |
| 2021 | Presença no exame | Unifor × CE públicas | 71,3% | 82,7% | −11,5 | **0,018** | 0,515 | 0,12 |
| 2021 | Presença no exame | Unifor × Brasil públicas | 71,3% | 80,2% | −9,0 | **0,037** | 0,993 | 0,03 |

Em negrito, valores-p menores que 0,05. Todos os 60 resultados detalhados constam em `data/processed/participacao/participacao_testes_comparacao.csv`.

### Impacto da entrega de discursivas em branco na nota geral (`NT_GER`) no Ceará

Como o caderno discursivo representa 40% da nota de Formação Geral (`NT_FG`) e 15% da nota de Componente Específico (`NT_CE`), entregar um caderno discursivo em branco atribui nota zero a essa parcela. A tabela abaixo compara a nota geral média (`NT_GER`) em **2021** segundo o preenchimento dos cadernos discursivos nos grupos do Ceará (`data/processed/participacao/participacao_impacto_notas_grupos.csv`):

| Grupo no Ceará (ENADE 2021) | Respondeu aos 2 cadernos discursivos (`n` / `NT_GER`) | Deixou ≥ 1 caderno discursivo em branco (`n` / `NT_GER`) | Diferença na nota geral (`NT_GER`) | Média de todos os presentes com nota válida (`n` / `NT_GER`) | Perda na média do grupo causada pelos cadernos em branco |
| --------------------------- | ----------------------------------------------------: | -------------------------------------------------------: | ---------------------------------: | -----------------------------------------------------------: | -------------------------------------------------------: |
| **Unifor** | n = 55 → **42,83** | n = 12 → **30,42** | −12,41 pts | n = 67 → **40,61** | −2,22 pts |
| CE públicas | n = 183 → 38,83 | n = 66 → 32,43 | −6,40 pts | n = 249 → 37,13 | −1,70 pts |
| CE privadas | n = 53 → 39,48 | n = 15 → 34,84 | −4,64 pts | n = 68 → 38,45 | −1,03 pts |
| CE geral | n = 236 → 38,97 | n = 81 → 32,88 | −6,09 pts | n = 317 → 37,41 | −1,56 pts |

Na série histórica da **Unifor** (`2005` a `2021`), o impacto de deixar ao menos um caderno discursivo em branco foi consistente em todas as edições:
- **2005:** 45,57 (respondeu aos 2 cadernos, $n=13$) vs. 31,12 (algum caderno em branco, $n=9$) → média oficial 39,66 (−5,91 pts).
- **2008:** 48,52 ($n=20$) vs. 32,63 ($n=22$) → média oficial 40,20 (−8,32 pts).
- **2011:** 50,10 ($n=34$) vs. 34,03 ($n=15$) → média oficial 45,18 (−4,92 pts).
- **2014:** 55,67 ($n=24$) vs. 42,65 ($n=8$) → média oficial 52,42 (−3,25 pts).
- **2017:** 49,27 ($n=50$) vs. 36,41 ($n=17$) → média oficial 46,01 (−3,26 pts).
- **2021:** 42,83 ($n=55$) vs. 30,42 ($n=12$) → média oficial 40,61 (−2,22 pts).

### Interpretação

- **Presença no exame (Pergunta 1):** historicamente, a presença dos concluintes da Unifor oscila entre **68,1% (2011)** e **85,9% (2017)**. Em **2017**, a presença da Unifor (**85,9%**) superou a média nacional geral (83,3%) e as privadas nacionais (79,4%), ficando próxima das privadas do Ceará (87,7%). Na edição de **2021** (realizada em contexto pós-pandemia), houve queda generalizada de presença em todo o país: na Unifor compareceram **67 dos 94 inscritos (71,3%)**, patamar praticamente idêntico ao das demais **privadas do Ceará (72,3%)**, mas inferior ao das **públicas do Ceará (82,7%)**, do **CE geral (80,3%)**, das **públicas do Brasil (80,2%)** e do **Brasil geral (78,5%)**.
- **Provas totalmente em branco vs. parcialmente respondidas (Pergunta 2):** desde **2014**, **nenhum estudante presente da Unifor entregou a prova inteira em branco** (ocorreu apenas para 1 aluno em 2008 e 1 em 2011), e quase 100% dos presentes preenchem todas as 35 questões objetivas (em 2021, 65 de 67 presentes responderam a todas as objetivas). O preenchimento parcial concentra-se nas **questões discursivas**:
  - Tanto em **2017** quanto em **2021**, exatamente **37,3%** dos presentes da Unifor responderam a 100% da prova e **62,7%** deixaram ao menos uma questão em branco. Em **2021**, a taxa de provas 100% respondidas da Unifor (**37,3%**) superou todos os grupos do Ceará (**CE públicas com 27,7%**, **CE privadas com 35,3%** e **CE geral com 29,3%**), além de superar **Brasil privadas (29,0%)** e **Brasil geral (33,5%)**, ficando próxima apenas de **Brasil públicas (38,9%)**.
  - No caderno **Discursivo de Formação Geral** (2 questões), a Unifor tinha **25,4%** de abandono total em 2017 (diferença estatisticamente significativa após Holm contra CE públicas, Brasil privadas e Brasil geral), mas reduziu essa taxa para **16,4%** em 2021, alinhando-se a CE públicas (15,7%), CE geral (14,5%) e Brasil geral (13,5%).
  - No caderno **Discursivo Específico de Computação** (3 questões), a Unifor apresenta historicamente **menor abandono total do caderno** do que as demais redes do estado e do país: em **2021**, apenas **11,9%** dos presentes da Unifor deixaram o caderno discursivo específico inteiro em branco, contra **19,7% em CE públicas**, **16,2% em CE privadas**, **18,9% em CE geral**, **27,0% em Brasil privadas** ($p = 0,005$) e **20,3% em Brasil geral**.
- **Efeito nas notas do curso no Ceará:** em 2021, considerando todos os presentes com nota válida, a média geral da Unifor (**40,61**) superou todas as agregações do Ceará (**CE públicas com 37,13**, **CE privadas com 38,45** e **CE geral com 37,41**). Quando se observam apenas os estudantes que responderam aos dois cadernos discursivos, a média da Unifor sobe para **42,83** (contra **30,42** dos 12 alunos que deixaram algum caderno discursivo em branco).

Possíveis encaminhamentos para a coordenação:

- **Foco na resolução das questões discursivas na preparação para o ENADE:** como quase 100% dos presentes já respondem a todas as questões objetivas, o ganho mais rápido e direto de nota para a Unifor está em reduzir os 17,9% de alunos que deixam cadernos discursivos inteiros em branco e os 50,7% que deixam 1 ou 2 discursivas específicas sem resposta. Orientar os concluintes sobre o peso das discursivas (40% na Formação Geral e 15% no Componente Específico) pode recuperar de 2 a 3 pontos na média geral do curso.
- **Redução da abstenção no dia do exame:** como a presença da Unifor em 2021 (71,3%) acompanhou as privadas do estado (72,3%) mas ficou cerca de 11 pontos percentuais abaixo das públicas do Ceará (82,7%), ações de acompanhamento junto aos concluintes (especialmente os que trabalham 40h semanais) ajudam a elevar o comparecimento.

Limitações:

- Os estudantes ausentes (`TP_PRES = 222`) não têm nota nem respostas de prova; não é possível saber se teriam desempenho superior ou inferior ao dos presentes.
- A diferença de nota entre quem responde e quem deixa as discursivas em branco combina dois efeitos que os microdados não permitem separar: a perda mecânica dos pontos da questão em branco (nota zero no item) e a possibilidade de que estudantes com maior domínio do conteúdo também tenham maior propensão a responder às questões abertas.

Os arquivos e gráficos gerados ficam em `data/processed/participacao/`: `participacao_historico_unifor.csv`, `participacao_resumo_grupos.csv`, `participacao_detalhe_componentes_grupos.csv`, `participacao_testes_comparacao.csv`, `participacao_impacto_notas_grupos.csv`, `situacao_presenca_2017.png`, `situacao_presenca_2021.png`, `participacao_comparacao_grupos_2017.png`, `participacao_comparacao_grupos_2021.png`, `participacao_evolucao_comparativa.png`, `participacao_preenchimento_discursivas_2021.png` e `participacao_impacto_notas_grupos_2021.png`.

