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

**Dataset resultante:** 6.686 PRs de 200 repositórios (5.118 MERGED / 1.568 CLOSED)

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

*(A ser preenchido na Sprint 3, após a análise e visualização dos dados.)*

---

## 4. Discussão

*(A ser preenchido na Sprint 3, contrastando os resultados com as hipóteses apresentadas na Seção 1.)*
