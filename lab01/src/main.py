from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from github_graphql import run_query

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
    updatedAt
    primaryLanguage { name }
    releases { totalCount }
    pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _extract_rows(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for repo in nodes:
        primary_language = None
        if repo.get("primaryLanguage"):
            primary_language = repo["primaryLanguage"].get("name")
        rows.append(
            {
                "name_with_owner": repo.get("nameWithOwner"),
                "owner_login": repo.get("owner", {}).get("login"),
                "stars": repo.get("stargazerCount"),
                "created_at": repo.get("createdAt"),
                "updated_at": repo.get("updatedAt"),
                "primary_language": primary_language,
                "releases_total": repo.get("releases", {}).get("totalCount"),
                "prs_merged_total": repo.get("pullRequests", {}).get("totalCount"),
                "issues_total": repo.get("issues", {}).get("totalCount"),
                "issues_closed_total": repo.get("closedIssues", {}).get("totalCount"),
            }
        )
    return rows


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


def write_json(payload: Dict[str, Any], out_path: Path) -> None:
    _ensure_parent(out_path)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _escape_graphql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_repo_details_query(repos: List[Dict[str, str]]) -> str:
    lines = ["query {"]
    for index, repo in enumerate(repos):
        owner = _escape_graphql_string(repo["owner"])
        name = _escape_graphql_string(repo["name"])
        lines.append(
            f"  repo{index}: repository(owner: \"{owner}\", name: \"{name}\") {{"
        )
        lines.append(REPO_FIELDS)
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def _fetch_search_repos(query: str, total: int) -> List[Dict[str, str]]:
    all_repos: List[Dict[str, str]] = []
    after: Optional[str] = None
    page_size_limit = 50
    while len(all_repos) < total:
        remaining = total - len(all_repos)
        page_size = page_size_limit if remaining > page_size_limit else remaining
        variables = {"query": query, "first": page_size, "after": after}
        response = run_query(SEARCH_QUERY, variables)
        search = response["data"]["search"]
        nodes = search["nodes"]
        for node in nodes:
            owner = node.get("owner", {}).get("login")
            name = node.get("name")
            if owner and name:
                all_repos.append({"owner": owner, "name": name})
        if not search["pageInfo"]["hasNextPage"]:
            break
        after = search["pageInfo"]["endCursor"]
    return all_repos


def fetch_repositories(query: str, total: int) -> Dict[str, Any]:
    repos = _fetch_search_repos(query, total)
    nodes: List[Dict[str, Any]] = []
    batch_size = 10
    for index in range(0, len(repos), batch_size):
        batch = repos[index : index + batch_size]
        details_query = _build_repo_details_query(batch)
        response = run_query(details_query, {})
        for key in sorted(response["data"].keys()):
            nodes.append(response["data"][key])
    return {"data": {"search": {"nodes": nodes}}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab01S01 GraphQL data fetch")
    parser.add_argument(
        "--first",
        type=int,
        default=100,
        help="Number of repositories to fetch (default: 100)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="stars:>0 sort:stars-desc",
        help="GitHub search query for repositories",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=_repo_root() / "lab01" / "data" / "raw" / "top_100.json",
        help="Path to write raw JSON response",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=_repo_root() / "lab01" / "data" / "raw" / "top_100.csv",
        help="Path to write CSV output",
    )
    args = parser.parse_args()

    response = fetch_repositories(args.query, args.first)
    nodes = response["data"]["search"]["nodes"]
    rows = _extract_rows(nodes)

    write_json(response, args.out_json)
    write_csv(rows, args.out_csv)

    print(f"Fetched {len(rows)} repositories.")
    print(f"Raw JSON: {args.out_json}")
    print(f"CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
