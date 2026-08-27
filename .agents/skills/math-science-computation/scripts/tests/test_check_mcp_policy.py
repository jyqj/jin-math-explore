from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = SKILL_ROOT / "scripts" / "check_mcp_policy.py"
SPEC = importlib.util.spec_from_file_location("check_mcp_policy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckMcpPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.openai_text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    def test_current_candidate_passes(self) -> None:
        self.assertEqual(MODULE.validate(self.skill_text, self.openai_text), [])

    def test_missing_efficiency_stop_rule_is_blocked(self) -> None:
        broken = self.skill_text.replace("Stop as soon as", "Continue after")
        self.assertIn("missing: explicit stop rule", MODULE.validate(broken, self.openai_text))

    def test_missing_mcp_gate_is_still_blocked(self) -> None:
        broken = self.skill_text.replace("## Mandatory Wolfram MCP Gate", "## Wolfram Gate")
        self.assertIn("missing: mandatory gate heading", MODULE.validate(broken, self.openai_text))

    def test_missing_fastest_completion_parallel_gate_is_blocked(self) -> None:
        broken = self.skill_text.replace(
            "attempt an appropriate bounded parallel implementation",
            "run an implementation",
        )
        self.assertIn("missing: bounded parallel attempt", MODULE.validate(broken, self.openai_text))

    def test_missing_fastest_completion_prompt_is_blocked(self) -> None:
        broken = self.openai_text.replace(
            "explicitly requests the fastest possible completion or minimum wall time",
            "requests a computation",
        )
        self.assertIn("missing: fastest-completion prompt", MODULE.validate(self.skill_text, broken))

    def test_missing_call_window_heading_is_blocked(self) -> None:
        broken = self.skill_text.replace(
            "## MCP Call-Window and Long-Run Routing",
            "## Long-Run Routing",
        )
        self.assertIn("missing: call-window heading", MODULE.validate(broken, self.openai_text))

    def test_missing_backend_readiness_heading_is_blocked(self) -> None:
        broken = self.skill_text.replace(
            "## Backend Readiness Gate",
            "## Backend Notes",
        )
        self.assertIn(
            "missing: backend readiness heading",
            MODULE.validate(broken, self.openai_text),
        )

    def test_missing_targeted_invalidation_is_blocked(self) -> None:
        broken = self.skill_text.replace(
            "`backend_inventory.py --mode Invalidate --backend <name> --reason-code <code>`",
            "refresh everything",
        )
        self.assertIn(
            "missing: targeted invalidation",
            MODULE.validate(broken, self.openai_text),
        )

    def test_missing_inventory_prompt_is_blocked(self) -> None:
        broken = self.openai_text.replace(
            "read or create the persistent local backend inventory first",
            "select a backend first",
        )
        self.assertIn(
            "missing: inventory prompt",
            MODULE.validate(self.skill_text, broken),
        )

    def test_missing_probabilistic_filter_boundary_is_blocked(self) -> None:
        broken = self.skill_text.replace(
            "A probabilistic filter may reduce exact-verifier work but cannot support an exact final claim by itself",
            "A probabilistic filter is enough",
        )
        self.assertIn(
            "missing: probabilistic filter boundary",
            MODULE.validate(broken, self.openai_text),
        )

    def test_missing_exclusive_scope_prompt_is_blocked(self) -> None:
        broken = self.openai_text.replace(
            "only for mathematics-related computation tasks; do not route unrelated work to it or perform work outside that scope",
            "for computation tasks",
        )
        self.assertIn(
            "missing: exclusive scope prompt",
            MODULE.validate(self.skill_text, broken),
        )

    def test_enumerated_rendering_task_is_blocked(self) -> None:
        broken = self.skill_text + "\nThis Skill does not do Manim rendering.\n"
        self.assertIn(
            "forbidden: Manim task enumeration",
            MODULE.validate(broken, self.openai_text),
        )

    def test_old_overbroad_interface_prompt_is_blocked(self) -> None:
        broken = self.openai_text.replace(
            'short_description: "Route computations efficiently and verify proportionately"',
            'short_description: "Prefer Wolfram MCP and deliver reproducible computation"',
        )
        self.assertIn("missing: English short description", MODULE.validate(self.skill_text, broken))


if __name__ == "__main__":
    unittest.main()
