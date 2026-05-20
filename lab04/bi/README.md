# Dashboard BI (Power BI / Tableau / Looker Studio)

O enunciado do Lab04 pede que o dashboard seja feito em uma ferramenta de BI (ex.: **Microsoft Power BI**, **Tableau** ou **Google Data Studio / Looker Studio**).

Este diretório contém **tabelas CSV prontas para importação** e um roteiro de como montar as páginas do dashboard para responder as RQs.

## 1) Gerar/atualizar as tabelas (CSV)

A partir do arquivo [lab04/dataset/ANALISE_RQ.md](../dataset/ANALISE_RQ.md), rode:

```bash
cd lab04
python3 prepare_bi_data.py
```

As tabelas serão geradas em [lab04/bi/tables](tables).

## 2) Arquivos (tabelas)

- [tables/dataset_overview.csv](tables/dataset_overview.csv)
- [tables/bots_distribution.csv](tables/bots_distribution.csv)
- [tables/rq1_repo_group_averages.csv](tables/rq1_repo_group_averages.csv)
- [tables/severity_distribution.csv](tables/severity_distribution.csv)
- [tables/severity_by_group_dependabot.csv](tables/severity_by_group_dependabot.csv)
- [tables/rq3_comparison_direct.csv](tables/rq3_comparison_direct.csv)
- [tables/rq3_tools_comparison.csv](tables/rq3_tools_comparison.csv)

## 3) Como montar o dashboard (recomendação de páginas)

### Página 1 — Caracterização do Dataset

Objetivo: caracterizar dataset completo e subgrupos.

Sugestão de visuais:
- **Cartões/KPIs** (dataset_overview):
  - Total de repositórios
  - % repos com vulnerabilidade
  - Total de CVEs
  - Total de dependências vulneráveis
- **Bar chart** (bots_distribution):
  - Eixo X: `tool`
  - Eixo Y: `repos` (ou `pct`)
- **Bar chart** (bots_distribution):
  - Eixo X: `tool`
  - Eixo Y: `taxa` (taxa de repos vulneráveis)

### Página 2 — RQ1 (Frequência)

Dados:
- `dataset_overview.csv`
- `rq1_repo_group_averages.csv`

Sugestão de visuais:
- **KPI**: taxa de repos vulneráveis (%).
- **Tabela**: médias por grupo (com vs sem vulnerabilidade).
- **Bar chart**: `metric` no eixo X, `with_vulnerability` no eixo Y (e/ou comparar com `without_vulnerability`).

### Página 3 — RQ2 (Severidade)

Dados:
- `severity_distribution.csv`
- `severity_by_group_dependabot.csv`

Sugestão de visuais:
- **Donut / Pie**: distribuição de severidade (severity_distribution).
- **100% stacked bar**: severidade por grupo (com vs sem Dependabot).

### Página 4 — RQ3 (Impacto do Dependabot)

Dados:
- `rq3_comparison_direct.csv`
- `rq3_tools_comparison.csv`

Sugestão de visuais:
- **Tabela**: comparação direta (com vs sem Dependabot).
- **Bar chart**: taxa de repos vulneráveis por ferramenta.
- **Bar chart**: `cves_per_repo` por ferramenta.

## 4) Exportar para entrega

- **Power BI**: `File -> Export -> PDF` (ou `Export -> PowerPoint` e salvar PDF).
- **Tableau**: `File -> Export as PDF`.
- **Looker Studio**: `File -> Download -> PDF`.

A entrega final deve incluir o **dashboard exportado em PDF**.

## 5) Observação importante

Os scripts/HTML gerados em `lab04/outputs/` são úteis como referência, mas o requisito do enunciado é que a entrega seja um dashboard feito em uma ferramenta de BI.
