from __future__ import annotations

import json
import sys
import time
from typing import Dict

from github_graphql import run_query

QUERY = """
query {
  viewer { login }
  rateLimit { remaining resetAt }
}
"""


def _print_payload(payload: Dict[str, object]) -> None:
	print(json.dumps(payload, indent=2))


def main() -> int:
	retries = 3
	for attempt in range(1, retries + 1):
		try:
			response = run_query(QUERY, {})
			_print_payload(response)
			return 0
		except RuntimeError as exc:
			message = str(exc)
			print(f"Attempt {attempt}/{retries} failed: {message}")
			if "HTTP error 502" in message and attempt < retries:
				time.sleep(2 * attempt)
				continue
			return 1
	return 1


if __name__ == "__main__":
	sys.exit(main())
