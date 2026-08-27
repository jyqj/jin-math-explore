#!/usr/bin/env python3
"""Create a canonical, receipt-bound v13 attempt package in fresh staging."""
from __future__ import annotations

import argparse
from pathlib import Path

from attempt_package_preflight_v13 import finalize_package, pointer
from v13_common import configure_stdio, emit, error_result


def parse_ref(value: str) -> dict[str, str]:
    path, separator, digest = value.rpartition("=")
    if not separator:
        raise ValueError("External references use PROJECT/PATH=LOWERCASE_SHA256")
    return pointer({"path": path, "sha256": digest}, "external reference")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--package-root", required=True, help="Final POSIX-relative project package root")
    parser.add_argument("--candidate-path", help="Candidate path relative to the source package")
    parser.add_argument("--dependency-path", action="append", default=[])
    parser.add_argument("--external-dependency-ref", action="append", default=[])
    parser.add_argument("--external-artifact-ref", action="append", default=[])
    parser.add_argument("--max-total-bytes", type=int, default=300_000)
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args()
    try:
        result = finalize_package(
            args.source, args.staging, attempt_id=args.attempt_id,
            package_root=args.package_root, candidate_path=args.candidate_path,
            dependency_paths=args.dependency_path,
            external_dependencies=[parse_ref(value) for value in args.external_dependency_ref],
            external_artifacts=[parse_ref(value) for value in args.external_artifact_ref],
            max_total_bytes=args.max_total_bytes, project_root=args.project_root,
        )
        return emit(result)
    except Exception as exc:
        value, code = error_result(exc)
        return emit(value, code)


if __name__ == "__main__":
    raise SystemExit(main())
