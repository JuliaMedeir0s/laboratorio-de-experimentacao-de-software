# Lab03 — Caracterizando a atividade de code review no GitHub

## Objetivo

Analisar a atividade de code review em repositórios populares do GitHub, identificando variáveis que influenciam no merge de um Pull Request.

---

## Questões de Pesquisa

### A. Feedback Final das Revisões (status do PR)

| # | Questão |
|---|---------|
| RQ01 | Qual a relação entre o **tamanho** dos PRs e o feedback final das revisões? |
| RQ02 | Qual a relação entre o **tempo de análise** dos PRs e o feedback final das revisões? |
| RQ03 | Qual a relação entre a **descrição** dos PRs e o feedback final das revisões? |
| RQ04 | Qual a relação entre as **interações** nos PRs e o feedback final das revisões? |

### B. Número de Revisões

| # | Questão |
|---|---------|
| RQ05 | Qual a relação entre o **tamanho** dos PRs e o número de revisões realizadas? |
| RQ06 | Qual a relação entre o **tempo de análise** dos PRs e o número de revisões realizadas? |
| RQ07 | Qual a relação entre a **descrição** dos PRs e o número de revisões realizadas? |
| RQ08 | Qual a relação entre as **interações** nos PRs e o número de revisões realizadas? |

---

## Métricas Coletadas

| Dimensão | Métrica | Coluna no CSV |
|----------|---------|---------------|
| Tamanho | Número de arquivos alterados | `files_changed` |
| Tamanho | Linhas adicionadas | `lines_added` |
| Tamanho | Linhas removidas | `lines_removed` |
| Tempo de análise | Horas entre criação e fechamento/merge | `analysis_time_hours` |
| Descrição | Número de caracteres do corpo (markdown) | `body_length` |
| Interações | Número de participantes | `participants_count` |
| Interações | Número de comentários | `comments_count` |
| Variável dependente A | Status do PR | `status` (`MERGED` / `CLOSED`) |
| Variável dependente B | Número de revisões | `reviews_count` |

---

## Critérios de Seleção do Dataset

**Repositórios:**
- 200 repositórios mais populares do GitHub (por número de estrelas)
- Cada repositório deve ter pelo menos 100 PRs (MERGED + CLOSED)

**Pull Requests:**
- Status `MERGED` ou `CLOSED`
- Pelo menos 1 revisão (`reviews.totalCount >= 1`)
- Tempo de análise superior a 1 hora — exclui revisões automáticas por bots/CI

---

## Estrutura do Projeto

```
lab03/
├── src/
│   ├── github_graphql.py         cliente GraphQL reutilizável
│   ├── coletar_repositorios.py   sprint 1 — coleta os 200 repositórios
│   └── coletar_prs.py            sprint 1 — coleta os PRs com métricas
├── data/
│   ├── repos.csv                 lista dos repositórios selecionados
│   ├── raw/                      um CSV por repositório (checkpoint)
│   └── processed/
│       └── prs.csv               dataset consolidado final
├── outputs/
│   ├── graficos/                 gerado na sprint 3
│   └── tabelas/                  gerado na sprint 3
├── docs/
│   └── LABORATÓRIO 03 (...).pdf
└── requirements.txt
```

---

## Como Executar

### 1. Configuração

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto com seu token do GitHub:

```
GITHUB_TOKEN=ghp_...
```

### 2. Coletar repositórios

```bash
cd lab03/src
python coletar_repositorios.py
```

Gera `data/repos.csv` com os 200 repositórios mais populares que atendem ao critério de PRs.

### 3. Coletar PRs

```bash
python coletar_prs.py
```

Argumentos opcionais:

| Argumento | Padrão | Descrição |
|-----------|--------|-----------|
| `--max-prs N` | `100` | Máximo de PRs verificados por repositório |
| `--repo owner/name` | — | Processa somente um repositório específico |

Exemplo para coletar mais PRs por repositório:
```bash
python coletar_prs.py --max-prs 200
```

O script salva um CSV por repositório em `data/raw/` ao longo da execução. Se interrompido, retoma automaticamente da onde parou ao ser executado novamente.

---

## Decisões de Implementação

**Faixas de estrelas na busca de repositórios**
A API de busca do GitHub limita qualquer query a 1000 resultados. Para garantir os 200 repositórios mais populares sem perder resultados, a busca é dividida em faixas de estrelas (`>=100000`, `50000..99999`, etc.), cada uma com sua própria paginação.

**PAGE_SIZE = 50 na coleta de PRs**
A API GraphQL do GitHub calcula um custo por query com base na complexidade dos campos solicitados. Com campos aninhados como `participants`, `comments` e `reviews`, 50 nós por página mantém o custo dentro do limite sem comprometer a velocidade.

**Checkpoint por repositório**
Cada repositório é salvo individualmente em `data/raw/` logo após ser coletado. Isso permite retomar a coleta sem repetir repositórios já processados, importante dado o volume de dados (até 200 repos × 100+ PRs cada).

**`replace("Z", "+00:00")` no parsing de datas**
O Python anterior à versão 3.11 não suporta o sufixo `Z` (UTC) em `datetime.fromisoformat()`. A substituição explícita garante compatibilidade com versões mais antigas.
