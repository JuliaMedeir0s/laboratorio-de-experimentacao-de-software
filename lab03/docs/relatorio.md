# Lab03 — Caracterizando a atividade de code review no GitHub

## 1. Introdução e Hipóteses

A prática de code review é central no desenvolvimento de software open source. No GitHub, ela se materializa através de Pull Requests (PRs): um desenvolvedor submete código, revisores avaliam e o PR é aceito (MERGED) ou rejeitado (CLOSED). Entender quais fatores influenciam esse resultado e quantas revisões um PR acumula é o objetivo deste laboratório.

A seguir, apresentamos hipóteses informais sobre o que esperamos encontrar para cada questão de pesquisa.

### A. Feedback Final das Revisões (Status do PR)

**RQ01: Tamanho × Status**
PRs maiores (mais arquivos alterados, mais linhas adicionadas e removidas) tendem a ser CLOSED. Um PR grande é mais difícil de revisar, aumenta o risco de conflitos e costuma gerar resistência dos mantenedores, que preferem contribuições menores e focadas.

**RQ02: Tempo de análise × Status**
PRs que ficam abertos por mais tempo tendem a ser CLOSED. O tempo prolongado pode indicar que o PR levantou discussões sem consenso, ou que os revisores identificaram problemas que o autor não conseguiu resolver.

**RQ03: Descrição × Status**
PRs com descrição mais longa tendem a ser MERGED. Uma descrição detalhada facilita a compreensão da mudança, reduz perguntas dos revisores e demonstra cuidado do autor.

**RQ04: Interações × Status**
PRs com mais comentários e participantes tendem a ser CLOSED. Um volume alto de interações pode refletir controvérsia sobre a abordagem adotada ou a identificação de problemas que impedem o merge.

### B. Número de Revisões

**RQ05: Tamanho × Número de revisões**
PRs maiores recebem mais revisões. Mais código para analisar naturalmente gera mais ciclos de feedback antes de uma decisão final.

**RQ06: Tempo de análise × Número de revisões**
PRs com mais revisões levam mais tempo para serem fechados. Cada rodada de revisão adiciona um intervalo de espera entre o feedback e a resposta do autor.

**RQ07: Descrição × Número de revisões**
PRs com descrição mais detalhada recebem menos revisões. Uma boa documentação antecipa dúvidas e reduz a necessidade de iterações.

**RQ08: Interações × Número de revisões**
PRs com mais participantes e comentários acumulam mais revisões. Mais vozes no processo tendem a gerar mais rodadas de avaliação.

---

## 2. Metodologia

### 2.1 Criação do Dataset

O dataset foi construído a partir da API GraphQL do GitHub, seguindo os critérios do enunciado:

**Repositórios selecionados:**
- Os 200 repositórios mais populares do GitHub (por número de estrelas)
- Cada repositório possui pelo menos 100 PRs (MERGED + CLOSED)

**Pull Requests incluídos:**
- Status `MERGED` ou `CLOSED`
- Pelo menos 1 revisão registrada (`reviews.totalCount >= 1`)
- Tempo de análise superior a 1 hora, critério para excluir revisões automáticas por bots e ferramentas de CI/CD

**Dataset resultante:** 6.721 PRs de 200 repositórios (5.163 MERGED / 1.558 CLOSED)

### 2.2 Métricas Coletadas

| Dimensão | Métrica | Coluna |
|----------|---------|--------|
| Tamanho | Arquivos alterados | `files_changed` |
| Tamanho | Linhas adicionadas | `lines_added` |
| Tamanho | Linhas removidas | `lines_removed` |
| Tempo de análise | Horas entre criação e fechamento/merge | `analysis_time_hours` |
| Descrição | Caracteres no corpo do PR (markdown) | `body_length` |
| Interações | Número de participantes | `participants_count` |
| Interações | Número de comentários | `comments_count` |
| Dependente A | Status final | `status` |
| Dependente B | Número de revisões | `reviews_count` |

### 2.3 Análise Estatística

Para responder às questões de pesquisa, utilizaremos o **teste de correlação de Spearman** (ρ). A escolha se justifica porque:

- As métricas coletadas (número de arquivos, linhas, comentários, tempo) apresentam distribuições fortemente assimétricas — valores extremos são comuns em repositórios populares
- O teste de Spearman é baseado em ranks, sendo robusto a outliers e não exige que os dados sigam distribuição normal
- Pearson pressupõe linearidade e normalidade, o que raramente se verifica em dados de engenharia de software

Para a dimensão A (Status do PR), o status será codificado como variável binária: `MERGED = 1`, `CLOSED = 0`. A correlação com cada métrica contínua será calculada via Spearman.

A sumarização dos dados será feita por **medianas**, conforme recomendado pelo enunciado, por serem mais representativas que médias em distribuições assimétricas.

---

## 3. Resultados

Esta seção apresenta (i) estatísticas descritivas (medianas) e (ii) correlações de Spearman (ρ) para responder às questões de pesquisa.

### 3.1 Estatísticas descritivas (medianas)

| status   |    n |   median_files_changed |   median_lines_added |   median_lines_removed |   median_analysis_time_hours |   median_body_length |   median_participants_count |   median_comments_count |   median_reviews_count |
|:---------|-----:|-----------------------:|---------------------:|-----------------------:|-----------------------------:|---------------------:|----------------------------:|------------------------:|-----------------------:|
| MERGED   | 5163 |                      2 |                   21 |                      5 |                      22.8439 |                854   |                           2 |                       1 |                      2 |
| CLOSED   | 1558 |                      1 |                   16 |                      1 |                      89.3526 |                809.5 |                           2 |                       2 |                      1 |

Em termos de medianas, PRs MERGED tendem a ter mais revisões (2 vs 1) e são fechados/mergeados mais rapidamente (≈22,84h vs ≈89,35h). PRs CLOSED apresentam mediana maior de comentários (2 vs 1).

### 3.2 Correlação (Spearman) — Status do PR (RQ01–RQ04)

Codificamos `MERGED = 1` e `CLOSED = 0` e calculamos a correlação de Spearman entre cada métrica e o status final.

| x                   | y          |    n |   spearman_rho |   p_value |
|:--------------------|:-----------|-----:|---------------:|----------:|
| lines_removed       | status_bin | 6721 |       0.149342 |  0        |
| files_changed       | status_bin | 6721 |       0.128479 |  0        |
| lines_added         | status_bin | 6721 |       0.033272 |  0.006374 |
| body_length         | status_bin | 6721 |       0.024304 |  0.046328 |
| participants_count  | status_bin | 6721 |      -0.015485 |  0.204329 |
| comments_count      | status_bin | 6721 |      -0.093134 |  0        |
| analysis_time_hours | status_bin | 6721 |      -0.228404 |  0        |

Os resultados sugerem associação negativa entre tempo de análise e status (PRs com maior tempo tendem a fechar sem merge) e associação negativa entre comentários e status. Por outro lado, métricas de tamanho (arquivos/linhas) apresentam associação positiva (ainda que fraca/moderada), indicando que PRs maiores não necessariamente são rejeitados no dataset.

### 3.3 Correlação (Spearman) — Número de revisões (RQ05–RQ08)

Calculamos a correlação de Spearman entre cada métrica e `reviews_count`.

| x                   | y             |    n |   spearman_rho |   p_value |
|:--------------------|:--------------|-----:|---------------:|----------:|
| participants_count  | reviews_count | 6721 |       0.348768 |  0        |
| lines_added         | reviews_count | 6721 |       0.296233 |  0        |
| comments_count      | reviews_count | 6721 |       0.275981 |  0        |
| files_changed       | reviews_count | 6721 |       0.256395 |  0        |
| lines_removed       | reviews_count | 6721 |       0.16609  |  0        |
| body_length         | reviews_count | 6721 |       0.1519   |  0        |
| analysis_time_hours | reviews_count | 6721 |       0.037589 |  0.002055 |

Observa-se correlação positiva mais forte entre número de participantes e número de revisões, e correlações positivas (moderadas) entre métricas de tamanho/interações e revisões.

---

## 4. Discussão

Nesta seção, contrastamos os resultados com as hipóteses propostas na Seção 1.

- **RQ01 (Tamanho × Status):** a hipótese previa que PRs maiores tenderiam a ser CLOSED. No entanto, as correlações entre tamanho e status foram **positivas** (arquivos e linhas adicionadas/removidas), sugerindo que, no conjunto analisado, PRs maiores estão levemente mais associados a MERGE. Uma explicação plausível é que PRs maiores podem representar mudanças relevantes (features/refactors) que recebem mais atenção e revisão até serem integradas.

- **RQ02 (Tempo de análise × Status):** a hipótese é **corroborada**. A correlação entre `analysis_time_hours` e status foi negativa (ρ ≈ -0,23), e as medianas indicam que PRs CLOSED demoram bem mais para encerrar do que PRs MERGED.

- **RQ03 (Descrição × Status):** a hipótese previa que descrições maiores tenderiam a MERGE. O resultado foi **muito fraco**, porém positivo (ρ ≈ 0,024), sugerindo que descrição pode ajudar, mas o efeito é pequeno no agregado.

- **RQ04 (Interações × Status):** a hipótese previa que mais interações tenderiam a CLOSED. O resultado foi misto: `comments_count` correlacionou negativamente com status (consistente com a hipótese), enquanto `participants_count` não apresentou correlação estatisticamente relevante.

- **RQ05–RQ08 (Métricas × Número de revisões):** os resultados indicam que **interações** (principalmente `participants_count`) e **tamanho** (`lines_added`, `files_changed`) têm associação positiva com o número de revisões, como esperado. O tempo de análise teve correlação positiva, mas muito pequena, sugerindo que o tempo total de vida do PR é influenciado por fatores além do número de revisões (ex.: disponibilidade de mantenedores, prioridades do projeto, mudanças solicitadas fora de ciclos de review).

Os resultados completos (CSV/MD) e gráficos estão em `outputs/tabelas/` e `outputs/graficos/`.
