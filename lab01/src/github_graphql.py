from __future__ import annotations

import json
import os
import time
from typing import Any, Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.github.com/graphql"

def get_github_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GITHUB_TOKEN não está presente."
        )
    return token


def run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    token = get_github_token()
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "lab01-graphql-client",
        },
    )

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request) as response:
                response_body = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else str(exc)
            if exc.code in (502, 503, 504) and attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(f"HTTP error {exc.code}: {error_body}") from exc
        except URLError as exc:
            if attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(f"Network error: {exc.reason}") from exc

    data = json.loads(response_body)
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data
