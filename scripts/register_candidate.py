#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from portfolio_contracts import (
    CLASSIFICATION_STATUSES,
    GOAL_TYPES,
    MSC_CODE,
    PORTFOLIO_ROLES,
    PROBLEM_ORIGINS,
    PROJECT_ID,
    SLUG,
    TAG,
    default_classification,
    default_dependencies,
    default_result_feedback,
    pretty_json,
    validate_registry,
    validate_taxonomy,
)


def _msc(value: str) -> str:
    if value == "unclassified" or MSC_CODE.fullmatch(value):
        return value
    raise argparse.ArgumentTypeError("MSC code must be unclassified or syntactically match MSC2020, e.g. 11, 11A, 11A05, 11Axx, or 11-XX")


def _tag(value: str) -> str:
    if TAG.fullmatch(value):
        return value
    raise argparse.ArgumentTypeError("tags must be lowercase kebab-case")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register a pre-genesis hard-problem candidate with faceted classification without claiming open status."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--origin",
        "--problem-class",
        "--problem_class",
        dest="origin",
        required=True,
        choices=PROBLEM_ORIGINS,
        help="Research origin; retained aliases keep the foundation-v0 command compatible.",
    )
    parser.add_argument("--primary-msc", type=_msc, default="unclassified")
    parser.add_argument("--secondary-msc", action="append", type=_msc, default=[])
    parser.add_argument("--goal-type", action="append", choices=GOAL_TYPES, default=[])
    parser.add_argument("--object-tag", action="append", type=_tag, default=[])
    parser.add_argument("--method-tag", action="append", type=_tag, default=[])
    parser.add_argument("--portfolio-role", choices=PORTFOLIO_ROLES, default="frontier_problem")
    parser.add_argument("--classification-status", choices=CLASSIFICATION_STATUSES, default="provisional")
    parser.add_argument("--dependency", action="append", default=[], help="Project dependency P-XXXX")
    parser.add_argument("--knowledge-dependency", action="append", default=[], help="Knowledge dependency K-XXXX")
    parser.add_argument("--shared-result-dependency", action="append", default=[], help="Verified shared result S-XXXX")
    args = parser.parse_args()

    root = args.root.resolve()
    if not PROJECT_ID.fullmatch(args.project_id):
        parser.error("--project-id must match P- followed by at least four digits")
    if not SLUG.fullmatch(args.slug):
        parser.error("--slug must be lowercase kebab-case")
    if not args.title.strip():
        parser.error("--title must be nonempty")
    if "unclassified" in args.secondary_msc:
        parser.error("--secondary-msc cannot be unclassified")

    output = root / "registry" / "projects" / f"{args.project_id}.json"
    if output.exists():
        parser.error(f"registry entry already exists: {output}")

    goals = args.goal_type or ["other"]
    entry = {
        "schema": "jin-math-project-registry/v2",
        "project_id": args.project_id,
        "slug": args.slug,
        "title": args.title.strip(),
        "classification": default_classification(
            origin=args.origin,
            primary_msc=args.primary_msc,
            secondary_msc=args.secondary_msc,
            goal_types=goals,
            object_tags=args.object_tag,
            method_tags=args.method_tag,
            portfolio_role=args.portfolio_role,
            status=args.classification_status,
        ),
        "operational_status": "candidate",
        "mathematical_status": "unknown",
        "project_path": None,
        "objective_sha256": None,
        "current_window_id": None,
        "dependencies": default_dependencies(
            projects=args.dependency,
            knowledge=args.knowledge_dependency,
            shared_results=args.shared_result_dependency,
        ),
        "source_audit": {"status": "pending", "as_of": None, "receipt": None},
        "last_merged_window": None,
        "result_feedback": default_result_feedback(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pretty_json(entry))
    problems = [*validate_taxonomy(root), *validate_registry(root)]
    if problems:
        output.unlink(missing_ok=True)
        for item in problems:
            print(item.render())
        return 1
    print(
        f"CREATED: {output.relative_to(root).as_posix()} "
        "(candidate only; source audit and reviewed classification are required before Project genesis)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
