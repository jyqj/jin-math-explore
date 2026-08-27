"""Native cross-platform equivalent of invoke_math_research_v13.ps1."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


TOOLS = {
    "startup": "math_research_state_v13.py",
    "state": "math_research_state_v13.py",
    "commit": "math_research_commit_v13.py",
    "migrate": "math_research_migrate_v12_to_v13.py",
    "map-review": "map_semantic_review_v1.py",
}


def parse(arguments: list[str]) -> tuple[str, list[str]] | None:
    values = list(arguments)
    if values[:1] in (["--tool"], ["-Tool"]):
        if len(values) < 2:
            return None
        tool, rest = values[1], values[2:]
    elif values:
        tool, rest = values[0], values[1:]
    else:
        return None
    if rest[:1] == ["--"]:
        rest = rest[1:]
    if tool not in TOOLS:
        return None
    return tool, rest


def main() -> int:
    parsed = parse(sys.argv[1:])
    if parsed is None:
        print("Tool must be one of: " + ", ".join(TOOLS), file=sys.stderr)
        return 1
    tool, rest = parsed
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    script = Path(__file__).resolve().with_name(TOOLS[tool])
    completed = subprocess.run([sys.executable, "-B", str(script), *rest], env=environment, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
