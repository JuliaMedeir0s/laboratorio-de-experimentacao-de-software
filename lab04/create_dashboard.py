#!/usr/bin/env python3
"""Gera o dashboard HTML do Lab04 a partir dos CSVs em bi/tables/.

Todos os gráficos são gerados com matplotlib e embutidos como base64.
Execute: python create_dashboard.py
Saída:   outputs/dashboard.html
"""

import csv
import io
import base64
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
BI_DIR = ROOT / "bi" / "tables"
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
C_BLUE   = "#4361ee"
C_PINK   = "#f72585"
C_TEAL   = "#4cc9f0"
C_GREEN  = "#52b788"
C_ORANGE = "#f8961e"
C_GRAY   = "#94a3b8"

BOT_COLORS = {
    "Sem bot":    C_GRAY,
    "Dependabot": C_BLUE,
    "Renovate":   C_GREEN,
    "Snyk":       C_ORANGE,
}

SEV_COLORS = {
    "CRITICAL": "#d62828",
    "HIGH":     "#f4a261",
    "MEDIUM":   "#e9c46a",
    "LOW":      "#52b788",
    "UNKNOWN":  "#adb5bd",
}

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def read_csv(name: str) -> list[dict]:
    path = BI_DIR / f"{name}.csv"
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data() -> dict:
    overview_rows = read_csv("dataset_overview")
    overview = {r["metric"]: r["value"] for r in overview_rows}

    bots = read_csv("bots_distribution")
    rq1  = read_csv("rq1_repo_group_averages")
    sev  = read_csv("severity_distribution")
    sev_group = read_csv("severity_by_group_dependabot")
    rq3_direct = read_csv("rq3_comparison_direct")
    rq3_tools  = read_csv("rq3_tools_comparison")

    return {
        "overview": overview,
        "bots": bots,
        "rq1": rq1,
        "severity": sev,
        "sev_group": sev_group,
        "rq3_direct": rq3_direct,
        "rq3_tools": rq3_tools,
    }

# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    buf.seek(0)
    result = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return result


def img_tag(b64: str, alt: str = "") -> str:
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);">'

# ---------------------------------------------------------------------------
# Chart 1 – Donut: repos com vs sem vulnerabilidade
# ---------------------------------------------------------------------------

def chart_vuln_donut(overview: dict) -> str:
    with_v = float(overview["repos_with_vuln_pct"])
    without_v = float(overview["repos_without_vuln_pct"])

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        [with_v, without_v],
        labels=["Com\nVulnerabilidade", "Sem\nVulnerabilidade"],
        colors=[C_PINK, C_TEAL],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
        pctdistance=0.75,
    )
    for t in texts:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")
        at.set_color("white")

    total = int(overview["total_repos"])
    ax.text(0, 0, f"{total:,}\nrepos", ha="center", va="center",
            fontsize=13, fontweight="bold", color="#333")
    ax.set_title("Repositórios com Vulnerabilidades Detectadas", fontsize=13, pad=15, fontweight="bold")
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 2 – Bar: taxa de vulnerabilidade por ferramenta (caracterização subgrupos)
# ---------------------------------------------------------------------------

def chart_bots_taxa(bots: list[dict]) -> str:
    tools = [r["tool"] for r in bots]
    taxas = [float(r["taxa"]) for r in bots]
    colors = [BOT_COLORS.get(t, C_BLUE) for t in tools]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(tools, taxas, color=colors, width=0.5, edgecolor="white", linewidth=1.5)

    for bar, v in zip(bars, taxas):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{v:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylim(0, max(taxas) * 1.2)
    ax.set_ylabel("Taxa de Repositórios Vulneráveis (%)", fontsize=11)
    ax.set_title("Taxa de Vulnerabilidade por Ferramenta de Automação", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 3 – Grouped bar: tamanho de cada subgrupo
# ---------------------------------------------------------------------------

def chart_bots_repos(bots: list[dict]) -> str:
    tools = [r["tool"] for r in bots]
    total = [int(r["repos"]) for r in bots]
    vulner = [int(r["repos_vulner"]) for r in bots]

    x = np.arange(len(tools))
    w = 0.35

    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar(x - w/2, total,  w, label="Total de repos",        color=[BOT_COLORS.get(t, C_BLUE) for t in tools], alpha=0.9, edgecolor="white")
    b2 = ax.bar(x + w/2, vulner, w, label="Repos com vulnerabilidade", color=[BOT_COLORS.get(t, C_BLUE) for t in tools], alpha=0.45, edgecolor="white", hatch="///")

    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 30,
                f"{int(h):,}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(tools, fontsize=11)
    ax.set_ylabel("Número de Repositórios", fontsize=11)
    ax.set_title("Distribuição de Repositórios por Ferramenta de Automação", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 4 – RQ1: Grouped bar comparando métricas entre grupos
# ---------------------------------------------------------------------------

def chart_rq1_metrics(rq1: list[dict]) -> str:
    labels = [r["metric"] for r in rq1]
    with_v = [float(r["with_vulnerability"]) for r in rq1]
    without_v = [float(r["without_vulnerability"]) for r in rq1]

    # Duas métricas mais relevantes: dependências diretas e CVEs
    selected = ["Dependências diretas/repo", "CVEs/repo"]
    sel_idx  = [labels.index(s) for s in selected if s in labels]

    labels_s   = [labels[i] for i in sel_idx]
    with_v_s   = [with_v[i] for i in sel_idx]
    without_v_s = [without_v[i] for i in sel_idx]

    x = np.arange(len(labels_s))
    w = 0.32

    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar(x - w/2, with_v_s,   w, label="Com vulnerabilidade",  color=C_PINK, edgecolor="white")
    b2 = ax.bar(x + w/2, without_v_s, w, label="Sem vulnerabilidade", color=C_TEAL, edgecolor="white")

    for bar in list(b1) + list(b2):
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.3,
                    f"{h:.1f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels_s, fontsize=11)
    ax.set_ylabel("Média por Repositório", fontsize=11)
    ax.set_title("RQ1 — Média de Métricas: Repos com vs. sem Vulnerabilidade", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 5 – RQ2: Donut de severidade
# ---------------------------------------------------------------------------

def chart_severity_donut(severity: list[dict]) -> str:
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    sev_map = {r["severity"]: r for r in severity}
    labels  = [s for s in order if s in sev_map]
    values  = [float(sev_map[s]["pct"]) for s in labels]
    colors  = [SEV_COLORS[s] for s in labels]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
        pctdistance=0.78,
    )
    for t in texts:
        t.set_fontsize(11)
        t.set_fontweight("bold")
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight("bold")
        at.set_color("white")

    high_crit = sum(v for s, v in zip(labels, values) if s in ("HIGH", "CRITICAL"))
    ax.text(0, 0, f"{high_crit:.1f}%\nHIGH+\nCRITICAL", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#d62828")
    ax.set_title("RQ2 — Distribuição de Severidade dos CVEs", fontsize=13, pad=15, fontweight="bold")
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 6 – RQ2: Grouped bar severidade com vs sem Dependabot
# ---------------------------------------------------------------------------

def chart_severity_groups(sev_group: list[dict]) -> str:
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    sg_map = {r["severity"]: r for r in sev_group}
    labels = [s for s in order if s in sg_map]
    with_d   = [float(sg_map[s]["with_dependabot_pct"]) for s in labels]
    without_d = [float(sg_map[s]["without_dependabot_pct"]) for s in labels]

    x = np.arange(len(labels))
    w = 0.32

    fig, ax = plt.subplots(figsize=(9, 4.5))
    b1 = ax.bar(x - w/2, with_d,   w, label="Com Dependabot",  color=C_BLUE, edgecolor="white")
    b2 = ax.bar(x + w/2, without_d, w, label="Sem Dependabot", color=C_GRAY, edgecolor="white")

    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.3,
                f"{h:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("% dos CVEs no grupo", fontsize=11)
    ax.set_title("RQ2 — Distribuição de Severidade: Com vs. sem Dependabot", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 7 – RQ3: Taxa de repos vulneráveis por ferramenta
# ---------------------------------------------------------------------------

def chart_rq3_taxa(rq3_tools: list[dict]) -> str:
    tools  = [r["tool"] for r in rq3_tools]
    taxas  = [float(r["taxa"]) for r in rq3_tools]
    colors = [BOT_COLORS.get(t, C_BLUE) for t in tools]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(tools, taxas, color=colors, width=0.5, edgecolor="white", linewidth=1.5)

    baseline = taxas[0] if taxas else 0
    for bar, v, t in zip(bars, taxas, tools):
        label = f"{v:.1f}%"
        if t != "Sem bot" and baseline:
            diff = v - baseline
            sign = "+" if diff > 0 else ""
            label += f"\n({sign}{diff:.1f} p.p.)"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                label, ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(baseline, color="red", linestyle="--", linewidth=1.2, alpha=0.6, label=f"Baseline sem bot ({baseline:.1f}%)")
    ax.set_ylim(0, max(taxas) * 1.3)
    ax.set_ylabel("Taxa de Repositórios Vulneráveis (%)", fontsize=11)
    ax.set_title("RQ3 — Taxa de Repos Vulneráveis por Ferramenta de Automação", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# Chart 8 – RQ3: CVEs por repo por ferramenta
# ---------------------------------------------------------------------------

def chart_rq3_cves(rq3_tools: list[dict]) -> str:
    tools = [r["tool"] for r in rq3_tools]
    cves  = [float(r["cves_per_repo"]) for r in rq3_tools]
    colors = [BOT_COLORS.get(t, C_BLUE) for t in tools]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(tools, cves, color=colors, width=0.5, edgecolor="white", linewidth=1.5)

    baseline = cves[0] if cves else 0
    for bar, v, t in zip(bars, cves, tools):
        label = f"{v:.1f}"
        if t != "Sem bot" and baseline:
            pct = (v - baseline) / baseline * 100
            sign = "+" if pct > 0 else ""
            label += f"\n({sign}{pct:.0f}%)"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                label, ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(baseline, color="red", linestyle="--", linewidth=1.2, alpha=0.6, label=f"Baseline sem bot ({baseline:.1f})")
    ax.set_ylim(0, max(cves) * 1.3)
    ax.set_ylabel("CVEs por Repositório (média)", fontsize=11)
    ax.set_title("RQ3 — Média de CVEs por Repositório por Ferramenta", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return to_b64(fig)

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f0f2f5;
    color: #1e293b;
    line-height: 1.6;
}

.container { max-width: 1300px; margin: 0 auto; padding: 24px; }

header {
    background: linear-gradient(135deg, #4361ee 0%, #7209b7 100%);
    color: white;
    padding: 40px 32px;
    border-radius: 12px;
    margin-bottom: 32px;
    box-shadow: 0 4px 20px rgba(67,97,238,.35);
}

header h1 { font-size: 2.2em; margin-bottom: 6px; }
header p  { font-size: 1.1em; opacity: .9; }

.meta {
    display: flex;
    justify-content: space-between;
    margin-top: 18px;
    font-size: .85em;
    opacity: .8;
    flex-wrap: wrap;
    gap: 8px;
}

.section {
    background: white;
    padding: 32px;
    margin-bottom: 28px;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
}

.section h2 {
    color: #4361ee;
    font-size: 1.7em;
    margin-bottom: 8px;
    padding-bottom: 10px;
    border-bottom: 3px solid #4361ee;
}

.section h3 {
    color: #7209b7;
    font-size: 1.2em;
    margin: 24px 0 12px;
}

.rq-question {
    background: #f0f4ff;
    border-left: 4px solid #4361ee;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0 24px;
    font-size: 1.05em;
}

.rq-question strong { color: #4361ee; }

.insight {
    background: #f0fdf4;
    border-left: 4px solid #52b788;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
}

.insight strong { color: #276749; }

.conclusion {
    background: #fff7ed;
    border-left: 4px solid #f8961e;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0 0;
}

.conclusion strong { color: #9c4221; }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 16px;
    margin: 20px 0 28px;
}

.kpi {
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    color: white;
    box-shadow: 0 3px 10px rgba(0,0,0,.12);
}

.kpi .val  { font-size: 2.2em; font-weight: 700; margin-bottom: 4px; line-height: 1.1; }
.kpi .lbl  { font-size: .85em; opacity: .92; }

.kpi-blue   { background: linear-gradient(135deg, #4361ee, #3a0ca3); }
.kpi-pink   { background: linear-gradient(135deg, #f72585, #b5179e); }
.kpi-teal   { background: linear-gradient(135deg, #4cc9f0, #0096c7); }
.kpi-green  { background: linear-gradient(135deg, #52b788, #1b4332); }
.kpi-orange { background: linear-gradient(135deg, #f8961e, #ae2012); }

.charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin: 24px 0;
}

.chart-wrap { text-align: center; }

.chart-wrap .chart-lbl {
    font-size: 1em;
    color: #4361ee;
    font-weight: 600;
    margin-bottom: 10px;
}

.chart-full { text-align: center; margin: 24px 0; }
.chart-full .chart-lbl {
    font-size: 1.05em;
    color: #4361ee;
    font-weight: 600;
    margin-bottom: 10px;
}

.table-wrap { overflow-x: auto; margin: 16px 0 24px; }

table { width: 100%; border-collapse: collapse; }
thead { background: #f0f4ff; border-bottom: 2px solid #4361ee; }
th { padding: 12px 14px; text-align: left; font-weight: 600; color: #4361ee; font-size: .95em; }
td { padding: 11px 14px; border-bottom: 1px solid #e8ecf0; font-size: .95em; }
tbody tr:hover { background: #f8faff; }

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: .82em;
    font-weight: 600;
}

.badge-red    { background: #fee2e2; color: #991b1b; }
.badge-orange { background: #ffedd5; color: #9a3412; }
.badge-yellow { background: #fef9c3; color: #713f12; }
.badge-green  { background: #dcfce7; color: #166534; }
.badge-gray   { background: #f1f5f9; color: #475569; }

footer {
    text-align: center;
    padding: 20px;
    color: #64748b;
    font-size: .88em;
    border-top: 1px solid #e2e8f0;
    margin-top: 32px;
}

@media (max-width: 768px) {
    .charts-row { grid-template-columns: 1fr; }
    .kpi-grid   { grid-template-columns: 1fr 1fr; }
}

@media print {
    body { background: white; }
    .section { box-shadow: none; border: 1px solid #e2e8f0; page-break-inside: avoid; }
    .kpi { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""


def sev_badge(sev: str) -> str:
    cls = {
        "CRITICAL": "badge-red",
        "HIGH":     "badge-orange",
        "MEDIUM":   "badge-yellow",
        "LOW":      "badge-green",
        "UNKNOWN":  "badge-gray",
    }.get(sev.upper(), "badge-gray")
    return f'<span class="badge {cls}">{sev}</span>'


def build_html(data: dict, charts: dict) -> str:
    ov   = data["overview"]
    bots = data["bots"]
    sev  = data["severity"]
    rq3d = data["rq3_direct"]
    rq3t = data["rq3_tools"]
    rq1  = {r["metric"]: r for r in data["rq1"]}

    total_repos  = int(ov["total_repos"])
    vuln_repos   = int(ov["repos_with_vuln"])
    vuln_pct     = float(ov["repos_with_vuln_pct"])
    no_vuln_repos = int(ov["repos_without_vuln"])
    total_cves   = int(ov["total_cves"])
    total_vdeps  = int(ov["total_vulnerable_deps"])
    total_deps   = int(ov["total_direct_deps"])
    vuln_dep_pct = total_vdeps / total_deps * 100

    rq1_deps_with  = float(rq1["Dependências diretas/repo"]["with_vulnerability"])
    rq1_cves_with  = float(rq1["CVEs/repo"]["with_vulnerability"])

    sev_map = {r["severity"]: r for r in sev}
    high_crit_pct = float(sev_map.get("HIGH", {}).get("pct", 0)) + float(sev_map.get("CRITICAL", {}).get("pct", 0))
    medium_plus_pct = high_crit_pct + float(sev_map.get("MEDIUM", {}).get("pct", 0))

    baseline_taxa = next((float(r["taxa"]) for r in rq3t if r["tool"] == "Sem bot"), 0)
    dep_taxa      = next((float(r["taxa"]) for r in rq3t if r["tool"] == "Dependabot"), 0)
    dep_cves      = next((float(r["cves_per_repo"]) for r in rq3t if r["tool"] == "Dependabot"), 0)
    base_cves     = next((float(r["cves_per_repo"]) for r in rq3t if r["tool"] == "Sem bot"), 0)
    dep_reduc_taxa = (baseline_taxa - dep_taxa) / baseline_taxa * 100
    dep_reduc_cves = (base_cves - dep_cves) / base_cves * 100

    now = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Bot rows
    bot_rows = ""
    for b in bots:
        bot_rows += f"""
        <tr>
            <td><strong>{b['tool']}</strong></td>
            <td>{int(b['repos']):,}</td>
            <td>{float(b['pct']):.1f}%</td>
            <td>{int(b['repos_vulner']):,}</td>
            <td>{float(b['taxa']):.1f}%</td>
            <td>{float(b['cves_per_repo']):.1f}</td>
        </tr>"""

    # Severity rows
    sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    sev_risk  = {"CRITICAL": "Imediato", "HIGH": "Imediato", "MEDIUM": "Médio prazo", "LOW": "Monitorar", "UNKNOWN": "Monitorar"}
    sev_rows = ""
    for s in sev_order:
        if s in sev_map:
            r = sev_map[s]
            sev_rows += f"""
        <tr>
            <td>{sev_badge(s)}</td>
            <td>{int(r['count']):,}</td>
            <td>{float(r['pct']):.2f}%</td>
            <td>{sev_risk[s]}</td>
        </tr>"""

    # RQ3 direct comparison rows
    rq3d_rows = ""
    for r in rq3d:
        rq3d_rows += f"""
        <tr>
            <td>{r['metric']}</td>
            <td>{r['with_dependabot']}</td>
            <td>{r['without_dependabot']}</td>
            <td>{r['ratio']}</td>
            <td>{r['benefit']}</td>
        </tr>"""

    # RQ3 tools rows
    rq3t_rows = ""
    for r in rq3t:
        rq3t_rows += f"""
        <tr>
            <td><strong>{r['tool']}</strong></td>
            <td>{int(r['repos']):,}</td>
            <td>{float(r['taxa']):.1f}%</td>
            <td>{float(r['cves_per_repo']):.1f}</td>
            <td>{r['status']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — Dependências Vulneráveis em Projetos Node.js</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<!-- HEADER -->
<header>
  <h1>Dashboard BI</h1>
  <p>Análise de Dependências Vulneráveis em Projetos Node.js do GitHub</p>
  <div class="meta">
    <span>9.982 repositórios Node.js públicos &nbsp;|&nbsp; Snapshot de maio de 2026</span>
    <span>Gerado em: {now}</span>
  </div>
</header>

<!-- ===== SEÇÃO 1: CARACTERIZAÇÃO ===== -->
<div class="section">
  <h2>1. Caracterização do Dataset</h2>
  <p style="margin-bottom:20px;">
    O dataset compreende <strong>{total_repos:,} repositórios Node.js públicos</strong> hospedados no GitHub,
    coletados em snapshot de maio de 2026. A identificação de vulnerabilidades utiliza a
    <strong>OSV API</strong> e o <strong>NVD (National Vulnerability Database)</strong>.
  </p>

  <h3>1.1. Visão Geral</h3>
  <div class="kpi-grid">
    <div class="kpi kpi-blue">
      <div class="val">{total_repos:,}</div>
      <div class="lbl">Repositórios Analisados</div>
    </div>
    <div class="kpi kpi-pink">
      <div class="val">{vuln_repos:,}</div>
      <div class="lbl">Com Vulnerabilidades ({vuln_pct:.1f}%)</div>
    </div>
    <div class="kpi kpi-teal">
      <div class="val">{no_vuln_repos:,}</div>
      <div class="lbl">Sem Vulnerabilidades ({100-vuln_pct:.1f}%)</div>
    </div>
    <div class="kpi kpi-orange">
      <div class="val">{total_cves:,}</div>
      <div class="lbl">CVEs Identificados</div>
    </div>
    <div class="kpi kpi-green">
      <div class="val">{total_vdeps:,}</div>
      <div class="lbl">Dependências Vulneráveis ({vuln_dep_pct:.1f}% das diretas)</div>
    </div>
  </div>

  <div class="charts-row">
    <div class="chart-wrap">
      <div class="chart-lbl">Proporção de Repositórios com Vulnerabilidades</div>
      {img_tag(charts['donut_vuln'], 'Donut vuln')}
    </div>
    <div class="chart-wrap">
      <div class="chart-lbl">Repositórios por Ferramenta de Automação</div>
      {img_tag(charts['bots_repos'], 'Bots repos')}
    </div>
  </div>

  <h3>1.2. Subgrupos por Ferramenta de Automação</h3>
  <p style="margin-bottom:14px;">
    O dataset é particionado conforme a presença de bots de automação de dependências.
    A caracterização de cada subgrupo é essencial para as análises comparativas das RQs.
  </p>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Ferramenta</th>
          <th>Total de Repos</th>
          <th>% do Dataset</th>
          <th>Repos com Vuln.</th>
          <th>Taxa de Vuln.</th>
          <th>CVEs/Repo (média)</th>
        </tr>
      </thead>
      <tbody>{bot_rows}</tbody>
    </table>
  </div>

  <div class="chart-full">
    <div class="chart-lbl">Taxa de Vulnerabilidade por Ferramenta (caracterização dos subgrupos)</div>
    {img_tag(charts['bots_taxa'], 'Taxa vuln por ferramenta')}
  </div>
</div>

<!-- ===== SEÇÃO 2: RQ1 ===== -->
<div class="section">
  <h2>2. RQ1 — Frequência de Dependências Vulneráveis</h2>

  <div class="rq-question">
    <strong>Pergunta de Pesquisa:</strong>
    Qual é a frequência de dependências vulneráveis em projetos Node.js hospedados no GitHub?
  </div>

  <div class="insight">
    <strong>Insight Principal:</strong>
    <strong>{vuln_pct:.1f}%</strong> dos projetos Node.js analisados contêm pelo menos uma
    dependência com vulnerabilidade conhecida — mais da metade do dataset.
    Repositórios vulneráveis têm em média <strong>{rq1_cves_with:.1f} CVEs</strong> e
    <strong>{rq1_deps_with:.1f} dependências diretas</strong> por projeto.
  </div>

  <h3>2.1. Estatísticas Principais</h3>
  <div class="kpi-grid">
    <div class="kpi kpi-pink">
      <div class="val">{vuln_pct:.1f}%</div>
      <div class="lbl">Taxa de Repos Vulneráveis</div>
    </div>
    <div class="kpi kpi-orange">
      <div class="val">{float(rq1["Dependências vulneráveis/repo"]["with_vulnerability"]):.1f}</div>
      <div class="lbl">Deps. Vulneráveis/Repo (média)</div>
    </div>
    <div class="kpi kpi-blue">
      <div class="val">{rq1_cves_with:.1f}</div>
      <div class="lbl">CVEs por Repo Vulnerável (média)</div>
    </div>
    <div class="kpi kpi-teal">
      <div class="val">{total_cves / vuln_repos:.1f}</div>
      <div class="lbl">CVEs por Dep. Vulnerável (média)</div>
    </div>
  </div>

  <h3>2.2. Comparação entre Grupos</h3>
  <div class="chart-full">
    <div class="chart-lbl">Métricas Médias — Repos com vs. sem Vulnerabilidade</div>
    {img_tag(charts['rq1_metrics'], 'RQ1 métricas')}
  </div>

  <div class="conclusion">
    <strong>Conclusão RQ1:</strong>
    A frequência de vulnerabilidades é expressiva: {vuln_pct:.1f}% dos repositórios contêm ao menos
    uma dependência comprometida. Repos vulneráveis têm, em média, {rq1_deps_with:.1f} dependências diretas
    (vs {float(rq1["Dependências diretas/repo"]["without_vulnerability"]):.1f} nos sem vuln) e acumulam
    {rq1_cves_with:.1f} CVEs por projeto — reforçando que maior uso de dependências eleva o risco.
  </div>
</div>

<!-- ===== SEÇÃO 3: RQ2 ===== -->
<div class="section">
  <h2>3. RQ2 — Nível de Severidade das Vulnerabilidades</h2>

  <div class="rq-question">
    <strong>Pergunta de Pesquisa:</strong>
    Qual é o nível de severidade das vulnerabilidades encontradas e qual a distribuição
    proporcional entre os níveis de risco?
  </div>

  <div class="insight">
    <strong>Insight Principal:</strong>
    <strong>{medium_plus_pct:.1f}%</strong> dos CVEs têm severidade MEDIUM ou superior,
    e <strong>{high_crit_pct:.1f}%</strong> são HIGH ou CRITICAL — exigindo atenção imediata.
  </div>

  <h3>3.1. Distribuição Agregada de Severidade</h3>
  <div class="charts-row">
    <div class="chart-wrap">
      <div class="chart-lbl">Distribuição Percentual dos CVEs por Severidade</div>
      {img_tag(charts['sev_donut'], 'Severidade donut')}
    </div>
    <div class="chart-wrap" style="display:flex;flex-direction:column;justify-content:center;">
      <div class="table-wrap" style="margin:0;">
        <table>
          <thead>
            <tr><th>Severidade</th><th>CVEs</th><th>%</th><th>Prioridade</th></tr>
          </thead>
          <tbody>{sev_rows}</tbody>
        </table>
      </div>
    </div>
  </div>

  <h3>3.2. Severidade com vs. sem Dependabot</h3>
  <div class="chart-full">
    <div class="chart-lbl">% de CVEs por Nível de Severidade — Com vs. sem Dependabot</div>
    {img_tag(charts['sev_groups'], 'Severidade por grupo')}
  </div>

  <div class="conclusion">
    <strong>Conclusão RQ2:</strong>
    A distribuição de severidade é dominada por MEDIUM ({float(sev_map.get('MEDIUM',{}).get('pct',0)):.1f}%)
    e HIGH ({float(sev_map.get('HIGH',{}).get('pct',0)):.1f}%), somando {medium_plus_pct:.1f}% dos CVEs com risco operacional
    relevante. Repositórios com Dependabot apresentam menor proporção de CVEs CRITICAL
    ({next((r['with_dependabot_pct'] for r in data['sev_group'] if r['severity']=='CRITICAL'), 0)}% vs
    {next((r['without_dependabot_pct'] for r in data['sev_group'] if r['severity']=='CRITICAL'), 0)}%),
    sugerindo que a automação contribui para mitigação das vulnerabilidades mais graves.
  </div>
</div>

<!-- ===== SEÇÃO 4: RQ3 ===== -->
<div class="section">
  <h2>4. RQ3 — Impacto das Ferramentas de Automação</h2>

  <div class="rq-question">
    <strong>Pergunta de Pesquisa:</strong>
    A utilização de ferramentas de automação (Dependabot, Renovate, Snyk) está associada a
    uma menor incidência de dependências vulneráveis nos projetos analisados?
  </div>

  <div class="insight">
    <strong>Insight Principal:</strong>
    Sim. O uso de <strong>Dependabot</strong> está associado a uma redução de
    <strong>{dep_reduc_taxa:.1f}%</strong> na taxa de repos vulneráveis e de
    <strong>{dep_reduc_cves:.1f}%</strong> no número médio de CVEs por projeto
    em comparação com repositórios sem automação.
  </div>

  <h3>4.1. Comparação Direta: com vs. sem Dependabot</h3>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Métrica</th>
          <th>Com Dependabot</th>
          <th>Sem Dependabot</th>
          <th>Razão</th>
          <th>Benefício</th>
        </tr>
      </thead>
      <tbody>{rq3d_rows}</tbody>
    </table>
  </div>

  <h3>4.2. Comparação entre Todas as Ferramentas</h3>
  <div class="charts-row">
    <div class="chart-wrap">
      <div class="chart-lbl">Taxa de Repos Vulneráveis por Ferramenta (%)</div>
      {img_tag(charts['rq3_taxa'], 'RQ3 taxa')}
    </div>
    <div class="chart-wrap">
      <div class="chart-lbl">Média de CVEs por Repositório por Ferramenta</div>
      {img_tag(charts['rq3_cves'], 'RQ3 CVEs')}
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Ferramenta</th>
          <th>Repos</th>
          <th>Taxa de Vuln. (%)</th>
          <th>CVEs/Repo (média)</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>{rq3t_rows}</tbody>
    </table>
  </div>

  <div class="conclusion">
    <strong>Conclusão RQ3:</strong>
    O uso de Dependabot e Renovate está associado a menor incidência de vulnerabilidades.
    O Dependabot reduz a taxa de repos vulneráveis em {dep_reduc_taxa:.1f}% e os CVEs/repo em {dep_reduc_cves:.1f}%
    em relação ao baseline. O Renovate apresenta desempenho similar. O Snyk, apesar de ter
    maior taxa de vulnerabilidade, possui amostra reduzida (57 repos), limitando conclusões generalizáveis.
  </div>
</div>

<!-- FOOTER -->
<footer>
  <p>Dashboard Lab04 — Laboratório de Experimentação de Software</p>
  <p>Análise de Dependências Vulneráveis em Projetos Node.js &nbsp;|&nbsp; Gerado em {now}</p>
</footer>

</div>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Carregando dados dos CSVs...")
    data = load_data()

    print("Gerando gráficos...")
    ov   = data["overview"]
    charts = {
        "donut_vuln":  chart_vuln_donut(ov),
        "bots_repos":  chart_bots_repos(data["bots"]),
        "bots_taxa":   chart_bots_taxa(data["bots"]),
        "rq1_metrics": chart_rq1_metrics(data["rq1"]),
        "sev_donut":   chart_severity_donut(data["severity"]),
        "sev_groups":  chart_severity_groups(data["sev_group"]),
        "rq3_taxa":    chart_rq3_taxa(data["rq3_tools"]),
        "rq3_cves":    chart_rq3_cves(data["rq3_tools"]),
    }
    print(f"  {len(charts)} gráficos gerados.")

    print("Montando HTML...")
    html = build_html(data, charts)

    out_path = OUT_DIR / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard salvo em: {out_path}")
    print(f"Tamanho: {len(html)/1024:.0f} KB")


if __name__ == "__main__":
    main()
