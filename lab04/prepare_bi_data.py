#!/usr/bin/env python3
"""Prepare BI-ready tables (CSV) from lab04/dataset/ANALISE_RQ.md.

Outputs go to lab04/bi/tables/.

This is intentionally simple (stdlib only) so it runs anywhere.
"""

from __future__ import annotations

import csv
from pathlib import Path

from dashboard_data import extract_metrics, load_analise


ROOT = Path(__file__).parent
OUT_DIR = ROOT / "bi" / "tables"


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def main() -> None:
    analise = load_analise()
    metrics = extract_metrics(analise)

    # dataset_overview (key-value)
    ds = metrics["dataset"]
    write_csv(
        OUT_DIR / "dataset_overview.csv",
        ["metric", "value"],
        [
            ["dataset", metrics["meta"].get("dataset")],
            ["periodo", metrics["meta"].get("periodo")],
            ["total_repos", ds.get("total_repos")],
            ["repos_with_vuln", ds.get("repos_with_vuln")],
            ["repos_with_vuln_pct", ds.get("repos_with_vuln_pct")],
            ["repos_without_vuln", ds.get("repos_without_vuln")],
            ["repos_without_vuln_pct", ds.get("repos_without_vuln_pct")],
            ["total_vulnerable_deps", ds.get("total_vulnerable_deps")],
            ["total_direct_deps", ds.get("total_direct_deps")],
            ["total_resolved_versions", ds.get("total_resolved_versions")],
            ["total_cves", ds.get("total_cves")],
        ],
    )

    # bots_distribution
    write_csv(
        OUT_DIR / "bots_distribution.csv",
        [
            "tool",
            "repos",
            "pct",
            "repos_vulner",
            "taxa",
            "cves_per_repo",
            "vuln_deps_per_repo",
        ],
        [
            [
                b["tool"],
                b["repos"],
                b["pct"],
                b["repos_vulner"],
                b["taxa"],
                b["cves_per_repo"],
                b["vuln_deps_per_repo"],
            ]
            for b in metrics["bots"]
        ],
    )

    # severity_distribution
    write_csv(
        OUT_DIR / "severity_distribution.csv",
        ["severity", "count", "pct"],
        [[s["severity"], s["count"], s["pct"]] for s in metrics["severity"]],
    )

    # severity_by_group
    write_csv(
        OUT_DIR / "severity_by_group_dependabot.csv",
        ["severity", "with_dependabot_pct", "without_dependabot_pct", "diff_pp"],
        [
            [
                s["severity"],
                s["with_dependabot_pct"],
                s["without_dependabot_pct"],
                s["diff_pp"],
            ]
            for s in metrics["severity_by_group"]
        ],
    )

    # rq1 per-repo averages (with vs without)
    rq1 = metrics["rq1_by_repo_group"]
    write_csv(
        OUT_DIR / "rq1_repo_group_averages.csv",
        ["metric", "with_vulnerability", "without_vulnerability"],
        [[k, v["with"], v["without"]] for k, v in rq1.items()],
    )

    # rq3 comparison direct
    write_csv(
        OUT_DIR / "rq3_comparison_direct.csv",
        ["metric", "with_dependabot", "without_dependabot", "ratio", "benefit"],
        [
            [
                r["metric"],
                r["with_dependabot"],
                r["without_dependabot"],
                r["ratio"],
                r["benefit"],
            ]
            for r in metrics["rq3_comparison_direct"]
        ],
    )

    # rq3 tools comparison
    write_csv(
        OUT_DIR / "rq3_tools_comparison.csv",
        ["tool", "repos", "taxa", "cves_per_repo", "status"],
        [
            [t["tool"], t["repos"], t["taxa"], t["cves_per_repo"], t["status"]]
            for t in metrics["rq3_tools_comparison"]
        ],
    )

    print("✅ BI tables generated in:", OUT_DIR)


if __name__ == "__main__":
    main()
