from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from github_graphql import run_query

# query pesada (participants, comments, reviews, body); 10 por página evita 502
PAGE_SIZE = 10
DEFAULT_MAX_PRS = 100

PR_QUERY = """
query ($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: [MERGED, CLOSED]
      first: $first
      after: $after
      orderBy: { field: CREATED_AT, direction: DESC }
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        state
        createdAt
        closedAt
        mergedAt
        body
        additions
        deletions
        changedFiles
        participants { totalCount }
        comments { totalCount }
        reviews { totalCount }
      }
    }
  }
}
"""

RAW_FIELDS = [
    "repo",
    "pr_number",
    "title",
    "status",
    "created_at",
    "closed_at",
    "merged_at",
    "analysis_time_hours",
    "files_changed",
    "lines_added",
    "lines_removed",
    "body_length",
    "participants_count",
    "comments_count",
    "reviews_count",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    # fromisoformat não aceita o sufixo "Z" em Python < 3.11
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _analysis_hours(node: dict) -> float | None:
    created = _parse_dt(node["createdAt"])
    if created is None:
        return None
    end_str = node["mergedAt"] if node["state"] == "MERGED" else node["closedAt"]
    end = _parse_dt(end_str)
    if end is None:
        return None
    return (end - created).total_seconds() / 3600


def _process_node(repo_nwo: str, node: dict) -> dict | None:
    reviews = node["reviews"]["totalCount"]
    if reviews < 1:
        return None

    hours = _analysis_hours(node)
    if hours is None or hours <= 1.0:
        return None

    return {
        "repo": repo_nwo,
        "pr_number": node["number"],
        "title": (node["title"] or "").replace("\n", " ").strip(),
        "status": node["state"],
        "created_at": node["createdAt"],
        "closed_at": node["closedAt"] or "",
        "merged_at": node["mergedAt"] or "",
        "analysis_time_hours": round(hours, 4),
        "files_changed": node["changedFiles"],
        "lines_added": node["additions"],
        "lines_removed": node["deletions"],
        "body_length": len(node["body"] or ""),
        "participants_count": node["participants"]["totalCount"],
        "comments_count": node["comments"]["totalCount"],
        "reviews_count": reviews,
    }


MAX_RETRIES = 5

def coletar_prs_repositorio(owner: str, name: str, max_prs: int) -> list[dict]:
    prs: list[dict] = []
    cursor = None
    repo_nwo = f"{owner}/{name}"
    total_fetched = 0
    consecutive_errors = 0

    while True:
        remaining = max_prs - total_fetched
        if remaining <= 0:
            break

        fetch = min(PAGE_SIZE, remaining)
        try:
            data = run_query(PR_QUERY, {
                "owner": owner,
                "name": name,
                "first": fetch,
                "after": cursor,
            })
            consecutive_errors = 0
        except RuntimeError as exc:
            consecutive_errors += 1
            wait = 15 * consecutive_errors
            print(f"    [AVISO] {repo_nwo}: {exc}. Tentativa {consecutive_errors}/{MAX_RETRIES}. Aguardando {wait}s...")
            if consecutive_errors >= MAX_RETRIES:
                print(f"    [PULANDO] {repo_nwo}: muitas falhas consecutivas, repositório ignorado.")
                return prs
            time.sleep(wait)
            continue

        repo_data = data["data"]["repository"]
        if repo_data is None:
            print(f"    [AVISO] {repo_nwo}: repositório não encontrado ou sem acesso.")
            break

        pr_data = repo_data["pullRequests"]
        nodes = pr_data["nodes"]
        page_info = pr_data["pageInfo"]

        for node in nodes:
            total_fetched += 1
            record = _process_node(repo_nwo, node)
            if record:
                prs.append(record)

        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
        time.sleep(0.5)

    return prs


def salvar_raw(prs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(prs)


def salvar_consolidado(all_prs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(all_prs)
    print(f"\nDataset consolidado: {path}  ({len(all_prs)} PRs)")


def _ler_repos(csv_path: Path) -> list[tuple[str, str]]:
    repos = []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            repos.append((row["owner"], row["repo_name"]))
    return repos


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta PRs dos repositórios em data/repos.csv")
    parser.add_argument(
        "--max-prs", type=int, default=DEFAULT_MAX_PRS,
        help=f"Máximo de PRs verificados por repositório (padrão: {DEFAULT_MAX_PRS})",
    )
    parser.add_argument(
        "--repo", type=str, default=None,
        help="Processar somente um repositório (ex: torvalds/linux)",
    )
    args = parser.parse_args()

    root = _repo_root()
    repos_csv = root / "data" / "repos.csv"

    if not repos_csv.exists():
        print(f"[ERRO] {repos_csv} não encontrado. Execute coletar_repositorios.py primeiro.")
        sys.exit(1)

    all_repos = _ler_repos(repos_csv)

    if args.repo:
        owner, name = args.repo.split("/", 1)
        all_repos = [(owner, name)]

    raw_dir = root / "data" / "raw"
    all_prs: list[dict] = []

    print(f"Coletando PRs de {len(all_repos)} repositório(s) | max {args.max_prs} PRs por repo\n")

    for i, (owner, name) in enumerate(all_repos, start=1):
        repo_nwo = f"{owner}/{name}"
        raw_path = raw_dir / f"{owner}_{name}_prs.csv"

        if raw_path.exists():
            print(f"  [{i:>3}/{len(all_repos)}] {repo_nwo:<45} [já coletado, carregando...]")
            with raw_path.open(encoding="utf-8") as f:
                existing = list(csv.DictReader(f))
            for r in existing:
                r["pr_number"] = int(r["pr_number"])
                r["analysis_time_hours"] = float(r["analysis_time_hours"])
                r["files_changed"] = int(r["files_changed"])
                r["lines_added"] = int(r["lines_added"])
                r["lines_removed"] = int(r["lines_removed"])
                r["body_length"] = int(r["body_length"])
                r["participants_count"] = int(r["participants_count"])
                r["comments_count"] = int(r["comments_count"])
                r["reviews_count"] = int(r["reviews_count"])
            all_prs.extend(existing)
            continue

        print(f"  [{i:>3}/{len(all_repos)}] {repo_nwo:<45}", end=" ", flush=True)
        prs = coletar_prs_repositorio(owner, name, args.max_prs)
        salvar_raw(prs, raw_path)
        all_prs.extend(prs)
        print(f"-> {len(prs)} PRs válidos")
        time.sleep(1)

    processed_path = root / "data" / "processed" / "prs.csv"
    salvar_consolidado(all_prs, processed_path)

    merged = sum(1 for p in all_prs if p["status"] == "MERGED")
    closed = sum(1 for p in all_prs if p["status"] == "CLOSED")
    print(f"\nResumo:")
    print(f"  Total de PRs: {len(all_prs)}")
    print(f"  MERGED: {merged}  |  CLOSED: {closed}")


if __name__ == "__main__":
    main()
