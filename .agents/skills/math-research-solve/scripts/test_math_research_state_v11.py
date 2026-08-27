from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import math_research_state_v11 as state


def objective() -> dict:
    return {
        "schema": state.OBJECTIVE_SCHEMA,
        "project_id": "synthetic-project",
        "statement": "Prove target theorem T.",
        "domain": "A declared mathematical domain.",
        "quantifier_order": "For every admissible object there exists a certified witness.",
        "assumptions": ["The source axioms are frozen."],
        "evidence_standard": "Independent proof verification.",
        "completion_standard": "A terminally audited proof of T.",
        "created_at_utc": "2026-01-01T00:00:00Z",
    }


class V11ReadOnlyCompatibilityTests(unittest.TestCase):
    def test_project_neutral_objective_passes(self) -> None:
        self.assertEqual(objective(), state.validate_objective(objective(), "synthetic-project"))

    def test_empty_completion_standard_fails(self) -> None:
        value = objective()
        value["completion_standard"] = ""
        with self.assertRaises(state.ResearchError) as caught:
            state.validate_objective(value, "synthetic-project")
        self.assertEqual("objective_invalid", caught.exception.code)

    def test_non_v11_head_delegates_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "project.json").write_text(
                '{"schema":"math-research-project/v10"}\n',
                encoding="utf-8",
                newline="\n",
            )
            result = state.startup(root)
            self.assertEqual("delegate_startup_v5", result["classification"])
            self.assertEqual("math-research-project/v10", result["schema"])


if __name__ == "__main__":
    unittest.main()
