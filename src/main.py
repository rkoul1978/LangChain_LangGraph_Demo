"""Command-line entry point: create a JIRA ticket from a JSON file.

Usage:
    python src/main.py sample_ticket.json
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from agent import run_agent_from_json_string


def main(argv: list[str]) -> int:
    load_dotenv()
    if len(argv) != 2:
        print("Usage: python src/main.py <path-to-ticket.json>")
        return 2

    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        print(f"Could not read file '{path}': {exc}")
        return 1

    try:
        result = run_agent_from_json_string(raw)
    except ValueError as exc:
        print(str(exc))
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
