from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pr_policy import Change, evaluate  # noqa: E402


class PullRequestPolicyTests(unittest.TestCase):
    def root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name)

    def codes(self, title: str, branch: str, changes: list[Change], root: Path | None = None) -> set[str]:
        return {item.code for item in evaluate(root or self.root(), title, branch, changes)}

    def test_infra_cannot_advance_project(self):
        codes = self.codes("[infra] update validator", "infra/update-validator", [Change("M", "projects/P-0001--x/project.json")])
        self.assertIn("authority_scope_violation", codes)
        self.assertIn("infra_authority_violation", codes)

    def test_window_is_one_project_and_objective_immutable(self):
        changes = [
            Change("M", "projects/P-0001--x/project.json"),
            Change("M", "projects/P-0002--y/project.json"),
            Change("M", "projects/P-0001--x/.research/identity/objective-core.json"),
        ]
        codes = self.codes("[P-0001][window] close W-0001", "research/p-0001/w-0001-close", changes)
        self.assertIn("changed_project_count", codes)
        self.assertIn("objective_immutability", codes)

    def test_genesis_requires_create_only_project_and_registry(self):
        changes = [
            Change("A", "projects/P-0001--x/project.json"),
            Change("A", "projects/P-0001--x/.research/identity/objective-core.json"),
            Change("A", "registry/projects/P-0001.json"),
            Change("A", "catalog/index.json"),
        ]
        self.assertEqual(set(), self.codes("[P-0001][genesis] create objective", "genesis/p-0001/objective-v1", changes))
        changes[0] = Change("M", changes[0].path)
        self.assertIn("genesis_not_create_only", self.codes("[P-0001][genesis] create objective", "genesis/p-0001/objective-v1", changes))

    def test_verify_cannot_modify_bound_candidate(self):
        root = self.root()
        project = root / "projects/P-0001--x"
        receipt = project / ".research/verifications/v-1/jin-math-verification.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({"candidate": {"path": ".research/proof.md", "sha256": "0" * 64}}), encoding="utf-8")
        changes = [
            Change("A", receipt.relative_to(root).as_posix()),
            Change("M", "projects/P-0001--x/.research/proof.md"),
        ]
        codes = self.codes("[P-0001][verify] verify C-0001", "verify/p-0001/w-0001/v-01", changes, root)
        self.assertIn("verification_candidate_modified", codes)

    def test_branch_prefix_is_enforced(self):
        codes = self.codes("[P-0001][state] park project", "research/p-0001/park", [Change("M", "registry/projects/P-0001.json")])
        self.assertIn("branch_name_invalid", codes)


if __name__ == "__main__":
    unittest.main()
