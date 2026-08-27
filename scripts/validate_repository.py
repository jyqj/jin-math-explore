#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_repo import validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mechanical jin-math-explore repository contracts.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    problems = validate_repository(args.root)
    payload = {
        "ok": not problems,
        "scope": "mechanical_repository_contracts_only",
        "mathematical_truth_verified": False,
        "problems": [item.__dict__ for item in problems],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    elif problems:
        for item in problems:
            print(item.render())
    else:
        print("PASS: mechanical repository contracts are valid; mathematical truth was not assessed.")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
