#!/usr/bin/env python3
"""Stage and atomically repair a v12 root only when every extra byte is archived."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_ENTRIES = {"README.md", "当前状态.md", "已验证结论.md", "障碍与失败.md", "下一步路线.md", "project.json", ".research"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def inspect(project: Path, imported: Path) -> dict:
    head = json.loads((project / "project.json").read_text(encoding="utf-8"))
    tree = json.loads(imported.read_text(encoding="utf-8"))
    entries = {item["path"]: item for item in tree["entries"]}
    extras = sorted({p.name for p in project.iterdir()} - ROOT_ENTRIES, key=str.casefold)
    rows = []
    for name in extras:
        top = project / name
        files = [top] if top.is_file() else sorted((p for p in top.rglob("*") if p.is_file()), key=lambda p: str(p).casefold())
        for file in files:
            if file.is_symlink():
                raise RuntimeError(f"symlink forbidden: {file}")
            rel = file.relative_to(project).as_posix()
            item = entries.get(rel)
            digest = sha(file)
            if item is None or item.get("sha256") != digest or item.get("size") != file.stat().st_size:
                raise RuntimeError(f"uncovered or changed extra file: {rel}")
            obj = project / ".research/objects/sha256" / digest[:2] / digest
            if not obj.is_file() or obj.stat().st_size != file.stat().st_size or sha(obj) != digest:
                raise RuntimeError(f"missing archive object: {rel}")
            rows.append({"path": rel, "sha256": digest, "size": file.stat().st_size})
    core = {"schema": "math-research-root-repair-plan/v1", "project_id": head["project_id"],
            "project_json_sha256": sha(project / "project.json"), "imported_tree_sha256": sha(imported),
            "extra_entries": extras, "extra_files": rows}
    return {**core, "plan_sha256": hashlib.sha256(canonical(core)).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--imported-tree", type=Path, required=True)
    parser.add_argument("--recovery-root", type=Path, required=True)
    parser.add_argument("--startup-script", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    plan = inspect(project, args.imported_tree.resolve())
    transaction = args.recovery_root.resolve() / plan["project_id"] / plan["plan_sha256"]
    if not args.write:
        print(json.dumps({"ok": True, "write": False, "plan": plan, "transaction_root": str(transaction)}, ensure_ascii=False, indent=2))
        return 0
    transaction.mkdir(parents=True, exist_ok=False)
    stage = transaction / "stage"
    old_root = transaction / "old-root"
    write_json = lambda path, value: path.write_bytes(canonical(value))
    stage.mkdir()
    write_json(transaction / "journal.json", {"status": "preparing", "plan": plan})
    for name in sorted(ROOT_ENTRIES, key=str.casefold):
        source = project / name
        target = stage / name
        shutil.copytree(source, target, copy_function=shutil.copy2) if source.is_dir() else shutil.copy2(source, target)
    check = subprocess.run([sys.executable, "-B", str(args.startup_script), "startup", "--project", str(stage), "--full"], capture_output=True, text=True, encoding="utf-8")
    if check.returncode:
        write_json(transaction / "journal.json", {"status": "validation_failed", "plan": plan, "stderr": check.stderr[-2000:]})
        raise RuntimeError("staged Full Startup failed")
    if inspect(project, args.imported_tree.resolve())["plan_sha256"] != plan["plan_sha256"]:
        raise RuntimeError("source changed after preparation")
    os.replace(project, old_root)
    try:
        os.replace(stage, project)
    except Exception:
        os.replace(old_root, project)
        raise
    write_json(transaction / "journal.json", {"status": "committed", "plan": plan, "old_root": str(old_root)})
    print(json.dumps({"ok": True, "write": True, "old_root": str(old_root)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
