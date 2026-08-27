#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from research_repo import load_json, validate_skill_dependencies, validate_vendored_skills


def candidates(root: Path, name: str) -> list[Path]:
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    explicit = os.environ.get("JIN_MATH_SKILLS_ROOT")
    values = [root / ".agents" / "skills" / name, codex_home / "skills" / name, home / ".agents" / "skills" / name]
    if explicit:
        values.insert(0, Path(explicit).expanduser() / name)
    seen: set[Path] = set()
    return [item for item in values if not (item in seen or seen.add(item))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Report required external Skill availability without installing anything.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--strict", action="store_true", help="Fail when a dependency is not installed.")
    args = parser.parse_args()
    root = args.root.resolve()
    contract_problems = validate_skill_dependencies(root) + validate_vendored_skills(root)
    if contract_problems:
        for item in contract_problems:
            print(item.render())
        return 1
    manifest = load_json(root / "skill-dependencies.json")
    rows = []
    missing = False
    for item in manifest["dependencies"]:
        found = next((path for path in candidates(root, item["name"]) if (path / "SKILL.md").is_file()), None)
        is_vendored = found == root / ".agents" / "skills" / item["name"]
        status = "available_verified_file_inventory" if is_vendored else "available_unverified_tree_hash" if found else "missing"
        missing |= found is None
        rows.append({"name": item["name"], "required_version": item["version"], "status": status, "path": str(found) if found else None})
    print(json.dumps({"ok": not (args.strict and missing), "strict": args.strict, "dependencies": rows}, ensure_ascii=False, separators=(",", ":")))
    return 1 if args.strict and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
