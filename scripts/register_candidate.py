#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from research_repo import PROBLEM_CLASSES, PROJECT_ID, SLUG, pretty_json, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Register a pre-genesis hard-problem candidate without claiming open status.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--problem-class", required=True, choices=sorted(PROBLEM_CLASSES))
    parser.add_argument("--dependency", action="append", default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    if not PROJECT_ID.fullmatch(args.project_id):
        parser.error("--project-id must match P- followed by at least four digits")
    if not SLUG.fullmatch(args.slug):
        parser.error("--slug must be lowercase kebab-case")
    if not args.title.strip():
        parser.error("--title must be nonempty")
    output = root / "registry" / "projects" / f"{args.project_id}.json"
    if output.exists():
        parser.error(f"registry entry already exists: {output}")
    entry = {
        "schema": "jin-math-project-registry/v1",
        "project_id": args.project_id,
        "slug": args.slug,
        "title": args.title.strip(),
        "problem_class": args.problem_class,
        "operational_status": "candidate",
        "mathematical_status": "unknown",
        "project_path": None,
        "objective_sha256": None,
        "current_window_id": None,
        "dependencies": args.dependency,
        "source_audit": {"status": "pending", "as_of": None, "receipt": None},
        "last_merged_window": None,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pretty_json(entry))
    problems = validate_registry(root)
    if problems:
        output.unlink(missing_ok=True)
        for item in problems:
            print(item.render())
        return 1
    print(f"CREATED: {output.relative_to(root).as_posix()} (candidate only; source audit required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
