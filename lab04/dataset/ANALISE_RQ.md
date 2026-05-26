# Análise de Dependências Vulneráveis em Projetos Node.js do GitHub (Dataset ampliado)

**Dataset:** 9.982 repositórios Node.js públicos  
**Período:** Snapshot de maio de 2026  
**Ferramenta:** OSV + NVD para mapeamento de CVEs

---

## RQ1: Qual é a frequência de dependências vulneráveis em projetos Node.js hospedados no GitHub?

### Taxas Absoluta e Normalizadas

| Métrica | Valor |
|---------|-------|
| **Total de repositórios analisados** | 9.982 |
| **Repositórios com vulnerabilidades detectadas** | 5.709 (57,19%) |
| **Repositórios sem vulnerabilidades** | 4.273 (42,81%) |
| **Dependências vulneráveis (total)** | 63.493 |
| **Dependências diretas (total)** | 144.137 |
| **Versões resolvidas (total)** | 703.056 |
| **CVEs associados (total)** | 137.987 |

### Análise Granular

#### Por Repositório (média por grupo)

| Métrica | Com Vulnerabilidade | Sem Vulnerabilidade |
|---------|-------------------|-------------------|
| **Dependências diretas/repo** | 16,74 | 11,37 |
| **Versões resolvidas/repo** | 120,83 | 3,10 |
| **Dependências vulneráveis/repo** | 11,12 | 0 |
| **CVEs/repo** | 24,17 | 0 |

#### Distribuição por Bot Detectado (by_dependency_bot)

| Tool | Repos | % | Repos Vulner. | Taxa | CVEs/Repo | Dependências Vulner./Repo |
|------|-------|------|---|------|-----------|--------|
| **Sem bot** | 8.964 | 89,80% | 5.117 | 57,08% | 13,75 | 6,25 |
| **Dependabot** | 524 | 5,25% | 290 | 55,34% | 11,70 | 5,99 |
| **CodeQL** | 162 | 1,62% | 104 | 64,20% | 18,72 | 9,23 |
| **Renovate** | 148 | 1,48% | 81 | 54,73% | 11,09 | 5,75 |
| **Mend** | 100 | 1,00% | 60 | 60,00% | 19,52 | 10,28 |
| **Snyk** | 61 | 0,61% | 43 | 70,49% | 26,66 | 12,41 |
| **npm_audit** | 22 | 0,22% | 13 | 59,09% | 11,36 | 5,91 |
| **PyUp** | 1 | 0,01% | 1 | 100,00% | 82,00 | 39,00 |

### Gráficos (RQ1)

![Probabilidade de vulnerabilidade: % repos com pelo menos 1 CVE (por grupo)](graficos/bar_repo_vulnerability_rate.png)

![Distribuição de CVEs por repositório](graficos/boxplot_cves_by_group.png)

![CVEs por dependência](graficos/boxplot_cves_per_dependency_by_group.png)



### Conclusão RQ1

**Mais da metade dos projetos Node.js analisados (57,19%) contém pelo menos uma dependência com vulnerabilidade conhecida.**  
A frequência é alarmante, especialmente considerando que:
- Repositórios vulneráveis têm em média **11,12 dependências vulneráveis** por projeto
- Média de **24,17 CVEs por repositório vulnerável**
- Projetos sem bot de automação têm **57,08% de chance** de conter vulnerabilidades

---

## RQ2: Qual é o nível de severidade das vulnerabilidades encontradas e qual a distribuição proporcional entre os níveis de risco?

### Distribuição Agregada (todos os 9.982 repos)

| Severidade | Contagem | % |
|-----------|----------|------|
| **MEDIUM** | 58.697 | 42,54% |
| **HIGH** | 50.619 | 36,68% |
| **LOW** | 10.725 | 7,77% |
| **CRITICAL** | 10.722 | 7,77% |
| **UNKNOWN** | 7.224 | 5,24% |
| **TOTAL** | 137.987 | 100% |

### Análise por Grupo

#### Contagem agregada de CVEs por severidade (por bot)

| Severidade | Sem bot | Dependabot | CodeQL | Renovate | Mend | Snyk | npm_audit | PyUp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **LOW** | 9.364 | 642 | 289 | 144 | 123 | 123 | 33 | 7 |
| **MEDIUM** | 52.558 | 2.562 | 1.206 | 729 | 844 | 660 | 103 | 35 |
| **HIGH** | 44.937 | 2.332 | 1.189 | 623 | 754 | 653 | 97 | 34 |
| **CRITICAL** | 9.931 | 263 | 172 | 76 | 163 | 111 | 4 | 2 |
| **UNKNOWN** | 6.483 | 331 | 176 | 70 | 68 | 79 | 13 | 4 |
| **TOTAL** | 123.273 | 6.130 | 3.032 | 1.642 | 1.952 | 1.626 | 250 | 82 |

#### Distribuição Normalizada (%) por bot

| Severidade | Sem bot | Dependabot | CodeQL | Renovate | Mend | Snyk | npm_audit | PyUp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **LOW** | 7,60% | 10,47% | 9,53% | 8,77% | 6,30% | 7,56% | 13,20% | 8,54% |
| **MEDIUM** | 42,64% | 41,79% | 39,78% | 44,40% | 43,24% | 40,59% | 41,20% | 42,68% |
| **HIGH** | 36,45% | 38,04% | 39,22% | 37,94% | 38,63% | 40,16% | 38,80% | 41,46% |
| **CRITICAL** | 8,06% | 4,29% | 5,67% | 4,63% | 8,35% | 6,83% | 1,60% | 2,44% |
| **UNKNOWN** | 5,26% | 5,40% | 5,80% | 4,26% | 3,48% | 4,86% | 5,20% | 4,88% |

#### Concentração de Risco

| Nível | Criticidade | Contagem | Risco Operacional |
|-------|------------|----------|------------------|
| **HIGH + CRITICAL** | Imediato | 61.341 | **44,45%** do volume total |
| **MEDIUM** | Médio prazo | 58.697 | **42,54%** do volume |
| **LOW + UNKNOWN** | Monitorar | 17.949 | **13,01%** do volume |

### Gráficos (RQ2)

![Distribuição percentual de severidade por grupo (100% stacked)](graficos/stacked_bar_severity_distribution.png)

![Heatmap: severidade (%) por grupo](graficos/heatmap_severity_distribution.png)

### Descobertas Principais RQ2

1. **87,0% dos CVEs têm severidade MEDIUM ou superior** — indicando risco significativo
2. **CRITICAL varia entre os bots**: maiores proporções em **Mend (8,35%)** e **Sem bot (8,06%)**; menores em **npm_audit (1,60%)** e **PyUp (2,44%)**
3. **HIGH tende a ficar entre 36%–41%** em quase todos os bots, com **Snyk (40,16%)** e **PyUp (41,46%)** no topo
4. **MEDIUM é dominante em todos os grupos**, com pico em **Renovate (44,40%)**

*Observação:* grupos com amostra pequena (ex.: **PyUp** e **npm_audit**) devem ser interpretados como indicativos.

---

## RQ3: A utilização de uma ferramenta automatizada está associada a uma menor incidência de dependências com vulnerabilidades conhecidas nos projetos analisados?

**Resposta curta:** **não há evidência de redução na incidência** quando comparamos **com bot** vs **sem bot**; a diferença é **pequena**.

### Tabela RQ3 — Comparação com bot vs sem bot (incidência)

| Grupo | n (repos) | % repos com ≥1 vuln | Repos vulneráveis (aprox.) |
|---|---:|---:|---:|
| **Sem bot** | 8.964 | 57,08% | 5.117 |
| **Com bot (1+)** | 1.018 | 58,15% | ~592 |

**Evidências no dataset:**
- A incidência em **com bot (1+)** é **~+1,07 p.p.** acima de **sem bot**.
- O valor de **com bot (1+)** foi obtido pela **agregação dos grupos 1/2/3+ bots**.

**Interpretação:** a associação é **fraca** e **não indica causalidade**; a leve diferença pode refletir **viés de seleção** (projetos mais complexos tendem a adotar automação).


## RQ4: Existem diferenças entre categorias de bots quanto ao impacto na incidência de vulnerabilidades?

Sim — há diferenças observadas entre as categorias quando medimos (i) **incidência** (percentual de repositórios com pelo menos 1 vulnerabilidade) e (ii) **densidade de vulnerabilidades** (dependências vulneráveis por 100 versões resolvidas). A tabela abaixo compara as categorias usando a **categoria primária** detectada em cada repositório:

| Categoria (primária) | n (repos) | % repos com ≥1 vuln | Vulneráveis / 100 versões resolvidas | CVEs / 100 versões resolvidas |
|---|---:|---:|---:|---:|
| update (Renovate/PyUp) | 149 | 55,03% | 5,41 | 10,49 |
| update_security (Dependabot) | 524 | 55,34% | 4,48 | 8,76 |
| none (sem automação detectada) | 8.964 | 57,08% | 9,79 | 21,53 |
| audit_automation (npm audit) | 22 | 59,09% | 3,61 | 6,94 |
| security_remediation (Mend/WhiteSource) | 100 | 60,00% | 7,96 | 15,11 |
| security_automation (CodeQL) | 162 | 64,20% | 7,93 | 16,08 |
| security_scanner (Snyk) | 61 | 70,49% | 8,78 | 18,86 |

**Interpretação:**

- Em **incidência**, categorias de **atualização** (update / update_security) aparecem com as menores taxas (~55%), enquanto **security_scanner** é a maior (70,49%).
- Em **densidade**, repositórios **sem automação** (`none`) têm maior proporção de dependências vulneráveis por 100 versões resolvidas (9,79), enquanto categorias de **atualização** ficam bem abaixo (4,48–5,41).

Observação importante: essas diferenças são **associações** descritivas; não implicam causalidade (há vieses potenciais como tamanho/complexidade do projeto, perfil de manutenção, e adoção seletiva de ferramentas).

## RQ5: O uso combinado de múltiplos bots está associado a menores níveis de vulnerabilidade?

**Com base nos dados atuais, não há evidência de redução na incidência** (ter ou não ter “ao menos 1 vulnerabilidade”) com mais bots; porém, **há indício de menor densidade de vulnerabilidades** por versão resolvida quando há múltiplos bots — com a ressalva de que o grupo multi-bot é pequeno.

Distribuição e métricas por quantidade de bots detectados em cada repositório (`dependency_bots`):

| # bots detectados | n (repos) | % repos com ≥1 vuln | Vulneráveis / 100 versões resolvidas | CVEs / 100 versões resolvidas |
|---:|---:|---:|---:|---:|
| 0 | 8.964 | 57,08% | 9,79 | 21,53 |
| 1 | 736 | 57,74% | 6,59 | 12,98 |
| 2 | 245 | 58,78% | 4,03 | 8,18 |
| 3+ | 37 | 62,16% | 4,91 | 9,13 |

A combinação de 2 bots mais comum no dataset é **codeql + dependabot** (148 repositórios).

**Leitura dos resultados:**

- A **incidência** não diminui com mais bots (fica entre 57% e 62%).
- A **densidade** de vulnerabilidades cai bastante de 0 → 2 bots (9,79 → 4,03 vulneráveis/100 versões), o que sugere associação com ecossistemas mais “bem cuidados” ou pipelines mais maduros.

#### Implicações

- Em termos de **dependências diretas**, a incidência estimada de itens vulneráveis é menor com Dependabot (31,27% vs 45,01%; **-13,74 p.p.**)
- O custo operacional de manter essas ferramentas é **significativamente menor** do que o risco mitigado
- A adoção é **recomendável** para projetos Node.js em produção

---

## Recomendações

### Curto Prazo
1. **Adotar Dependabot ou Renovate** em todos os repositórios críticos
2. **Auditar dependências existentes** — especialmente HIGH e CRITICAL
3. **Estabelecer política SLA** para resolução de vulnerabilidades por severidade

### Médio Prazo
1. **Automatizar atualizações de LOW** — sem risco de breaking changes
2. **Revisar manualmente MEDIUM e HIGH** dentro de 30 dias
3. **Bloquear CRITICAL** em CI/CD até resolução

### Longo Prazo
1. **Monitorar tendências** de novas CVEs contra dependências pinadas
2. **Consolidar dependências** — reduzir a superfície de ataque
3. **Formar equipes de segurança** para resposta rápida a advisories

---

## Metodologia

- **Coleta**: OSV (Open Source Vulnerability) API para identificação
- **Validação**: Verificação cruzada com NVD (National Vulnerability Database)
- **Severidade**: CVSS base score normalizado para níveis

## Dados Brutos

Arquivo original: `summary_package-lock.json`  
Análise detalhada por repositório: `scan_por_repo/`

---

## Apêndice: Outros gráficos gerados

- [Scatter plot: dependências base versus CVEs por grupo](graficos/scatter_dependencies_vs_cves.png)
- [Scatter plot — Dependabot](graficos/scatter_dependencies_vs_cves_dependabot.png)
- [Scatter plot — None](graficos/scatter_dependencies_vs_cves_none.png)
- [Scatter plot — Renovate](graficos/scatter_dependencies_vs_cves_renovate.png)
- [Scatter plot — Snyk](graficos/scatter_dependencies_vs_cves_snyk.png)
- [Distribuição de CVEs por repositório (boxplot)](graficos/boxplot_cves_by_group.png)
- [CVEs por dependência (CVEs / dependências base) — boxplot](graficos/boxplot_cves_per_dependency_by_group.png)
