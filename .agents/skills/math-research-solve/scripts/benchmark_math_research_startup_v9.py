#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
import tempfile
import time
from pathlib import Path

from test_math_research_state_v9 import V9Fixture, mr


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        fixture = V9Fixture(Path(temp))
        fixture.create()
        elapsed = []
        for _ in range(10):
            started = time.perf_counter()
            result = mr.startup(fixture.project, "Auto", None)
            elapsed.append(time.perf_counter() - started)
            if result["classification"] != "v9_ready":
                raise RuntimeError("startup classification changed")
        median = statistics.median(elapsed)
        output = {
            "schema": "math-research-startup-benchmark/v1",
            "fixture": "synthetic-v9-current-head",
            "runs": 10,
            "median_seconds": median,
            "p95_seconds": sorted(elapsed)[-1],
            "target_seconds": 4.0,
            "passed": median <= 4.0,
        }
        print(json.dumps(output, sort_keys=True))
        return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

