from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from coordination_policy import evaluate  # noqa: E402


BASE = "a" * 40
NOW = datetime(2026, 8, 28, 20, 0, tzinfo=timezone.utc)


def body(
    *,
    write_set: list[str] | None = None,
    read_set: list[str] | None = None,
    mode: str = "exclusive_write",
    role: str = "protocol_maintainer",
    base_sha: str = BASE,
    expires_at: str = "2026-08-29T00:00:00Z",
    independence: dict[str, object] | None = None,
) -> str:
    manifest = {
        "protocol": "jin-math-agent-coordination/v1",
        "issue": 15,
        "actor": {
            "kind": "agent",
            "id": "openai-chatgpt",
            "run_id": "run-20260828-governance",
            "role": role,
        },
        "lease": {
            "id": "L-0015-governance",
            "mode": mode,
            "base_sha": base_sha,
            "expires_at": expires_at,
            "read_set": read_set or [],
            "write_set": write_set or ["GOVERNANCE.md"],
        },
        "independence": independence
        or {
            "required": False,
            "solver_context_access": False,
            "candidate_frozen": False,
        },
        "handoff": {"status": "complete", "summary": "All declared deliverables are present."},
    }
    return f"<!-- jin-math-coordination:v1\n{json.dumps(manifest)}\n-->"


class CoordinationPolicyTests(unittest.TestCase):
    def codes(self, pr_body: str, title: str, changes: list[str], base_sha: str = BASE) -> set[str]:
        return {item.code for item in evaluate(pr_body, title, base_sha, changes, now=NOW)}

    def test_valid_manifest_covers_diff(self):
        self.assertEqual(set(), self.codes(body(), "[infra] governance", ["GOVERNANCE.md"]))

    def test_manifest_is_required_and_unique(self):
        self.assertIn("coordination_manifest_missing", self.codes("", "[infra] governance", ["GOVERNANCE.md"]))
        duplicate = body() + "\n" + body()
        self.assertIn("coordination_manifest_count", self.codes(duplicate, "[infra] governance", ["GOVERNANCE.md"]))

    def test_diff_must_be_within_precise_write_set(self):
        codes = self.codes(body(write_set=["GOVERNANCE.md", "unused.md"]), "[infra] governance", ["GOVERNANCE.md", "README.md"])
        self.assertIn("coordination_write_scope_violation", codes)
        self.assertIn("coordination_write_scope_unused", codes)

    def test_scope_rejects_traversal_and_globs(self):
        codes = self.codes(body(write_set=["../GOVERNANCE.md", "program/*.md"]), "[infra] governance", ["GOVERNANCE.md"])
        self.assertIn("coordination_write_set_path", codes)

    def test_base_sha_must_match_event(self):
        self.assertIn("coordination_base_stale", self.codes(body(base_sha="b" * 40), "[infra] governance", ["GOVERNANCE.md"]))

    def test_expired_lease_is_rejected(self):
        self.assertIn("coordination_lease_expired", self.codes(body(expires_at="2026-08-28T19:59:59Z"), "[infra] governance", ["GOVERNANCE.md"]))

    def test_global_paths_require_exclusive_write(self):
        self.assertIn(
            "coordination_global_requires_exclusive",
            self.codes(body(mode="partitioned_write"), "[infra] governance", ["GOVERNANCE.md"]),
        )

    def test_verifier_requires_run_level_independence(self):
        changes = ["projects/P-0001--x/.research/verifications/v-1/jin-math-verification.json"]
        manifest = body(
            write_set=changes,
            mode="partitioned_write",
            role="solver",
            independence={
                "required": False,
                "solver_context_access": True,
                "candidate_frozen": False,
            },
        )
        codes = self.codes(manifest, "[P-0001][verify] verify C-0001", changes)
        self.assertTrue(
            {
                "coordination_verifier_role",
                "coordination_verifier_independence",
                "coordination_verifier_context",
                "coordination_verifier_candidate",
            }.issubset(codes)
        )

    def test_valid_verifier_manifest(self):
        changes = ["projects/P-0001--x/.research/verifications/v-1/jin-math-verification.json"]
        manifest = body(
            write_set=changes,
            mode="partitioned_write",
            role="independent_verifier",
            independence={
                "required": True,
                "solver_context_access": False,
                "candidate_frozen": True,
            },
        )
        self.assertEqual(set(), self.codes(manifest, "[P-0001][verify] verify C-0001", changes))


if __name__ == "__main__":
    unittest.main()
