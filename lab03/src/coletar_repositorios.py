from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from github_graphql import run_query

TARGET_REPOS = 200
MIN_PRS = 100
PAGE_SIZE = 25  # queries com contagem de PRs por repo são pesadas; 25 evita 502
MAX_RETRIES = 5

SEARCH_QUERY = """
query ($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        owner { login }
        name
        stargazerCount
        mergedPRs: pullRequests(states: MERGED) { totalCount }
        closedPRs: pullRequests(states: CLOSED) { totalCount }
      }
    }
  }
}
"""

CSV_FIELDS = [
    "rank",
    "name_with_owner",
    "owner",
    "repo_name",
    "stars",
    "merged_prs",
    "closed_prs",
    "total_prs",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _output_path() -> Path:
    path = _repo_root() / "data" / "repos.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _fetch_page(star_range: str, after: str | None) -> dict:
    variables = {
        "query": f"stars:{star_range} sort:stars-desc",
        "first": PAGE_SIZE,
        "after": after,
    }
    return run_query(SEARCH_QUERY, variables)


def coletar_repositorios() -> list[dict]:
    # A API de busca do GitHub limita a 1000 resultados por query;
    # dividir por faixas de estrelas contorna esse limite.
    star_ranges = [
        ">=100000",
        "50000..99999",
        "20000..49999",
        "10000..19999",
        "5000..9999",
        "2000..4999",
        "1000..1999",
    ]

    repos: list[dict] = []
    seen: set[str] = set()

    for star_range in star_ranges:
        if len(repos) >= TARGET_REPOS:
            break

        cursor = None
        has_next = True
        consecutive_errors = 0

        while has_next and len(repos) < TARGET_REPOS:
            print(f"  Buscando stars:{star_range} | coletados: {len(repos)} | cursor: {cursor}")

            try:
                data = _fetch_page(star_range, cursor)
                consecutive_errors = 0
            except RuntimeError as exc:
                consecutive_errors += 1
                wait = 10 * consecutive_errors
                print(f"  [AVISO] {exc}. Tentativa {consecutive_errors}/{MAX_RETRIES}. Aguardando {wait}s...")
                if consecutive_errors >= MAX_RETRIES:
                    print(f"  [ERRO] Muitas falhas consecutivas em stars:{star_range}. Abortando.")
                    raise
                time.sleep(wait)
                continue

            search = data["data"]["search"]
            nodes = search["nodes"]
            page_info = search["pageInfo"]

            for node in nodes:
                if not node:
                    continue
                nwo = node["nameWithOwner"]
                if nwo in seen:
                    continue

                merged = node["mergedPRs"]["totalCount"]
                closed = node["closedPRs"]["totalCount"]
                total = merged + closed

                if total < MIN_PRS:
                    continue

                seen.add(nwo)
                repos.append({
                    "name_with_owner": nwo,
                    "owner": node["owner"]["login"],
                    "repo_name": node["name"],
                    "stars": node["stargazerCount"],
                    "merged_prs": merged,
                    "closed_prs": closed,
                    "total_prs": total,
                })

                if len(repos) >= TARGET_REPOS:
                    break

            has_next = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
            time.sleep(1)

    repos.sort(key=lambda r: r["stars"], reverse=True)
    for i, repo in enumerate(repos, start=1):
        repo["rank"] = i

    return repos[:TARGET_REPOS]


def salvar_csv(repos: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows({k: repo[k] for k in CSV_FIELDS} for repo in repos)
    print(f"\nSalvo: {path}  ({len(repos)} repositórios)")


def main() -> None:
    print(f"Coletando os {TARGET_REPOS} repositórios mais populares com >= {MIN_PRS} PRs...\n")
    repos = coletar_repositorios()
    output = _output_path()
    salvar_csv(repos, output)
    print("\nTop 10:")
    for r in repos[:10]:
        print(f"  #{r['rank']:>3}  {r['name_with_owner']:<45}  {r['stars']:>8,} stars  PRs: {r['total_prs']:>6,}")


if __name__ == "__main__":
    main()
