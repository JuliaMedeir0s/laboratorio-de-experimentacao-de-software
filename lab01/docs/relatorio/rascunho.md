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

Os dados foram coletados com autenticação por token e paginação até completar os 1.000 registros. Para cada repositório, foram obtidos campos de identificação, datas de criação e atualização, linguagem principal, número de releases, número de pull requests aceitas, total de issues e total de issues fechadas.