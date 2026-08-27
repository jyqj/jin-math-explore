#!/usr/bin/env python3
"""Validate official research-map v1 or recover pre-standardization prototypes."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from v13_common import configure_stdio


def module(name: str):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


_V2 = module("validate_research_map_v2")
CONTROL_PATHS = _V2.CONTROL_PATHS


def validate_map(args):
    """Compatibility surface used by frozen v2 tests and callers."""
    return _V2.validate_map(args)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("map_root", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--allow-stale", action="store_true", help="v2 compatibility only")
    parser.add_argument("--for-v13-attempt", action="store_true")
    parser.add_argument("--for-result-export", action="store_true")
    parser.add_argument("--for-publication", action="store_true")
    parser.add_argument("--previous-map-root", type=Path)
    args = parser.parse_args()
    root = args.map_root.resolve()
    hidden = root / ".research/research-map.json"
    if hidden.is_file():
        try:
            schema = json.loads(hidden.read_text(encoding="utf-8")).get("schema")
        except Exception:
            schema = None
        if schema == "math-research-map/v1":
            result = module("research_map_v1").validate_root(
                root,
                for_attempt=args.for_v13_attempt,
                for_export=args.for_result_export,
                for_publication=args.for_publication,
                previous_map_root=args.previous_map_root.resolve() if args.previous_map_root else None,
            )
        elif schema == "math-research-map/v4":
            if args.for_v13_attempt or args.for_result_export or args.for_publication:
                result = {"ok": False, "schema": "math-research-map-validation/v1", "map_schema": schema, "activation_eligible": False, "issues": [{"code": "prototype_map_activation_forbidden", "path": ".research/research-map.json"}]}
            else:
                result = module("research_map_v4").validate_root(root, for_attempt=False)
        elif schema == "math-research-map/v3":
            if args.for_v13_attempt or args.for_result_export or args.for_publication:
                result = {"ok": False, "schema": "math-research-map-validation/v1", "map_schema": schema, "activation_eligible": False, "issues": [{"code": "prototype_map_activation_forbidden", "path": ".research/research-map.json"}]}
            elif args.project_root is None:
                parser.error("math-research-map/v3 requires --project-root")
            else:
                result = module("research_map_v3").validate_v3(root, args.project_root.resolve())
        else:
            result = {"ok": False, "schema": "math-research-map-validation/v1", "issues": [{"code": "map_schema_unsupported", "path": ".research/research-map.json"}]}
    elif (root / "research-map.json").is_file():
        if args.for_v13_attempt or args.for_result_export or args.for_publication:
            result = {"ok": False, "schema": "math-research-map-validation/v1", "activation_eligible": False, "issues": [{"code": "prototype_map_activation_forbidden", "path": "research-map.json"}]}
        else:
            result = _V2.validate(root, allow_stale=args.allow_stale)
    else:
        result = {"ok": False, "schema": "math-research-map-validation/v1", "issues": [{"code": "map_control_missing"}]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
