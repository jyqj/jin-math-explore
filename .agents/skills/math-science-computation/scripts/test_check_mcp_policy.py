from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check_mcp_policy.py")
SPEC = importlib.util.spec_from_file_location("check_mcp_policy", MODULE_PATH)
assert SPEC and SPEC.loader
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


class CheckMcpPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
        self.openai_text = (root / "agents" / "openai.yaml").read_text(encoding="utf-8")

    def test_installed_candidate_passes(self) -> None:
        self.assertEqual(POLICY.validate(self.skill_text, self.openai_text), [])

    def test_missing_completion_gate_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "The model has no discretion to omit it",
            "The model may choose whether to omit it",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: mandatory execution", errors)

    def test_missing_user_termination_authority_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "The user retains the right to terminate it",
            "Termination is automatic",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: user termination authority", errors)

    def test_missing_parallel_serial_fallback_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "return to the best serial implementation",
            "continue without a fallback",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: serial fallback", errors)

    def test_missing_long_run_local_route_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "use an actually callable local executable or monitorable process for the full run",
            "keep using the same evaluator call",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: durable local route", errors)

    def test_missing_backend_readiness_gate_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "## Backend Readiness Gate",
            "## Backend Notes",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: backend readiness heading", errors)

    def test_cache_hit_backend_start_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "On a cache hit, do not start Mathematica, SageMath, Python, primecount, or any MCP tool",
            "On a cache hit, start every backend",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: cache-hit no-start rule", errors)

    def test_persisted_mcp_authority_is_blocked(self) -> None:
        altered = self.openai_text.replace(
            "Treat persisted MCP information as historical only",
            "Treat persisted MCP information as live",
            1,
        )
        errors = POLICY.validate(self.skill_text, altered)
        self.assertIn("missing: session MCP authority prompt", errors)

    def test_missing_timeout_inspection_prompt_is_blocked(self) -> None:
        altered = self.openai_text.replace(
            "inspect whether work is still running before retrying after a timeout",
            "retry after a timeout",
            1,
        )
        errors = POLICY.validate(self.skill_text, altered)
        self.assertIn("missing: timeout inspection prompt", errors)

    def test_missing_exclusive_scope_is_blocked(self) -> None:
        altered = self.skill_text.replace(
            "This Skill handles only mathematics-related computation tasks.",
            "This Skill handles tasks.",
            1,
        )
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("missing: exclusive computation scope", errors)

    def test_enumerated_unrelated_tasks_are_blocked(self) -> None:
        altered = self.skill_text + "\nThis Skill does not handle Vault writes.\n"
        errors = POLICY.validate(altered, self.openai_text)
        self.assertIn("forbidden: Vault task enumeration", errors)


if __name__ == "__main__":
    unittest.main()
