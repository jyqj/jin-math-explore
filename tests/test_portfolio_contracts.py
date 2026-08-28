from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from portfolio_contracts import (  # noqa: E402
    catalog_payload,
    canonical_json,
    default_classification,
    default_dependencies,
    default_result_feedback,
    frontier_markdown,
    pretty_json,
    sha256_bytes,
    validate_knowledge_nodes,
    validate_registry,
    validate_taxonomy,
)


class PortfolioContractTests(unittest.TestCase):
    def root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "registry/projects").mkdir(parents=True)
        (root / "registry/shared-results").mkdir(parents=True)
        (root / "knowledge/nodes").mkdir(parents=True)
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

    def classification(self, *, reviewed: bool = True) -> dict:
        return default_classification(
            origin="internal_frontier",
            primary_msc="11A05" if reviewed else "unclassified",
            secondary_msc=["05Cxx"] if reviewed else [],
            goal_types=["existence"] if reviewed else ["other"],
            object_tags=["synthetic-object"] if reviewed else [],
            method_tags=["synthetic-method"] if reviewed else [],
            portfolio_role="frontier_problem",
            status="reviewed" if reviewed else "provisional",
        )

    def candidate_entry(self, project_id: str = "P-0001") -> dict:
        return {
            "schema": "jin-math-project-registry/v2",
            "project_id": project_id,
            "slug": f"candidate-{project_id.lower()}",
            "title": f"Candidate {project_id}",
            "classification": self.classification(reviewed=False),
            "operational_status": "candidate",
            "mathematical_status": "unknown",
            "project_path": None,
            "objective_sha256": None,
            "current_window_id": None,
            "dependencies": default_dependencies(),
            "source_audit": {"status": "pending", "as_of": None, "receipt": None},
            "last_merged_window": None,
            "result_feedback": default_result_feedback(),
        }

    def make_project(self, root: Path) -> tuple[Path, dict]:
        project = root / "projects/P-0001--synthetic-hard-problem"
        (project / ".research/identity").mkdir(parents=True)
        (project / ".research/heads").mkdir(parents=True)
        (project / "研究地图").mkdir()
        (project / "README.md").write_text("# Synthetic\n", encoding="utf-8")
        objective_raw = canonical_json(self.objective())
        objective_path = project / ".research/identity/objective-core.json"
        objective_path.write_bytes(objective_raw)
        research_path = project / ".research/heads/research.json"
        execution_path = project / ".research/heads/execution.json"
        research_path.write_bytes(canonical_json({"schema": "math-research-authority-head/v13", "generation": 1}))
        execution_path.write_bytes(
            canonical_json({"schema": "math-research-execution-head/v13", "generation": 1, "phase": "window_idle"})
        )

        def pointer(path: Path) -> dict:
            return {"path": path.relative_to(project).as_posix(), "sha256": sha256_bytes(path.read_bytes())}

        (project / "project.json").write_bytes(
            canonical_json(
                {
                    "schema": "math-research-project/v13",
                    "project_id": "P-0001",
                    "created_at_utc": "2026-08-28T00:00:00Z",
                    "objective": pointer(objective_path),
                    "objective_commitment_sha256": sha256_bytes(objective_raw),
                    "research_authority_head": pointer(research_path),
                    "execution_state_head": pointer(execution_path),
                    "generation": 1,
                    "project_complete": False,
                    "pending_goal_update": False,
                }
            )
        )
        source_receipt = project / ".research/source-audit.md"
        source_receipt.write_text("Synthetic source-audit receipt.\n", encoding="utf-8")
        entry = {
            "schema": "jin-math-project-registry/v2",
            "project_id": "P-0001",
            "slug": "synthetic-hard-problem",
            "title": "Synthetic hard problem",
            "classification": self.classification(),
            "operational_status": "active",
            "mathematical_status": "open",
            "project_path": "projects/P-0001--synthetic-hard-problem",
            "objective_sha256": sha256_bytes(objective_raw),
            "current_window_id": None,
            "dependencies": default_dependencies(),
            "source_audit": {
                "status": "pass",
                "as_of": "2026-08-28",
                "receipt": source_receipt.relative_to(root).as_posix(),
            },
            "last_merged_window": None,
            "result_feedback": default_result_feedback(),
        }
        (root / "registry/projects/P-0001.json").write_bytes(pretty_json(entry))
        return project, entry

    def knowledge_node(
        self,
        knowledge_id: str,
        *,
        prerequisites: list[str] | None = None,
        relations: list[dict[str, str]] | None = None,
    ) -> dict:
        return {
            "schema": "jin-math-knowledge-node/v1",
            "knowledge_id": knowledge_id,
            "kind": "definition",
            "title": f"Synthetic knowledge {knowledge_id}",
            "classification": {
                "subject": {"scheme": "MSC2020", "primary": "11A05", "secondary": []},
                "object_tags": ["synthetic-object"],
                "method_tags": [],
            },
            "statement": "A synthetic definition used only by the test fixture.",
            "assumptions": [],
            "scope": "Synthetic tests.",
            "conventions": [],
            "prerequisites": prerequisites or [],
            "relations": relations or [],
            "authority": {"status": "reference_only", "receipt": None, "shared_result": None},
            "source_refs": ["tests/test_portfolio_contracts.py"],
            "cannot_imply": ["Does not establish a mathematical theorem."],
        }

    def write_entry(self, root: Path, entry: dict) -> None:
        (root / f"registry/projects/{entry['project_id']}.json").write_bytes(pretty_json(entry))

    def write_knowledge(self, root: Path, node: dict) -> None:
        (root / f"knowledge/nodes/{node['knowledge_id']}.json").write_bytes(pretty_json(node))

    def test_committed_taxonomy_matches_closed_vocabulary(self):
        self.assertEqual([], validate_taxonomy(REPOSITORY_ROOT))

    def test_candidate_can_be_provisionally_unclassified(self):
        root = self.root()
        self.write_entry(root, self.candidate_entry())
        self.assertEqual([], validate_registry(root))

    def test_active_project_requires_reviewed_specific_classification(self):
        root = self.root()
        self.make_project(root)
        path = root / "registry/projects/P-0001.json"
        entry = json.loads(path.read_text(encoding="utf-8"))
        entry["classification"] = self.classification(reviewed=False)
        path.write_bytes(pretty_json(entry))
        codes = {item.code for item in validate_registry(root)}
        self.assertTrue(
            {
                "classification_review_missing",
                "subject_review_missing",
                "classification_goals_unreviewed",
                "classification_tags_missing",
            }.issubset(codes)
        )

    def test_invalid_msc_code_is_rejected(self):
        root = self.root()
        entry = self.candidate_entry()
        entry["classification"]["subject"]["primary"] = "number-theory"
        self.write_entry(root, entry)
        self.assertIn("subject_primary_invalid", {item.code for item in validate_registry(root)})

    def test_typed_project_and_knowledge_dependencies_must_exist(self):
        root = self.root()
        entry = self.candidate_entry()
        entry["dependencies"]["projects"] = ["P-9999"]
        entry["dependencies"]["knowledge"] = ["K-9999"]
        self.write_entry(root, entry)
        codes = {item.code for item in validate_registry(root)}
        self.assertIn("dependency_missing", codes)
        self.assertIn("knowledge_dependency_missing", codes)

    def test_project_dependency_cycle_is_rejected(self):
        root = self.root()
        first = self.candidate_entry("P-0001")
        second = self.candidate_entry("P-0002")
        first["dependencies"]["projects"] = ["P-0002"]
        second["dependencies"]["projects"] = ["P-0001"]
        self.write_entry(root, first)
        self.write_entry(root, second)
        self.assertIn("project_dependency_cycle", {item.code for item in validate_registry(root)})

    def test_feedback_event_requires_existing_receipt(self):
        root = self.root()
        entry = self.candidate_entry()
        entry["result_feedback"].update(
            {
                "event_type": "source_audit",
                "event_id": "SA-0001",
                "receipt": "missing/source-audit.md",
                "frontier_movement": "clarified",
            }
        )
        self.write_entry(root, entry)
        self.assertIn("feedback_receipt_missing", {item.code for item in validate_registry(root)})

    def test_merged_window_requires_audited_feedback_projection(self):
        root = self.root()
        _, entry = self.make_project(root)
        entry["last_merged_window"] = "W-0001"
        self.write_entry(root, entry)
        self.assertIn("feedback_missing_after_window", {item.code for item in validate_registry(root)})

    def test_valid_reference_only_knowledge_node(self):
        root = self.root()
        self.write_knowledge(root, self.knowledge_node("K-0001"))
        self.assertEqual([], validate_knowledge_nodes(root))

    def test_knowledge_prerequisite_cycle_is_rejected(self):
        root = self.root()
        self.write_knowledge(root, self.knowledge_node("K-0001", prerequisites=["K-0002"]))
        self.write_knowledge(root, self.knowledge_node("K-0002", prerequisites=["K-0001"]))
        self.assertIn("knowledge_prerequisite_cycle", {item.code for item in validate_knowledge_nodes(root)})

    def test_knowledge_relation_target_must_exist(self):
        root = self.root()
        self.write_knowledge(
            root,
            self.knowledge_node("K-0001", relations=[{"type": "motivates", "target": "P-9999"}]),
        )
        self.assertIn("knowledge_relation_target_missing", {item.code for item in validate_knowledge_nodes(root)})

    def test_catalog_projects_expose_facets_dependencies_and_feedback(self):
        root = self.root()
        _, entry = self.make_project(root)
        node = self.knowledge_node("K-0001")
        payload = catalog_payload([entry], [node])
        self.assertEqual("11A05", payload["projects"][0]["classification"]["subject"]["primary"])
        self.assertEqual(default_dependencies(), payload["projects"][0]["dependencies"])
        self.assertEqual("not_started", payload["projects"][0]["result_feedback"]["frontier_movement"])
        self.assertEqual(1, payload["counts"]["knowledge_nodes"])
        markdown = frontier_markdown([entry], [node])
        self.assertIn("Synthetic hard problem", markdown)
        self.assertIn("Knowledge network", markdown)

    def test_empty_catalog_remains_byte_compatible(self):
        self.assertEqual(
            {
                "schema": "jin-math-catalog/v1",
                "projects": [],
                "counts": {
                    "projects": 0,
                    "active": 0,
                    "review_gate": 0,
                    "compute_wait": 0,
                    "terminal_audit": 0,
                    "closed": 0,
                },
            },
            catalog_payload([]),
        )
        self.assertEqual(
            "# Research frontier\n\n<!-- Generated by scripts/build_catalog.py. Do not edit manually. -->\n\n当前尚未登记研究项目。\n",
            frontier_markdown([]),
        )


if __name__ == "__main__":
    unittest.main()
