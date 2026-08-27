#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_repo import validate_computation_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one research/computation bridge mechanically.")
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--root", type=Path, required=True, help="Project root used to resolve artifact paths.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    problems = validate_computation_handoff(args.handoff.resolve(), args.root.resolve())
    payload = {
        "ok": not problems,
        "scope": "byte_path_and_required_field_closure_only",
        "mathematical_truth_verified": False,
        "problems": [item.__dict__ for item in problems],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    elif problems:
        for item in problems:
            print(item.render())
    else:
        print("PASS: computation handoff bytes and paths close; mathematical semantics were not assessed.")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
