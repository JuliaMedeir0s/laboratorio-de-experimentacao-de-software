# Relatório Inicial — Lab 01

## 1. Introdução
Este relatório inicial apresenta o planejamento da investigação sobre repositórios open-source populares no GitHub.
O estudo considera os 1.000 repositórios com maior número de estrelas para analisar maturidade, contribuição externa, releases, atualização, linguagem e resolução de issues.
A análise será conduzida por estatísticas descritivas, priorizando mediana para variáveis numéricas e contagens para variáveis categóricas.

## 2. Hipóteses de Pesquisa (RQ01–RQ06)
**RQ01 — Sistemas populares são maduros/antigos?**
Hipótese: repositórios mais populares tendem a ser mais antigos, por terem maior tempo de consolidação.

**RQ02 — Sistemas populares recebem muita contribuição externa?**
Hipótese: projetos populares apresentam maior volume de contribuições externas, observado pelo número de PRs aceitas (MERGED).

**RQ03 — Sistemas populares lançam releases com frequência?**
Hipótese: repositórios populares mantêm ciclos de release mais ativos.

**RQ04 — Sistemas populares são atualizados com frequência?**
Hipótese: projetos populares têm menor tempo desde a última atualização.

**RQ05 — Sistemas populares são escritos nas linguagens mais populares?**
Hipótese: linguagens amplamente adotadas aparecem com maior frequência entre os repositórios analisados.

**RQ06 — Sistemas populares possuem alto percentual de issues fechadas?**
Hipótese: projetos populares apresentam maior proporção de issues fechadas.

## 3. Metodologia
Este estudo tem caráter quantitativo e descritivo, com unidade de análise em nível de repositório.
A amostra foi composta pelos 1.000 repositórios mais estrelados no GitHub no momento da coleta, utilizando ordenação por estrelas na GitHub GraphQL API.

Os dados foram coletados com autenticação por token e paginação até completar os 1.000 registros. Para cada repositório, foram obtidos campos de identificação, datas de criação e atualização, linguagem principal, número de releases, número de pull requests aceitas (estado MERGED), total de issues e total de issues fechadas.

Após a coleta, os dados foram armazenados em formato bruto e submetidos a tratamento para análise: padronização de campos, cálculo de métricas derivadas (idade do repositório, tempo desde última atualização e proporção de issues fechadas) e verificação de valores ausentes.

Por fim, a análise estatística foi conduzida com medidas de tendência central para variáveis numéricas (medianas) e frequências absolutas para variáveis categóricas, de forma alinhada às questões RQ01–RQ06.

Data da coleta: 04/03/2026.

## 4. Métricas que serão analisadas
**Medianas (variáveis numéricas):**
- idade do repositório (RQ01);
- total de pull requests aceitas — estado MERGED (RQ02);
- total de releases (RQ03);
- tempo desde a última atualização, em dias (RQ04);
- razão de issues fechadas sobre total de issues (RQ06).

**Contagens (variáveis categóricas):**
- frequência de repositórios por linguagem primária (RQ05);
- contagem de registros com ausência de dados em campos relevantes.