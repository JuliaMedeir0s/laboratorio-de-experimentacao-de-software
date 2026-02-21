# Laboratório 01 — Características de repositórios populares (GitHub)

Este laboratório investiga características de repositórios open-source populares no GitHub, analisando idade, contribuição externa, releases, frequência de atualização, linguagem e taxa de issues fechadas.

**Repositório da disciplina:** laboratorio-de-experimentacao-de-software  
**Equipe:** Júlia Mederios e Thiago Laass

---

## Objetivo

Coletar dados dos **1.000 repositórios com maior número de estrelas no GitHub** e responder às questões de pesquisa (RQs) por meio de estatísticas descritivas (principalmente **mediana**) e contagens por categoria.

---

## Questões de Pesquisa (RQs) e Métricas

### RQ01 — Sistemas populares são maduros/antigos?
- **Métrica:** idade do repositório (a partir de `createdAt`).

### RQ02 — Sistemas populares recebem muita contribuição externa?
- **Métrica:** total de pull requests aceitas.  
- **Decisão de implementação:** considerar **PRs aceitas = PRs com estado `MERGED`** (`pullRequests(states: MERGED).totalCount`).

### RQ03 — Sistemas populares lançam releases com frequência?
- **Métrica:** total de releases (`releases.totalCount`).

### RQ04 — Sistemas populares são atualizados com frequência?
- **Métrica:** tempo desde a última atualização (a partir de `updatedAt`).

### RQ05 — Sistemas populares são escritos nas linguagens mais populares?
- **Métrica:** linguagem primária (`primaryLanguage.name`).

### RQ06 — Sistemas populares possuem alto percentual de issues fechadas?
- **Métrica:** razão entre issues fechadas e total:
  - total: `issues.totalCount`
  - fechadas: `issues(states: CLOSED).totalCount`
  - razão: `closed / total`

### (BÔNUS) RQ07 — Linguagens mais populares impactam PRs, releases e atualização?
Comparar **RQ02**, **RQ03** e **RQ04** por linguagem (ex.: top linguagens por frequência).

---

## Estrutura de Pastas do Lab

```
lab01/
├─ README.md
├─ docs/
│ ├─ enunciado.pdf
│ └─ relatorio/
│ ├─ rascunho.md
│ └─ final.pdf
├─ src/
│ ├─ main.py
│ ├─ github_graphql.py
│ ├─ coleta.py
│ └─ analise.py
├─ data/
│ ├─ raw/ # respostas brutas (json/csv)
│ └─ processed/ # dados tratados (csv final)
└─ outputs/
├─ tabelas/
└─ graficos/
```

---

## Metodologia (resumo)

1. Consultar a **GitHub GraphQL API** usando autenticação via token.
2. Buscar os repositórios ordenado por estrelas.
3. Paginar resultados até atingir **1000 repositórios**.
4. Persistir os dados brutos e gerar um **CSV** com as colunas necessárias.
5. Calcular métricas derivadas:
   - idade do repositório,
   - total de pull requests aceitas,
   - total de releases,
   - tempo desde última atualização,
   - linguagem primária,
   - razão de issues fechadas.
6. Produzir estatísticas descritivas:
   - **mediana** por RQ,
   - contagem por categoria (linguagem).

---

## Como reproduzir

---

## Colunas esperads no dataset

---

## Resultados
- RQ01 (idade, mediana): 
- RQ02 (PRs merged, mediana): 
- RQ03 (releases, mediana): 
- RQ04 (dias desde update, mediana): 
- RQ05 (linguagens mais comuns): 
- RQ06 (ratio issues fechadas, mediana): 
