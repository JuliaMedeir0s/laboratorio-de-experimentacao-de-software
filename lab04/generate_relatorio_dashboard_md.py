#!/usr/bin/env python3
"""Generate lab04/outputs/RELATORIO_DASHBOARD.md from dataset/ANALISE_RQ.md.

Keeps the report aligned with the latest analysis (no hard-coded numbers).
Stdlib-only.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from dashboard_data import extract_metrics, load_analise


ROOT = Path(__file__).parent
OUT_PATH = ROOT / "outputs" / "RELATORIO_DASHBOARD.md"


def _fmt_int(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", ".")


def _fmt_pct(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}".replace(".", ",")


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def main() -> None:
    metrics = extract_metrics(load_analise())
    ds = metrics["dataset"]

    total_vuln_deps = ds.get("total_vulnerable_deps") or 0
    total_direct_deps = ds.get("total_direct_deps") or 0
    vuln_dep_rate = (100 * total_vuln_deps / total_direct_deps) if total_direct_deps else None
    cves_per_vuln_dep = (ds.get("total_cves") or 0) / total_vuln_deps if total_vuln_deps else None

    sev_pct = {s["severity"]: float(s["pct"]) for s in metrics.get("severity", [])}
    medium_or_higher = sev_pct.get("MEDIUM", 0) + sev_pct.get("HIGH", 0) + sev_pct.get("CRITICAL", 0)
    high_or_critical = sev_pct.get("HIGH", 0) + sev_pct.get("CRITICAL", 0)

    now = datetime.now().strftime("%d/%m/%Y")

    # Build tables
    dataset_table = _md_table(
        ["Métrica", "Valor"],
        [
            ["Total de repositórios analisados", _fmt_int(ds.get("total_repos"))],
            [
                "Repositórios com vulnerabilidades detectadas",
                f"{_fmt_int(ds.get('repos_with_vuln'))} ({_fmt_pct(ds.get('repos_with_vuln_pct'), 2)}%)",
            ],
            [
                "Repositórios sem vulnerabilidades",
                f"{_fmt_int(ds.get('repos_without_vuln'))} ({_fmt_pct(ds.get('repos_without_vuln_pct'), 2)}%)",
            ],
            ["Dependências vulneráveis (total)", _fmt_int(ds.get("total_vulnerable_deps"))],
            ["Dependências diretas (total)", _fmt_int(ds.get("total_direct_deps"))],
            ["Versões resolvidas (total)", _fmt_int(ds.get("total_resolved_versions"))],
            ["CVEs associados (total)", _fmt_int(ds.get("total_cves"))],
        ],
    )

    bots_rows = []
    for b in metrics.get("bots", []):
        bots_rows.append(
            [
                f"**{b['tool']}**",
                _fmt_int(b["repos"]),
                f"{_fmt_pct(b['pct'], 2)}%",
                f"{_fmt_pct(b['taxa'], 2)}%",
            ]
        )
    bots_table = _md_table(
        ["Ferramenta", "Repositórios", "Percentual", "Taxa de Vulnerabilidade"],
        bots_rows,
    )

    rq1 = metrics.get("rq1_by_repo_group", {})
    rq1_table = _md_table(
        ["Métrica", "Com Vulnerabilidade", "Sem Vulnerabilidade"],
        [
            [
                "**Dependências diretas/repo**",
                str(rq1.get("Dependências diretas/repo", {}).get("with", "—")).replace(".", ","),
                str(rq1.get("Dependências diretas/repo", {}).get("without", "—")).replace(".", ","),
            ],
            [
                "**Versões resolvidas/repo**",
                str(rq1.get("Versões resolvidas/repo", {}).get("with", "—")).replace(".", ","),
                str(rq1.get("Versões resolvidas/repo", {}).get("without", "—")).replace(".", ","),
            ],
            [
                "**Dependências vulneráveis/repo**",
                str(rq1.get("Dependências vulneráveis/repo", {}).get("with", "—")).replace(".", ","),
                "0",
            ],
            [
                "**CVEs/repo**",
                str(rq1.get("CVEs/repo", {}).get("with", "—")).replace(".", ","),
                "0",
            ],
        ],
    )

    severity_rows = []
    for s in metrics.get("severity", []):
        level = s["severity"]
        risk = "Imediato" if level in ("HIGH", "CRITICAL") else "Médio prazo" if level == "MEDIUM" else "Monitorar"
        severity_rows.append([f"**{level}**", _fmt_int(s["count"]), f"{_fmt_pct(s['pct'], 2)}%", risk])
    severity_table = _md_table(
        ["Nível de Severidade", "Contagem", "Percentual", "Risco Operacional"],
        severity_rows,
    )

    sev_norm_rows = []
    for s in metrics.get("severity_by_group", []):
        sev_norm_rows.append(
            [
                f"**{s['severity']}**",
                f"{_fmt_pct(s['with_dependabot_pct'], 2)}%",
                f"{_fmt_pct(s['without_dependabot_pct'], 2)}%",
                f"{_fmt_pct(s['diff_pp'], 2)} p.p.",
            ]
        )
    sev_norm_table = _md_table(
        ["Severity", "Com Dependabot", "Sem Dependabot", "Diferença"],
        sev_norm_rows,
    )

    rq3_direct_rows = []
    for r in metrics.get("rq3_comparison_direct", []):
        rq3_direct_rows.append(
            [
                f"**{r['metric']}**",
                r["with_dependabot"],
                r["without_dependabot"],
                r["ratio"],
                r["benefit"],
            ]
        )
    rq3_direct_table = _md_table(
        ["Métrica", "Com Dependabot", "Sem Dependabot", "Razão (Sem/Com)", "Benefício"],
        rq3_direct_rows,
    )

    rq3_tools_rows = []
    for t in metrics.get("rq3_tools_comparison", []):
        rq3_tools_rows.append(
            [
                f"**{t['tool']}**",
                _fmt_int(t["repos"]),
                f"{_fmt_pct(t['taxa'], 2)}%",
                str(t["cves_per_repo"]).replace(".", ","),
                t["status"],
            ]
        )
    rq3_tools_table = _md_table(
        ["Ferramenta", "Repos", "Taxa Vulner.", "CVEs/Repo", "Status"],
        rq3_tools_rows,
    )

    md = f"""# Dashboard BI - Análise de Dependências Vulneráveis em Projetos Node.js

**Data de Geração:** {now}  \
**Dataset:** {metrics['meta'].get('dataset','')}  \
**Período:** {metrics['meta'].get('periodo','')}  \
**Ferramenta:** OSV + NVD para mapeamento de CVEs

---

## Nota sobre a ferramenta de BI

O enunciado do laboratório pede um dashboard construído em **Power BI**, **Tableau** ou **Looker Studio**.

Este relatório em Markdown e os artefatos em `outputs/` servem como **documentação** e referência.
Para montar o dashboard em BI a partir dos CSVs, use `lab04/bi/README.md`.

---

## 1. Caracterização do Dataset

### 1.1. Visão Geral

{dataset_table}

### 1.2. Distribuição de Bots de Automação

{bots_table}

### 1.3. Distribuição de Dependências

| Métrica | Valor |
|---|---|
| **Dependências Diretas (Total)** | {_fmt_int(ds.get('total_direct_deps'))} |
| **Versões Resolvidas** | {_fmt_int(ds.get('total_resolved_versions'))} |
| **Dependências Vulneráveis** | {_fmt_int(ds.get('total_vulnerable_deps'))} |
| **Taxa de Vulnerabilidade** | {_fmt_pct(vuln_dep_rate, 2)}% |

### 1.4. Estatísticas Descritivas por Grupo

{rq1_table}

---

## 2. RQ1: Frequência de Dependências Vulneráveis

### Pergunta de Pesquisa

**Qual é a frequência de dependências vulneráveis em projetos Node.js hospedados no GitHub?**

### Insight Principal

**{_fmt_pct(ds.get('repos_with_vuln_pct'), 2)}% dos projetos analisados contém pelo menos uma vulnerabilidade.**

### Estatísticas Principais

| Métrica | Valor |
|---|---|
| **Taxa de Repos Vulneráveis** | {_fmt_pct(ds.get('repos_with_vuln_pct'), 2)}% |
| **Dependências Vulneráveis/Repo (média)** | {str(rq1.get('Dependências vulneráveis/repo',{}).get('with','—')).replace('.', ',')} |
| **CVEs por Repositório Vulnerável** | {str(rq1.get('CVEs/repo',{}).get('with','—')).replace('.', ',')} |
| **CVEs por Dependência Vulnerável** | {_fmt_pct(cves_per_vuln_dep, 2) if cves_per_vuln_dep is not None else '—'} |

### Visualizações

- Taxa de Vulnerabilidade por Grupo (`bar_repo_vulnerability_rate.png`)
- Distribuição de CVEs por Repositório (`boxplot_cves_by_group.png`)

---

## 3. RQ2: Nível de Severidade das Vulnerabilidades

### Pergunta de Pesquisa

**Qual é o nível de severidade das vulnerabilidades encontradas e qual a distribuição proporcional entre os níveis de risco?**

### Insight Principal

**{_fmt_pct(medium_or_higher, 2)}% dos CVEs têm severidade MEDIUM ou superior.**

### Distribuição de Severidade

{severity_table}

### Concentração de Risco

| Classificação | Severidade | % do Total |
|---|---|---|
| **HIGH + CRITICAL** | Imediato | {_fmt_pct(high_or_critical, 2)}% |
| **MEDIUM** | Médio prazo | {_fmt_pct(sev_pct.get('MEDIUM', 0), 2)}% |
| **LOW + UNKNOWN** | Monitorar | {_fmt_pct(sev_pct.get('LOW', 0) + sev_pct.get('UNKNOWN', 0), 2)}% |

### Distribuição Normalizada com/sem Dependabot

{sev_norm_table}

### Visualizações

- Distribuição Percentual de Severidade (100% Stacked) (`stacked_bar_severity_distribution.png`)
- Heatmap de Severidade por Grupo (`heatmap_severity_distribution.png`)

---

## 4. RQ3: Impacto da Automação (Dependabot, Renovate, Snyk)

### Pergunta de Pesquisa

**A utilização de ferramentas de automação está associada a menor incidência de vulnerabilidades?**

### Comparação Direta (Dependabot vs Sem Dependabot)

{rq3_direct_table}

### Comparação com Outras Ferramentas

{rq3_tools_table}

### Visualizações

- Comparação Normalizada de Risco (`bar_normalized_comparison.png`)
- Atividade de Correção - Versões Resolvidas (`bar_activity_difference_vs_none.png`)
- Scatter Plot - Dependências vs CVEs (`scatter_dependencies_vs_cves.png`)

---

## 5. Recomendações (síntese)

- Curto prazo: auditar dependências, adotar automação, priorizar HIGH/CRITICAL.
- Médio prazo: automatizar updates e impor políticas em CI/CD.
- Longo prazo: monitoramento contínuo e redução de acoplamento de dependências.
"""

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(md, encoding="utf-8")
    print("✅ Report generated:", OUT_PATH)


if __name__ == "__main__":
    main()
