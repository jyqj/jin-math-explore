#!/usr/bin/env python3
"""Independently rehash a frozen v13 attempt package."""
from __future__ import annotations

import argparse
from pathlib import Path

from attempt_package_preflight_v13 import validate_package_directory
from v13_common import configure_stdio, emit, error_result


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    try:
        return emit(validate_package_directory(args.package, project_root=args.project_root))
    except Exception as exc:
        value, code = error_result(exc)
        return emit(value, code)


if __name__ == "__main__":
    raise SystemExit(main())
