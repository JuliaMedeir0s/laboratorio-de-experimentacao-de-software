from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from github_graphql import run_query

SEARCH_QUERY = """
query ($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Repository {
        name
        owner { login }
        nameWithOwner
        stargazerCount
      }
    }
  }
}
"""

REPO_FIELDS = """
  name
  nameWithOwner
  owner { login }
  stargazerCount
  createdAt
  pushedAt
  primaryLanguage { name }
  releases { totalCount }
  pullRequests(states: MERGED) { totalCount }
  issues { totalCount }
  closedIssues: issues(states: CLOSED) { totalCount }
  isFork
  isArchived
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(payload: Dict[str, Any], out_path: Path) -> None:
    _ensure_parent(out_path)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    _ensure_parent(out_path)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _escape_graphql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_repo_details_query(repos: List[Dict[str, str]]) -> str:
    lines = ["query {"]
    for index, repo in enumerate(repos):
        owner = _escape_graphql_string(repo["owner"])
        name = _escape_graphql_string(repo["name"])
        lines.append(f'  repo{index}: repository(owner: "{owner}", name: "{name}") {{')
        lines.append(REPO_FIELDS)
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def _extract_rows(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for repo in nodes:
        lang = None
        if repo.get("primaryLanguage"):
            lang = repo["primaryLanguage"].get("name")

        rows.append(
            {
                "name_with_owner": repo.get("nameWithOwner"),
                "owner_login": repo.get("owner", {}).get("login"),
                "stars": repo.get("stargazerCount"),
                "created_at": repo.get("createdAt"),
                "pushed_at": repo.get("pushedAt"),
                "primary_language": lang,
                "releases_total": repo.get("releases", {}).get("totalCount"),
                "prs_merged_total": repo.get("pullRequests", {}).get("totalCount"),
                "issues_total": repo.get("issues", {}).get("totalCount"),
                "issues_closed_total": repo.get("closedIssues", {}).get("totalCount"),
                "is_fork": repo.get("isFork"),
                "is_archived": repo.get("isArchived"),
            }
        )
    return rows


def _stars_ranges() -> List[Tuple[Optional[int], Optional[int]]]:
    """
    Estratégia: começar no topo (mais estrelas) e descer por blocos.
    Cada tupla é (min, max); quando max=None, a leitura é ">= min".
    """
    return [
        (100000, None),
        (50000, 99999),
        (20000, 49999),
        (10000, 19999),
        (5000, 9999),
        (2000, 4999),
    ]


def _build_search_query_for_range(stars_min: int, stars_max: Optional[int]) -> str:
    if stars_max is None:
        return f"stars:>={stars_min} sort:stars"
    return f"stars:{stars_min}..{stars_max} sort:stars"


def fetch_code_repos_across_ranges(
    target_code_count: int,
    batch_size: int = 10,
    page_size: int = 50,
    max_pages_per_range: int = 25,
) -> Dict[str, Any]:
    """
    Processo geral:
    1) dividir a busca por faixas de estrelas para contornar o teto de 1000 resultados por query;
    2) paginar dentro de cada faixa;
    3) buscar detalhes em lotes e aceitar apenas repositórios com linguagem principal.
    """
    accepted: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    meta_ranges: List[Dict[str, Any]] = []

    for stars_min, stars_max in _stars_ranges():
        if len(accepted) >= target_code_count:
            break

        q = _build_search_query_for_range(stars_min, stars_max)
        after: Optional[str] = None
        pages = 0
        scanned_in_range = 0
        accepted_in_range = 0

        print(f"\n=== RANGE stars {stars_min}..{stars_max if stars_max is not None else 'INF'} ===")

        while len(accepted) < target_code_count and pages < max_pages_per_range:
            pages += 1
            variables = {"query": q, "first": page_size, "after": after}
            resp = run_query(SEARCH_QUERY, variables)
            search = resp["data"]["search"]
            nodes = search["nodes"]

            repos: List[Dict[str, str]] = []
            for node in nodes:
                owner = node.get("owner", {}).get("login")
                name = node.get("name")
                nwo = node.get("nameWithOwner")
                if owner and name and nwo and nwo not in seen:
                    repos.append({"owner": owner, "name": name, "nwo": nwo})

            scanned_in_range += len(repos)
            if not repos:
                # Se esta página não trouxe candidatos inéditos, seguimos para a próxima
                # somente quando houver cursor disponível.
                if not search["pageInfo"]["hasNextPage"]:
                    break
                after = search["pageInfo"]["endCursor"]
                continue

            # Agora enriquecemos os candidatos em lotes menores para controlar o custo
            # da query de detalhes e manter o fluxo previsível.
            for i in range(0, len(repos), batch_size):
                batch = repos[i : i + batch_size]
                print(f"[DETAILS] batch {i+1}..{min(i+batch_size, len(repos))} (range page {pages})")

                details_query = _build_repo_details_query(batch)
                details = run_query(details_query, {})

                for key in sorted(details["data"].keys()):
                    repo = details["data"][key]
                    nwo = repo.get("nameWithOwner")
                    if not nwo or nwo in seen:
                        continue

                    lang = None
                    if repo.get("primaryLanguage"):
                        lang = repo["primaryLanguage"].get("name")

                    # Critério de aceite: manter apenas projetos com linguagem principal
                    # definida, para evitar entradas sem base de código clara.
                    if lang:
                        accepted.append(repo)
                        accepted_in_range += 1
                        seen.add(nwo)

                    # Mesmo quando rejeitado, marcamos como visto para não processar o
                    # mesmo repositório novamente em páginas/faixas seguintes.
                    else:
                        seen.add(nwo)

                    if len(accepted) >= target_code_count:
                        break

                if len(accepted) >= target_code_count:
                    break

            if not search["pageInfo"]["hasNextPage"]:
                break
            after = search["pageInfo"]["endCursor"]

        meta_ranges.append(
            {
                "stars_min": stars_min,
                "stars_max": stars_max,
                "pages": pages,
                "scanned_candidates": scanned_in_range,
                "accepted_code": accepted_in_range,
                "query": q,
            }
        )

        print(f"[RANGE DONE] accepted_code={accepted_in_range}, total_accepted={len(accepted)}")

    return {"data": {"search": {"nodes": accepted, "meta": {"ranges": meta_ranges, "accepted": len(accepted)}}}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab01: coletar 1000 repositórios de código mais estrelados.")
    parser.add_argument("--first", type=int, default=1000, help="Quantidade de repositórios de código (default: 1000)")
    parser.add_argument("--batch-size", type=int, default=10, help="Repos por query de detalhes (default: 10)")
    parser.add_argument("--page-size", type=int, default=50, help="Repos por página do search (default: 50)")
    parser.add_argument(
        "--out-json",
        type=Path,
        default=_repo_root() / "lab01" / "data" / "raw" / "top_1000.json",
        help="Caminho do JSON bruto",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=_repo_root() / "lab01" / "data" / "processed" / "top_1000.csv",
        help="Caminho do CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    response = fetch_code_repos_across_ranges(
        target_code_count=args.first,
        batch_size=args.batch_size,
        page_size=args.page_size,
        max_pages_per_range=25,
    )

    nodes = response["data"]["search"]["nodes"]
    rows = _extract_rows(nodes)

    write_json(response, args.out_json)
    write_csv(rows, args.out_csv)

    print("\nDONE")
    print(f"Accepted (codigo): {len(rows)} / Target: {args.first}")
    print(f"Raw JSON: {args.out_json}")
    print(f"CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
