# Dashboard BI - Análise de Dependências Vulneráveis em Projetos Node.js

**Data de Geração:** 20/05/2026  **Dataset:** ** 9.982 repositórios Node.js públicos  **Período:** ** Snapshot de maio de 2026  **Ferramenta:** OSV + NVD para mapeamento de CVEs

---

## Nota sobre a ferramenta de BI

O enunciado do laboratório pede um dashboard construído em **Power BI**, **Tableau** ou **Looker Studio**.

Este relatório em Markdown e os artefatos em `outputs/` servem como **documentação** e referência.
Para montar o dashboard em BI a partir dos CSVs, use `lab04/bi/README.md`.

---

## 1. Caracterização do Dataset

### 1.1. Visão Geral

| Métrica | Valor |
|---|---|
| Total de repositórios analisados | 9.982 |
| Repositórios com vulnerabilidades detectadas | 5.616 (56,26%) |
| Repositórios sem vulnerabilidades | 4.366 (43,74%) |
| Dependências vulneráveis (total) | 61.977 |
| Dependências diretas (total) | 144.348 |
| Versões resolvidas (total) | 707.977 |
| CVEs associados (total) | 137.995 |

### 1.2. Distribuição de Bots de Automação

| Ferramenta | Repositórios | Percentual | Taxa de Vulnerabilidade |
|---|---|---|---|
| **Sem bot** | 9.261 | 92,78% | 56,67% |
| **Dependabot** | 484 | 4,85% | 49,59% |
| **Renovate** | 180 | 1,80% | 50,56% |
| **Snyk** | 57 | 0,57% | 64,91% |

### 1.3. Distribuição de Dependências

| Métrica | Valor |
|---|---|
| **Dependências Diretas (Total)** | 144.348 |
| **Versões Resolvidas** | 707.977 |
| **Dependências Vulneráveis** | 61.977 |
| **Taxa de Vulnerabilidade** | 42,94% |

### 1.4. Estatísticas Descritivas por Grupo

| Métrica | Com Vulnerabilidade | Sem Vulnerabilidade |
|---|---|---|
| **Dependências diretas/repo** | 16,88 | 11,35 |
| **Versões resolvidas/repo** | 122,02 | 5,2 |
| **Dependências vulneráveis/repo** | 11,04 | 0 |
| **CVEs/repo** | 24,57 | 0 |

---

## 2. RQ1: Frequência de Dependências Vulneráveis

### Pergunta de Pesquisa

**Qual é a frequência de dependências vulneráveis em projetos Node.js hospedados no GitHub?**

### Insight Principal

**56,26% dos projetos analisados contém pelo menos uma vulnerabilidade.**

### Estatísticas Principais

| Métrica | Valor |
|---|---|
| **Taxa de Repos Vulneráveis** | 56,26% |
| **Dependências Vulneráveis/Repo (média)** | 11,04 |
| **CVEs por Repositório Vulnerável** | 24,57 |
| **CVEs por Dependência Vulnerável** | 2,23 |

### Visualizações

- Taxa de Vulnerabilidade por Grupo (`bar_repo_vulnerability_rate.png`)
- Distribuição de CVEs por Repositório (`boxplot_cves_by_group.png`)

---

## 3. RQ2: Nível de Severidade das Vulnerabilidades

### Pergunta de Pesquisa

**Qual é o nível de severidade das vulnerabilidades encontradas e qual a distribuição proporcional entre os níveis de risco?**

### Insight Principal

**86,93% dos CVEs têm severidade MEDIUM ou superior.**

### Distribuição de Severidade

| Nível de Severidade | Contagem | Percentual | Risco Operacional |
|---|---|---|---|
| **MEDIUM** | 58.192 | 42,17% | Médio prazo |
| **HIGH** | 50.979 | 36,94% | Imediato |
| **LOW** | 10.869 | 7,88% | Monitorar |
| **CRITICAL** | 10.789 | 7,82% | Imediato |
| **UNKNOWN** | 7.166 | 5,19% | Monitorar |

### Concentração de Risco

| Classificação | Severidade | % do Total |
|---|---|---|
| **HIGH + CRITICAL** | Imediato | 44,76% |
| **MEDIUM** | Médio prazo | 42,17% |
| **LOW + UNKNOWN** | Monitorar | 13,07% |

### Distribuição Normalizada com/sem Dependabot

| Severity | Com Dependabot | Sem Dependabot | Diferença |
|---|---|---|---|
| **LOW** | 10,58% | 7,76% | 2,82 p.p. |
| **MEDIUM** | 41,07% | 42,22% | -1,15 p.p. |
| **HIGH** | 38,88% | 36,86% | 2,02 p.p. |
| **CRITICAL** | 4,24% | 7,97% | -3,73 p.p. |
| **UNKNOWN** | 5,23% | 5,19% | 0,04 p.p. |

### Visualizações

- Distribuição Percentual de Severidade (100% Stacked) (`stacked_bar_severity_distribution.png`)
- Heatmap de Severidade por Grupo (`heatmap_severity_distribution.png`)

---

## 4. RQ3: Impacto da Automação (Dependabot, Renovate, Snyk)

### Pergunta de Pesquisa

**A utilização de ferramentas de automação está associada a menor incidência de vulnerabilidades?**

### Comparação Direta (Dependabot vs Sem Dependabot)

| Métrica | Com Dependabot | Sem Dependabot | Razão (Sem/Com) | Benefício |
|---|---|---|---|---|
| **Taxa de repos vulneráveis** | 49,59% | 56,60% | 1,14x | ✅ -7,01 p.p. |
| **CVEs/repo** | 11,50 | 13,94 | 1,21x | ✅ -17,52% |
| **Dependências vulner./repo** | 5,63 | 6,24 | 1,11x | ✅ -9,78% |
| **CVEs por dep. vulnerável** | 2,04 | 2,23 | 1,09x | ✅ -8,58% |

### Comparação com Outras Ferramentas

| Ferramenta | Repos | Taxa Vulner. | CVEs/Repo | Status |
|---|---|---|---|---|
| **Sem bot** | 9.261 | 56,67% | 13,95 | Baseline |
| **Dependabot** | 484 | 49,59% | 11,5 | ✅ Menor incidência |
| **Renovate** | 180 | 50,56% | 10,67 | ✅ Menor incidência |
| **Snyk** | 57 | 64,91% | 23,53 | ⚠️ Amostra pequena |

### Visualizações

- Comparação Normalizada de Risco (`bar_normalized_comparison.png`)
- Atividade de Correção - Versões Resolvidas (`bar_activity_difference_vs_none.png`)
- Scatter Plot - Dependências vs CVEs (`scatter_dependencies_vs_cves.png`)

---

## 5. Recomendações (síntese)

- Curto prazo: auditar dependências, adotar automação, priorizar HIGH/CRITICAL.
- Médio prazo: automatizar updates e impor políticas em CI/CD.
- Longo prazo: monitoramento contínuo e redução de acoplamento de dependências.
