# 📝 Relatório Técnico de Laboratório

## Informações do grupo
- **🎓 Curso:** Engenharia de Software
- **📘 Disciplina:** Laboratório de Experimentação de Software
- **🗓 Período:** 6° Período
- **👥 Membros do Grupo:** Júlia Medeiros e Thiago Laass

---

## 1 Introdução

### 1.1 Contextualização
Este laboratório analisa características de repositórios open-source populares no GitHub, tomando como base os 1000 repositórios de código com maior número de estrelas no momento da coleta. O objetivo é caracterizar esses projetos a partir de indicadores de maturidade, atividade recente, histórico de pull requests aceitas, releases, linguagem principal e resolução de issues.

### 1.2 Problema foco do experimento
Repositórios populares são, de fato, mais maduros e bem mantidos? Em particular, deseja-se investigar se esses projetos tendem a ser mais antigos, se acumulam volume relevante de pull requests aceitas, se apresentam histórico expressivo de releases, se permanecem ativos ao longo do tempo e se mantêm boa taxa de fechamento de issues.

### 1.3 Questões de Pesquisa (RQs)
- **RQ01:** Sistemas populares são maduros/antigos?
- **RQ02:** Sistemas populares apresentam alto volume de pull requests aceitas?
- **RQ03:** Sistemas populares apresentam histórico expressivo de releases?
- **RQ04:** Sistemas populares são atualizados com frequência?
- **RQ05:** Sistemas populares são escritos nas linguagens mais populares?
- **RQ06:** Sistemas populares possuem alto percentual de issues fechadas?
> (Opcional) **RQ07 (bônus):** Comparar RQ02–RQ04 por linguagem.

### 1.4 Hipóteses
- **H01 (RQ01):** Repositórios populares tendem a ser mais antigos.
- **H02 (RQ02):** Repositórios populares apresentam alto volume de PRs aceitas.
- **H03 (RQ03):** Repositórios populares possuem número elevado de releases.
- **H04 (RQ04):** Repositórios populares são atualizados frequentemente.
- **H05 (RQ05):** Linguagens populares (Python/JS/TS) são mais frequentes.
- **H06 (RQ06):** Repositórios populares têm alta taxa de issues fechadas.

### 1.5 Objetivos
**Objetivo principal:** caracterizar repositórios populares do GitHub por métricas de processo e produto, respondendo às RQ01–RQ06 com estatísticas descritivas.

**Objetivos específicos:**
- Coletar dados dos 1000 repositórios de código mais estrelados por meio da GitHub GraphQL API
- Derivar métricas como idade do repositório, dias desde o último push e percentual de issues fechadas
- Calcular medianas para as RQs numéricas e contagens por linguagem principal
- Produzir tabelas e gráficos para apoiar a interpretação e a discussão dos resultados

---

## 2 Metodologia
### 2.1 Passo a passo do experimento
O experimento foi dividido em quatro etapas principais: (1) coleta dos dados, (2) transformação e organização do dataset, (3) cálculo de métricas derivadas e (4) análise estatística com apoio de visualizações. Essa sequência foi adotada para responder às RQ01–RQ06 de forma reprodutível e alinhada às métricas disponíveis na GitHub GraphQL API.

#### Etapas
1. Definição das questões de pesquisa e das métricas correspondentes.
2. Preparação do ambiente de execução em Python, com dependências declaradas em `requirements.txt`.
3. Configuração do token de acesso do GitHub em arquivo `.env`, mantendo o valor sensível fora do repositório e documentando o formato em `.env.example`.
4. Coleta dos repositórios via GitHub GraphQL API, usando ordenação por estrelas e paginação por cursor.
5. Persistência dos dados em duas camadas: JSON bruto para rastreabilidade e CSV processado para análise.
6. Conversão e tratamento dos dados coletados, incluindo padronização de datas e cálculo de métricas derivadas.
7. Geração de estatísticas descritivas e visualizações para interpretação dos resultados.

### 2.2 Materiais utilizados
- GitHub GraphQL API com autenticação por token pessoal.
- Ambiente virtual Python (`venv`) para isolar dependências.
- Arquivos de apoio à reprodutibilidade: `.env.example` para documentar a variável `GITHUB_TOKEN` e `.gitignore` para evitar vazamento de credenciais.
- Dependências instaladas via `requirements.txt`, incluindo bibliotecas para configuração do ambiente, tratamento de dados e geração de gráficos.
- Artefatos gerados pela coleta e análise: JSON bruto, CSV processado, tabelas e gráficos.

### 2.3 Métodos utilizados
A coleta foi feita com um script próprio utilizando a GitHub GraphQL API. A busca inicial foi configurada para retornar repositórios ordenados por estrelas (`sort:stars`), em conformidade com o objetivo de estudar projetos populares. Como o experimento exigia repositórios de código, foi adotado como critério de aceite a presença de linguagem principal definida (`primaryLanguage != null`).

Durante a execução, observou-se uma limitação prática da API de busca do GitHub: a paginação não permite percorrer indefinidamente os resultados de uma única consulta, o que dificultava alcançar 1000 repositórios aceitos quando se filtrava apenas projetos com linguagem principal definida. Para contornar esse problema, a busca foi dividida em faixas de estrelas, como `stars:50000..99999` e `stars:20000..49999`, acumulando resultados de múltiplas consultas até completar a amostra desejada.

Em cada faixa, a coleta utilizou paginação por cursor com `pageInfo.endCursor` e `hasNextPage`. Os candidatos retornados pelo search eram então enriquecidos por meio de queries GraphQL compostas com aliases (`repo0`, `repo1`, etc.), executadas em lotes menores. A saída final da coleta foi persistida em dois formatos: um JSON bruto, voltado à auditoria e rastreabilidade, e um CSV processado com uma linha por repositório, contendo colunas como `stars`, `created_at`, `pushed_at`, `primary_language`, `releases_total`, `prs_merged_total`, `issues_total` e `issues_closed_total`.

### 2.4 Decisões
Após a coleta, as datas em formato ISO 8601 foram convertidas para `datetime`, permitindo o cálculo das métricas derivadas. As principais métricas calculadas foram `repo_age_days`, `days_since_push` e `issues_closed_ratio`. No caso da razão de issues fechadas, foi necessário tratar explicitamente situações com `issues_total = 0`, evitando divisão por zero.

As decisões operacionais mais relevantes foram as seguintes:
- **PRs aceitas = PRs com estado `MERGED`.** Essa definição foi usada como proxy de colaboração aceita pelo projeto.
- **Última atualização = `pushedAt`.** Essa escolha foi feita porque `pushedAt` representa atividade real de código, ao contrário de `updatedAt`, que também pode refletir alterações apenas em metadados.
- **Amostra = 1000 repositórios de código.** Foram aceitos apenas repositórios com `primaryLanguage` definida.
- **Lotes conservadores de coleta.** O tamanho do batch foi mantido em valor reduzido para evitar falhas e timeout em queries muito grandes.
- **Estatística principal = mediana.** Essa opção foi adotada por ser mais robusta diante de distribuições assimétricas e presença de outliers.

Na etapa analítica, para as variáveis numéricas foram utilizadas mediana e estatísticas descritivas complementares, como percentis 25 e 75. Para a variável categórica de linguagem, foram calculadas contagens absolutas e percentuais. As visualizações incluíram gráficos de barras, histogramas, boxplots, dispersão em escala log-log e heatmap de correlação, com o objetivo de tornar visíveis padrões de concentração, cauda longa e possíveis associações entre métricas.

Entre as principais dificuldades enfrentadas, destacam-se o limite prático de resultados da busca do GitHub, a instabilidade de queries muito grandes e a forte assimetria das distribuições observadas. Esses problemas foram tratados, respectivamente, com a divisão da coleta em faixas de estrelas, a redução do tamanho dos lotes e o uso de medidas robustas e visualizações com escala log quando apropriado.

### 2.5 Métricas e suas unidades
- **RQ01:** maturidade do projeto, medida pela idade do repositório a partir de `created_at` (dias e anos).
- **RQ02:** volume de pull requests aceitas, medido por `prs_merged_total` (contagem).
- **RQ03:** histórico de releases, medido por `releases_total` (contagem).
- **RQ04:** atividade recente, medida pelo tempo desde o último push, calculado a partir de `pushed_at` (dias).
- **RQ05:** linguagem principal do repositório, representada por `primary_language` (categoria).
- **RQ06:** taxa de fechamento de issues, calculada como `issues_closed_total / issues_total` (proporção).

---

## 3 Visualização dos Resultados

### 3.1 Visualização tabular (tabelas)
- **Tabela A — Medianas por RQ:** (colar conteúdo de `tabela_mediana_rqs.csv`)
- **Tabela B — Top linguagens (Top 20):** (colar conteúdo de `tabela_linguagens_top20.csv`)
- (Opcional) **Tabela C — Estatísticas descritivas:** (p25, mediana, p75, min, max)

### 3.2 Visualização gráfica (figuras)
Sugestão de figuras (as que vocês já têm):
- Barras: Top 10 linguagens
- Histograma: idade dos repositórios
- Histograma: dias desde o último push (zoom 365)
- Boxplot: PRs merged (sem outliers ou escala log)
- (Opcional) Scatter log-log: stars vs PRs merged
- (Opcional) Heatmap: correlação entre métricas

---

## 4 Discussão dos resultados
### 4.1 Confronto com as Questões de Pesquisa
Para cada RQ, escrever 3 coisas:
- **resultado numérico (mediana / contagem)**
- **o que isso sugere**
- **se confirmou a hipótese**

**RQ01 — Maturidade/idade**
- Resultado: [mediana idade]  
- Interpretação: …  
- Hipótese: confirmada / parcial / refutada

**RQ02 — PRs aceitas**
- Resultado: [mediana PRs merged]  
- Interpretação: …  
- Hipótese: …

(... repetir até RQ06)

### 4.2 Insights (padrões observados)
- Distribuições assimétricas (cauda longa) em PRs, releases e stars
- Linguagens dominantes no top 1000
- Alta atividade recente (dias desde push concentrado em valores baixos)
- Boa taxa de fechamento de issues (mas com variação)

### 4.3 Comparações e estatísticas
- Comparar “miolo” vs outliers usando boxplot sem outliers e/ou escala log
- (Opcional) Comparar métricas por linguagem (bônus/RQ07)

---

## 5 Conclusão
### 5.1 Tomada de decisão (resultado conclusivo sucinto)
Com base nos resultados:
- Repositórios populares tendem a ser [maduros / ativos / bem mantidos] segundo as métricas analisadas.
- Principais evidências: [cite 2–3 números das medianas e 1 gráfico]

### 5.2 Sugestões futuras
- Fazer a RQ07 por linguagem
- Incluir outras métricas (ex.: forks, contributors, tamanho/LOC) se coletarem
- Analisar evolução temporal com séries mais detalhadas (por mês/ano)

### 5.3 Plus — relação com literatura (curto)
- Comparar os achados com relatórios empíricos/benchmarks (ex.: produtividade, cadência de releases, manutenção).
- Discutir se os resultados corroboram a ideia de que projetos populares têm maior maturidade e atividade.