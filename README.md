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
