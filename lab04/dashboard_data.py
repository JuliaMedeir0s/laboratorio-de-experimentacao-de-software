"""Utilities to parse lab04/dataset/ANALISE_RQ.md into structured data.

Designed to be stdlib-only so it works in the course environment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_ANALISE_PATH = Path(__file__).parent / "dataset" / "ANALISE_RQ.md"


def _to_number(value: str) -> float:
    """Parse numbers in pt-BR formatting.

    Accepts forms like:
    - "9.982" -> 9982
    - "56,26%" -> 56.26
    - "58.192" -> 58192
    - "16,88" -> 16.88
    """

    value = value.strip()
    value = value.replace("**", "")

    # Extract inside parentheses if like "5.616 (56,26%)".
    # Caller can decide which part to use.
    if value.endswith("%"):  # percentage
        value = value[:-1].strip()

    # Remove thousands separators '.' and swap decimal ',' -> '.'
    value = value.replace(".", "")
    value = value.replace(",", ".")

    # Keep only digits, dot, minus
    value = re.sub(r"[^0-9.\-]", "", value)
    if value == "" or value == "." or value == "-":
        raise ValueError(f"Cannot parse number from: {value!r}")

    return float(value)


def _parse_markdown_table(lines: list[str], start_index: int) -> tuple[list[str], list[list[str]], int]:
    """Parse a markdown table starting at start_index (line beginning with '|').

    Returns (headers, rows, next_index).
    """

    i = start_index
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    i += 1

    # separator line
    if i < len(lines) and re.match(r"^\|?\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?$", lines[i].strip()):
        i += 1

    rows: list[list[str]] = []
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if not line.strip().startswith("|"):
            break
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        # Allow tables with trailing empty columns
        if len(cols) < len(header):
            cols += [""] * (len(header) - len(cols))
        rows.append(cols)
        i += 1

    return header, rows, i


def load_analise(path: Path | None = None) -> dict[str, Any]:
    """Load analysis from ANALISE_RQ.md and return a structured dict."""

    analise_path = path or _ANALISE_PATH
    text = analise_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Header metadata
    dataset_repos = None
    periodo = None

    for line in lines[:40]:
        if line.startswith("**Dataset:**"):
            dataset_repos = line.split(":", 1)[1].strip()
        if line.startswith("**Período:**"):
            periodo = line.split(":", 1)[1].strip()

    out: dict[str, Any] = {
        "meta": {
            "dataset": dataset_repos,
            "periodo": periodo,
        },
        "tables": {},
    }

    # Capture the main tables we need.
    table_names = {
        "Taxas Absoluta e Normalizadas": "dataset_overview",
        "Por Repositório (média por grupo)": "rq1_by_repo_group",
        "Distribuição por Grupo de Dependência-Manager": "bots_distribution",
        "Distribuição Agregada": "severity_distribution",
        "Distribuição Normalizada": "severity_by_group",
        "Comparação Direta": "rq3_comparison_direct",
        "Comparação com Outras Ferramentas": "rq3_tools_comparison",
    }

    i = 0
    current_section = None
    while i < len(lines):
        line = lines[i].strip()

        # Identify section headers to label the next table.
        if line.startswith("### "):
            current_section = line.replace("### ", "").strip()

        # Some tables are under ####
        if line.startswith("#### "):
            current_section = line.replace("#### ", "").strip()

        if line.startswith("|"):
            headers, rows, next_i = _parse_markdown_table(lines, i)
            key = None

            # Match by the last seen section header.
            if current_section:
                for section_prefix, name in table_names.items():
                    if current_section.startswith(section_prefix):
                        key = name
                        break

            # Special-case: "Distribuição Agregada (todos os ... )" is a ### line.
            if key is None and current_section and current_section.startswith("Distribuição Agregada"):
                key = "severity_distribution"

            if key:
                out["tables"][key] = {
                    "headers": headers,
                    "rows": rows,
                    "section": current_section,
                }

            i = next_i
            continue

        i += 1

    return out


def extract_metrics(analise: dict[str, Any]) -> dict[str, Any]:
    """Compute a normalized metrics dict from parsed tables."""

    tables = analise.get("tables", {})

    dataset = {}
    t = tables.get("dataset_overview")
    if t:
        for metric, value in t["rows"]:
            metric = metric.replace("**", "").strip()
            value = value.strip()
            dataset[metric] = value

    bots = []
    t = tables.get("bots_distribution")
    if t:
        for row in t["rows"]:
            # Tool | Repos | % | Repos Vulner. | Taxa | CVEs/Repo | Dependências Vulner./Repo
            tool = row[0].replace("**", "").strip()
            bots.append(
                {
                    "tool": tool,
                    "repos": int(_to_number(row[1])),
                    "pct": float(_to_number(row[2])),
                    "repos_vulner": int(_to_number(row[3])),
                    "taxa": float(_to_number(row[4])),
                    "cves_per_repo": float(_to_number(row[5])),
                    "vuln_deps_per_repo": float(_to_number(row[6])),
                }
            )

    severity = []
    t = tables.get("severity_distribution")
    if t:
        for row in t["rows"]:
            # Severidade | Contagem | %
            sev = row[0].replace("**", "").strip()
            if sev.upper() == "TOTAL":
                continue
            severity.append(
                {
                    "severity": sev,
                    "count": int(_to_number(row[1])),
                    "pct": float(_to_number(row[2])),
                }
            )

    sev_by_group = []
    t = tables.get("severity_by_group")
    if t:
        for row in t["rows"]:
            # Severity | Com Dependabot | Sem Dependabot | Diferença
            sev = row[0].replace("**", "").strip()
            sev_by_group.append(
                {
                    "severity": sev,
                    "with_dependabot_pct": float(_to_number(row[1])),
                    "without_dependabot_pct": float(_to_number(row[2])),
                    "diff_pp": float(_to_number(row[3])),
                }
            )

    rq1_repo_group = {}
    t = tables.get("rq1_by_repo_group")
    if t:
        for metric, with_v, without_v in t["rows"]:
            rq1_repo_group[metric.replace("**", "").strip()] = {
                "with": float(_to_number(with_v)),
                "without": float(_to_number(without_v)),
            }

    rq3_direct = []
    t = tables.get("rq3_comparison_direct")
    if t:
        for row in t["rows"]:
            # Métrica | Com Dependabot | Sem Dependabot | Razão (Sem/Com) | Benefício
            rq3_direct.append(
                {
                    "metric": row[0].replace("**", "").strip(),
                    "with_dependabot": row[1].strip(),
                    "without_dependabot": row[2].strip(),
                    "ratio": row[3].strip(),
                    "benefit": row[4].strip(),
                }
            )

    rq3_tools = []
    t = tables.get("rq3_tools_comparison")
    if t:
        for row in t["rows"]:
            rq3_tools.append(
                {
                    "tool": row[0].replace("**", "").strip(),
                    "repos": int(_to_number(row[1])),
                    "taxa": float(_to_number(row[2])),
                    "cves_per_repo": float(_to_number(row[3])),
                    "status": row[4].strip(),
                }
            )

    # Convert some key dataset metrics into numbers
    total_repos = None
    repos_with_v = None
    repos_without_v = None
    total_vuln_deps = None
    total_direct_deps = None
    total_resolved_versions = None
    total_cves = None

    if dataset:
        total_repos = int(_to_number(dataset.get("Total de repositórios analisados", "0")))
        repos_with_v = dataset.get("Repositórios com vulnerabilidades detectadas", "")
        repos_without_v = dataset.get("Repositórios sem vulnerabilidades", "")
        total_vuln_deps = int(_to_number(dataset.get("Dependências vulneráveis (total)", "0")))
        total_direct_deps = int(_to_number(dataset.get("Dependências diretas (total)", "0")))
        total_resolved_versions = int(_to_number(dataset.get("Versões resolvidas (total)", "0")))
        total_cves = int(_to_number(dataset.get("CVEs associados (total)", "0")))

    def _split_count_pct(s: str) -> tuple[int | None, float | None]:
        m = re.match(r"\s*([0-9.]+)\s*\(([^)]+)\)\s*", s)
        if not m:
            try:
                return int(_to_number(s)), None
            except Exception:
                return None, None
        return int(_to_number(m.group(1))), float(_to_number(m.group(2)))

    repos_with_v_count, repos_with_v_pct = _split_count_pct(repos_with_v or "")
    repos_without_v_count, repos_without_v_pct = _split_count_pct(repos_without_v or "")

    return {
        "meta": analise.get("meta", {}),
        "dataset": {
            "total_repos": total_repos,
            "repos_with_vuln": repos_with_v_count,
            "repos_with_vuln_pct": repos_with_v_pct,
            "repos_without_vuln": repos_without_v_count,
            "repos_without_vuln_pct": repos_without_v_pct,
            "total_vulnerable_deps": total_vuln_deps,
            "total_direct_deps": total_direct_deps,
            "total_resolved_versions": total_resolved_versions,
            "total_cves": total_cves,
        },
        "bots": bots,
        "severity": severity,
        "severity_by_group": sev_by_group,
        "rq1_by_repo_group": rq1_repo_group,
        "rq3_comparison_direct": rq3_direct,
        "rq3_tools_comparison": rq3_tools,
    }
