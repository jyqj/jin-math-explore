#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from research_repo import catalog_payload, frontier_markdown, pretty_json, public_registry_entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Build generated portfolio views from per-project registry entries.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true", help="Fail when committed generated files are stale.")
    args = parser.parse_args()
    root = args.root.resolve()
    entries = public_registry_entries(root)
    outputs = {
        root / "catalog" / "index.json": pretty_json(catalog_payload(entries)),
        root / "catalog" / "frontier.md": frontier_markdown(entries).encode("utf-8"),
    }
    stale = []
    for path, expected in outputs.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                stale.append(path.relative_to(root).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if stale:
        print("STALE: " + ", ".join(stale))
        return 1
    print(("PASS" if args.check else "UPDATED") + f": {len(outputs)} catalog files; projects={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
