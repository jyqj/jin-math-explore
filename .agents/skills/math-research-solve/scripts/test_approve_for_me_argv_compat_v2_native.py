#!/usr/bin/env python3
from __future__ import annotations

import unittest

from MathResearchApproveForMeArgvCompatV2 import (
    assert_approve_for_me_arguments,
    new_features_arguments,
    new_global_arguments,
)


class ArgvCompatibilityTests(unittest.TestCase):
    def test_launcher_success(self) -> None:
        values = new_global_arguments(
            flavor="launcher-v2", run_directory="fixture", model="gpt-test",
            reasoning_effort="high", sandbox="workspace-write", approval_mode="approve_for_me",
            allow_web_search=True, enable_multi_agent=True, max_child_agents=3,
        )
        self.assertTrue(assert_approve_for_me_arguments(values))
        self.assertEqual(1, values.count("--search"))
        self.assertIn("agents.max_threads=3", values)

    def test_never_mode_has_explicit_sandbox(self) -> None:
        values = new_global_arguments(
            flavor="launcher-v2", run_directory="fixture", model="gpt-test",
            reasoning_effort="low", sandbox="read-only", approval_mode="never",
            allow_web_search=False, enable_multi_agent=False,
        )
        self.assertNotIn("--approve-for-me", values)
        self.assertEqual(["-s", "read-only", "-a", "never"], values[5:9])

    def test_features_success(self) -> None:
        values = new_features_arguments(run_directory="fixture", max_child_agents=2, approval_mode="approve_for_me")
        self.assertEqual(["features", "list"], values[-2:])

    def test_blocked_invalid_sandbox(self) -> None:
        with self.assertRaises(ValueError):
            new_global_arguments(
                flavor="legacy-v1-compat", run_directory="fixture", model="gpt-test",
                reasoning_effort="high", sandbox="read-only", allow_web_search=False,
                enable_multi_agent=False,
            )

    def test_blocked_tampered_arguments(self) -> None:
        with self.assertRaises(ValueError):
            assert_approve_for_me_arguments(["--approve-for-me", "-s", "workspace-write"])


if __name__ == "__main__":
    unittest.main()
