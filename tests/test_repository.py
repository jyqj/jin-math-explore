from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from research_repo import (  # noqa: E402
    catalog_payload,
    canonical_json,
    frontier_markdown,
    pretty_json,
    sha256_bytes,
    validate_computation_handoff,
    validate_registry,
    validate_verification,
    validate_vendored_skills,
)


class RepositoryContractTests(unittest.TestCase):
    def root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "registry/projects").mkdir(parents=True)
        (root / "registry/shared-results").mkdir(parents=True)
        (root / "projects").mkdir()
        return root

    def objective(self) -> dict:
        return {
            "statement": "Prove the synthetic statement.",
            "domain": "Synthetic objects",
            "quantifier_order": "For every object there exists a witness.",
            "assumptions": ["Synthetic fixture only"],
            "evidence_standard": "Independent proof verification",
            "completion_standard": "All quantifiers covered",
        }

    def entry(self, objective_sha: str) -> dict:
        return {
            "schema": "jin-math-project-registry/v1",
            "project_id": "P-0001",
            "slug": "synthetic-hard-problem",
            "title": "Synthetic hard problem",
            "problem_class": "internal_frontier",
            "operational_status": "active",
            "mathematical_status": "open",
            "project_path": "projects/P-0001--synthetic-hard-problem",
            "objective_sha256": objective_sha,
            "current_window_id": None,
            "dependencies": [],
            "source_audit": {"status": "pass", "as_of": "2026-08-28", "receipt": "projects/P-0001--synthetic-hard-problem/.research/source-audit.md"},
            "last_merged_window": None,
        }

    def make_project(self, root: Path) -> tuple[Path, dict]:
        project = root / "projects/P-0001--synthetic-hard-problem"
        (project / ".research/identity").mkdir(parents=True)
        (project / ".research/heads").mkdir(parents=True)
        (project / "研究地图").mkdir()
        (project / "README.md").write_text("# Synthetic\n", encoding="utf-8")
        objective_raw = canonical_json(self.objective())
        (project / ".research/identity/objective-core.json").write_bytes(objective_raw)
        research_path = project / ".research/heads/research.json"
        execution_path = project / ".research/heads/execution.json"
        research_path.write_bytes(canonical_json({"schema": "math-research-authority-head/v13", "generation": 1}))
        execution_path.write_bytes(canonical_json({"schema": "math-research-execution-head/v13", "generation": 1, "phase": "window_idle"}))
        def pointer(path: Path) -> dict:
            return {"path": path.relative_to(project).as_posix(), "sha256": sha256_bytes(path.read_bytes())}
        project_head = {
            "schema": "math-research-project/v13",
            "project_id": "P-0001",
            "created_at_utc": "2026-08-28T00:00:00Z",
            "objective": pointer(project / ".research/identity/objective-core.json"),
            "objective_commitment_sha256": sha256_bytes(objective_raw),
            "research_authority_head": pointer(research_path),
            "execution_state_head": pointer(execution_path),
            "generation": 1,
            "project_complete": False,
            "pending_goal_update": False,
        }
        (project / "project.json").write_bytes(canonical_json(project_head))
        (project / ".research/source-audit.md").write_text("Synthetic source audit receipt.\n", encoding="utf-8")
        entry = self.entry(sha256_bytes(objective_raw))
        (root / "registry/projects/P-0001.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return project, entry

    def test_valid_active_project(self):
        root = self.root()
        self.make_project(root)
        self.assertEqual([], validate_registry(root))

    def test_valid_candidate_has_no_project_authority(self):
        root = self.root()
        entry = {
            "schema": "jin-math-project-registry/v1",
            "project_id": "P-0001",
            "slug": "candidate-only",
            "title": "Candidate only",
            "problem_class": "likely_open_needs_audit",
            "operational_status": "candidate",
            "mathematical_status": "unknown",
            "project_path": None,
            "objective_sha256": None,
            "current_window_id": None,
            "dependencies": [],
            "source_audit": {"status": "pending", "as_of": None, "receipt": None},
            "last_merged_window": None,
        }
        (root / "registry/projects/P-0001.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertEqual([], validate_registry(root))

    def test_objective_hash_mismatch_is_rejected(self):
        root = self.root()
        self.make_project(root)
        path = root / "registry/projects/P-0001.json"
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["objective_sha256"] = "0" * 64
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertIn("objective_hash_mismatch", {item.code for item in validate_registry(root)})

    def test_component_head_tamper_is_rejected(self):
        root = self.root()
        project, _ = self.make_project(root)
        (project / ".research/heads/execution.json").write_text('{"schema":"tampered","generation":1}\n', encoding="utf-8")
        codes = {item.code for item in validate_registry(root)}
        self.assertIn("artifact_hash_mismatch", codes)

    def test_candidate_cannot_bind_project_state(self):
        root = self.root()
        _, entry = self.make_project(root)
        entry["operational_status"] = "candidate"
        path = root / "registry/projects/P-0001.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertIn("preproject_state_invalid", {item.code for item in validate_registry(root)})

    def test_unknown_dependency_is_rejected(self):
        root = self.root()
        _, entry = self.make_project(root)
        entry["dependencies"] = ["P-9999"]
        path = root / "registry/projects/P-0001.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertIn("dependency_missing", {item.code for item in validate_registry(root)})

    def test_catalog_is_deterministic(self):
        root = self.root()
        _, entry = self.make_project(root)
        payload = catalog_payload([entry])
        self.assertEqual(1, payload["counts"]["projects"])
        self.assertEqual(1, payload["counts"]["active"])
        markdown = frontier_markdown([entry])
        self.assertIn("P-0001", markdown)
        self.assertIn("Synthetic hard problem", markdown)

    def test_computation_handoff_detects_artifact_tamper(self):
        root = self.root()
        project, _ = self.make_project(root)
        code = project / ".research/code.py"
        result = project / ".research/result.json"
        record = project / ".research/computation-record.json"
        code.write_text("print(2 + 2)\n", encoding="utf-8")
        result.write_text('{"value":4}\n', encoding="utf-8")
        record.write_text('{"schema":"synthetic"}\n', encoding="utf-8")
        def pointer(path: Path) -> dict:
            rel = path.relative_to(project).as_posix()
            return {"path": rel, "sha256": sha256_bytes(path.read_bytes())}
        handoff = {
            "schema": "jin-math-computation-handoff/v1",
            "problem_id": "P-0001",
            "window_id": "W-0001",
            "attempt_id": "A-0001",
            "claim_id": "C-0001",
            "objective_sha256": sha256_bytes((project / ".research/identity/objective-core.json").read_bytes()),
            "question": "Compute the synthetic value exactly.",
            "domain": "Integers",
            "assumptions": [],
            "requested_evidence": "exact_check",
            "backend": {"name": "Python", "version": "3.12", "interface": "local", "inventory_snapshot_sha256": None},
            "exact_input": {"expression": "2+2"},
            "reproduction_command": "python .research/code.py",
            "code_artifacts": [pointer(code)],
            "result_artifacts": [pointer(result)],
            "computation_record": pointer(record),
            "evidence_grade": "exact_check",
            "cannot_imply": ["Does not establish an unbounded theorem."],
        }
        path = project / ".research/computation-handoff.json"
        path.write_bytes(canonical_json(handoff))
        self.assertEqual([], validate_computation_handoff(path, project))
        result.write_text('{"value":5}\n', encoding="utf-8")
        self.assertIn("artifact_hash_mismatch", {item.code for item in validate_computation_handoff(path, project)})

    def test_verification_receipt_binds_candidate(self):
        root = self.root()
        project, _ = self.make_project(root)
        candidate = project / ".research/proof.md"
        dependency = project / ".research/lemma.md"
        candidate.write_text("Candidate proof.\n", encoding="utf-8")
        dependency.write_text("Verified lemma.\n", encoding="utf-8")
        def pointer(path: Path) -> dict:
            return {"path": path.relative_to(project).as_posix(), "sha256": sha256_bytes(path.read_bytes())}
        receipt = {
            "schema": "jin-math-verification/v1",
            "verification_id": "V-0001",
            "problem_id": "P-0001",
            "claim_id": "C-0001",
            "candidate": pointer(candidate),
            "dependencies": [pointer(dependency)],
            "reviewer_principal": "fresh-reviewer-1",
            "context_isolated": True,
            "verdict": "PASS",
            "checked_scope": "Synthetic statement under the recorded assumption.",
            "earliest_error": None,
            "unresolved": [],
            "cannot_imply": ["Does not establish any unstated generalization."],
        }
        path = project / ".research/jin-math-verification.json"
        path.write_bytes(canonical_json(receipt))
        self.assertEqual([], validate_verification(path, project))
        candidate.write_text("Changed proof.\n", encoding="utf-8")
        self.assertIn("artifact_hash_mismatch", {item.code for item in validate_verification(path, project)})

    def test_vendored_skill_lock_detects_tamper(self):
        root = self.root()
        dependencies = []
        packages = []
        for name, tree_hash in (
            ("math-research-solve", "1" * 64),
            ("math-science-computation", "2" * 64),
        ):
            skill = root / ".agents/skills" / name
            skill.mkdir(parents=True)
            payload = f"---\nname: {name}\ndescription: Synthetic.\n---\n".encode()
            (skill / "SKILL.md").write_bytes(payload)
            dependencies.append({"name": name, "version": "1.11", "package_tree_sha256": tree_hash, "required_for": ["test"]})
            packages.append({
                "name": name,
                "version": "1.11",
                "package_tree_sha256": tree_hash,
                "source_artifact": "synthetic",
                "file_count": 1,
                "files": [{"path": "SKILL.md", "sha256": sha256_bytes(payload), "executable": False}],
            })
        (root / "skill-dependencies.json").write_bytes(pretty_json({"schema": "jin-math-skill-dependencies/v1", "dependencies": dependencies}))
        (root / "vendored-skills.lock.json").write_bytes(pretty_json({"schema": "jin-math-vendored-skills-lock/v1", "packages": packages}))
        self.assertEqual([], validate_vendored_skills(root))
        (root / ".agents/skills/math-research-solve/SKILL.md").write_text("tampered\n", encoding="utf-8")
        self.assertIn("vendored_file_hash_mismatch", {item.code for item in validate_vendored_skills(root)})


if __name__ == "__main__":
    unittest.main()
