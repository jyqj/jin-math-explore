#!/usr/bin/env python3
"""Tests for the backend routing policy validator."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = SKILL_ROOT / "scripts" / "check_backend_routing.py"
SPEC = importlib.util.spec_from_file_location("check_backend_routing", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


CATALOG = """# Backend routing

| route_id | task_class | conditions | primary | fallback | decision_metrics | evidence_status | evidence_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| example | Example task | Exact result required | Tool A | Tool B | correctness, wall time | heuristic | none |
"""


class BackendRoutingValidationTests(unittest.TestCase):
    def test_accepts_complete_heuristic_route(self) -> None:
        self.assertEqual(MODULE.validate(CATALOG, "# Evidence\n"), [])

    def test_rejects_benchmarked_route_without_registered_evidence(self) -> None:
        invalid = CATALOG.replace("heuristic | none", "benchmarked | EV-001")
        self.assertEqual(
            MODULE.validate(invalid, "# Evidence\n"),
            ["example: unknown evidence_id EV-001"],
        )

    def test_accepts_benchmarked_route_with_registered_evidence(self) -> None:
        promoted = CATALOG.replace("heuristic | none", "benchmarked | EV-001")
        ledger = "# Evidence\n\n- `evidence_id`: `EV-001`\n"
        self.assertEqual(MODULE.validate(promoted, ledger), [])


if __name__ == "__main__":
    unittest.main()
