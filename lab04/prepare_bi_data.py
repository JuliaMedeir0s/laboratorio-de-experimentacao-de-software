#!/usr/bin/env python3
"""Generate BI-ready CSV tables from novo/summary_package-lock.json.

Outputs go to bi/tables/.
"""

import csv
import json
from pathlib import Path

ROOT     = Path(__file__).parent
SRC_JSON = ROOT / "dataset" / "summary_package-lock.json"
OUT_DIR  = ROOT / "bi" / "tables"

BOT_ORDER = ["none", "dependabot", "codeql", "renovate", "mend", "snyk", "npm_audit", "pyup"]
BOT_LABEL = {
    "none":      "Sem bot",
    "dependabot":"Dependabot",
    "codeql":    "CodeQL",
    "renovate":  "Renovate",
    "mend":      "Mend",
    "snyk":      "Snyk",
    "npm_audit": "npm_audit",
    "pyup":      "PyUp",
}
SEV_ORDER = ["MEDIUM", "HIGH", "LOW", "CRITICAL", "UNKNOWN"]
CAT_ORDER = ["update", "update_security", "none", "audit_automation",
             "security_remediation", "security_automation", "security_scanner"]
CAT_LABEL = {
    "update":               "update (Renovate/PyUp)",
    "update_security":      "update_security (Dependabot)",
    "none":                 "none (sem automação)",
    "audit_automation":     "audit_automation (npm_audit)",
    "security_remediation": "security_remediation (Mend)",
    "security_automation":  "security_automation (CodeQL)",
    "security_scanner":     "security_scanner (Snyk)",
}


def r2(x):
    return round(x, 2)


def write_csv(name, headers, rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / name
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in rows:
            w.writerow(row)
    print(f"  {p.name}")


def main():
    data = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    bbd  = data["by_dependency_bot"]
    bbc  = data["by_dependency_bot_category"]

    total_repos     = data["total_repos"]
    total_cves      = sum(b["total_cves"]                for b in bbd.values())
    total_vuln_deps = sum(b["vulnerable_dependencies"]   for b in bbd.values())
    total_direct    = sum(b["total_direct_dependencies"] for b in bbd.values())
    total_resolved  = sum(b["total_resolved_versions"]   for b in bbd.values())
    repos_with_vuln = sum(b["repos_with_any_vuln"]       for b in bbd.values())
    repos_without   = total_repos - repos_with_vuln

    # ── dataset_overview ──────────────────────────────────────────────────────
    write_csv("dataset_overview.csv",
        ["metric", "value"],
        [
            ["total_repos",             total_repos],
            ["repos_with_vuln",         repos_with_vuln],
            ["repos_with_vuln_pct",     r2(repos_with_vuln / total_repos * 100)],
            ["repos_without_vuln",      repos_without],
            ["repos_without_vuln_pct",  r2(repos_without   / total_repos * 100)],
            ["total_vulnerable_deps",   total_vuln_deps],
            ["total_direct_deps",       total_direct],
            ["total_resolved_versions", total_resolved],
            ["total_cves",              total_cves],
        ]
    )

    # ── bots_distribution ─────────────────────────────────────────────────────
    bots_rows = []
    for key in BOT_ORDER:
        b = bbd[key]
        n    = b["repos"]
        v    = b["repos_with_any_vuln"]
        cves = b["total_cves"]
        vd   = b["vulnerable_dependencies"]
        res  = b["total_resolved_versions"]
        bots_rows.append([
            BOT_LABEL[key], n,
            r2(n / total_repos * 100),
            v,
            r2(v / n * 100),
            r2(cves / n),
            r2(vd / n),
            r2(vd / res * 100),
            r2(cves / res * 100),
        ])
    write_csv("bots_distribution.csv",
        ["tool","repos","pct","repos_vulner","taxa","cves_per_repo",
         "vuln_deps_per_repo","vuln_per_100_resolved","cves_per_100_resolved"],
        bots_rows
    )

    # ── severity_distribution ─────────────────────────────────────────────────
    sev_agg = {s: 0 for s in SEV_ORDER}
    for b in bbd.values():
        for s, c in b["cve_severity_distribution"].items():
            sev_agg[s.upper()] += c
    total_sev = sum(sev_agg.values())
    write_csv("severity_distribution.csv",
        ["severity", "count", "pct"],
        [[s, sev_agg[s], r2(sev_agg[s] / total_sev * 100)] for s in SEV_ORDER]
    )

    # ── severity_by_bot (normalized % per bot) ────────────────────────────────
    sev_by_bot_headers = ["severity"] + [BOT_LABEL[k] for k in BOT_ORDER]
    sev_by_bot_rows = []
    for s in SEV_ORDER:
        row = [s]
        for key in BOT_ORDER:
            b   = bbd[key]
            tot = sum(b["cve_severity_distribution"].values())
            cnt = b["cve_severity_distribution"].get(s, 0)
            row.append(r2(cnt / tot * 100) if tot else 0)
        sev_by_bot_rows.append(row)
    write_csv("severity_by_bot.csv", sev_by_bot_headers, sev_by_bot_rows)

    # ── rq1_repo_group_averages ───────────────────────────────────────────────
    # Values from ANALISE_RQ.md (per-group breakdown not in JSON)
    write_csv("rq1_repo_group_averages.csv",
        ["metric", "with_vulnerability", "without_vulnerability"],
        [
            ["Dependências diretas/repo",     16.74, 11.37],
            ["Versões resolvidas/repo",       120.83,  3.10],
            ["Dependências vulneráveis/repo",  11.12,  0.0],
            ["CVEs/repo",                      24.17,  0.0],
        ]
    )

    # ── rq3_bot_comparison ────────────────────────────────────────────────────
    bot_keys  = [k for k in BOT_ORDER if k != "none"]
    n_bot     = sum(bbd[k]["repos"]                    for k in bot_keys)
    v_bot     = sum(bbd[k]["repos_with_any_vuln"]      for k in bot_keys)
    cves_bot  = sum(bbd[k]["total_cves"]               for k in bot_keys)
    vdeps_bot = sum(bbd[k]["vulnerable_dependencies"]  for k in bot_keys)
    res_bot   = sum(bbd[k]["total_resolved_versions"]  for k in bot_keys)

    bn = bbd["none"]
    n_none     = bn["repos"]
    v_none     = bn["repos_with_any_vuln"]
    cves_none  = bn["total_cves"]
    vdeps_none = bn["vulnerable_dependencies"]
    res_none   = bn["total_resolved_versions"]

    taxa_bot  = r2(v_bot  / n_bot  * 100)
    taxa_none = r2(v_none / n_none * 100)

    write_csv("rq3_bot_comparison.csv",
        ["metric", "com_bot", "sem_bot", "diff_pp"],
        [
            ["Taxa repos vulneráveis (%)",
             taxa_bot, taxa_none, r2(taxa_bot - taxa_none)],
            ["CVEs/repo",
             r2(cves_bot/n_bot), r2(cves_none/n_none),
             r2(cves_bot/n_bot - cves_none/n_none)],
            ["Vuln./100 versões resolvidas",
             r2(vdeps_bot/res_bot*100), r2(vdeps_none/res_none*100),
             r2(vdeps_bot/res_bot*100 - vdeps_none/res_none*100)],
            ["CVEs/100 versões resolvidas",
             r2(cves_bot/res_bot*100), r2(cves_none/res_none*100),
             r2(cves_bot/res_bot*100 - cves_none/res_none*100)],
        ]
    )

    # ── rq4_categories ────────────────────────────────────────────────────────
    rq4_rows = []
    for key in CAT_ORDER:
        c    = bbc[key]
        n    = c["repos"]
        v    = c["repos_with_any_vuln"]
        vd   = c["vulnerable_dependencies"]
        cves = c["total_cves"]
        res  = c["total_resolved_versions"]
        rq4_rows.append([
            CAT_LABEL[key], n,
            r2(v / n * 100),
            r2(vd / res * 100),
            r2(cves / res * 100),
        ])
    write_csv("rq4_categories.csv",
        ["category","repos","taxa_vuln_pct","vuln_per_100_resolved","cves_per_100_resolved"],
        rq4_rows
    )

    # ── rq5_multi_bot ─────────────────────────────────────────────────────────
    # Values from ANALISE_RQ.md
    write_csv("rq5_multi_bot.csv",
        ["n_bots","repos","taxa_vuln_pct","vuln_per_100_resolved","cves_per_100_resolved"],
        [
            [0,    8964, 57.08, 9.79, 21.53],
            [1,     736, 57.74, 6.59, 12.98],
            [2,     245, 58.78, 4.03,  8.18],
            ["3+",   37, 62.16, 4.91,  9.13],
        ]
    )

    print("✅ BI tables updated in:", OUT_DIR)


if __name__ == "__main__":
    main()
