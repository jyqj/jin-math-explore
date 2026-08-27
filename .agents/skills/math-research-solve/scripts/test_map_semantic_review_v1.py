from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from map_semantic_review_v1 import (
    MAX_CYCLES,
    RESULT_SCHEMA,
    REVIEWER_MODE,
    SYNTHESIS_ROLES,
    ReviewError,
    _visible_rows,
    build_test_closure,
    document_sha256,
    finalize_documents,
    result_contract_sha256,
    sha256,
    ticket_id_for,
    validate_closure_document,
    validate_packet_document,
    validate_result_document,
)
from test_v13_contract_and_harness import make_project


def valid_fixture(root: Path):
    make_project(root)
    closure = build_test_closure(root)
    row = closure["rounds"][0]
    return closure, copy.deepcopy(row["packet"]), copy.deepcopy(row["ticket"]), copy.deepcopy(row["result"])


def result_for(packet, ticket, verdict="PASS"):
    component = "PASS" if verdict == "PASS" else verdict
    rationale = "bounded deterministic review rationale"
    result = {
        "schema": RESULT_SCHEMA,
        "ticket_id": ticket["ticket_id"],
        "packet_sha256": ticket["packet_sha256"],
        "protocol_sha256": ticket["protocol_sha256"],
        "project_id": ticket["project_id"],
        "candidate_map_sha256": ticket["candidate_map_sha256"],
        "visible_tree_inventory_sha256": ticket["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": ticket["authority_manifest_sha256"],
        "authority_inventory_sha256": ticket["authority_inventory_sha256"],
        "structural_receipt_sha256": ticket["structural_receipt_sha256"],
        "reviewer_principal": ticket["reviewer_principal"],
        "reviewer_mode": ticket["reviewer_mode"],
        "dispatch_id": ticket["dispatch_id"],
        "cycle": ticket["cycle"],
        "authority_coverage": [{"authority_id": row["authority_id"], "verdict": component, "rationale": rationale} for row in packet["authority"]["entries"]],
        "synthesis_checks": [{"role": role, "verdict": component, "rationale": rationale} for role in SYNTHESIS_ROLES],
        "evidence_boundary": {"classification": "minimized-remote", "categories_seen": ["research-map-control"], "retrieval_requests": []},
        "verdict": verdict,
        "repairs": [] if verdict == "PASS" else ["repair the frozen finding"],
        "unresolved": ["obtain bounded evidence"] if verdict == "INCONCLUSIVE" else [],
    }
    return result


def next_round(packet, prior_result, cycle, reviewer, verdict):
    candidate = copy.deepcopy(packet)
    candidate["candidate"]["map_control"]["fixture_revision"] = cycle
    candidate["candidate"]["map_control_semantic_sha256"] = document_sha256(candidate["candidate"]["map_control"])
    candidate_sha = document_sha256({"candidate": cycle})
    candidate["candidate"]["map_control_sha256"] = candidate_sha
    for row in candidate["candidate"]["visible_tree_inventory"]:
        if row["path"] == candidate["candidate"]["map_control_path"]:
            row["sha256"] = candidate_sha
            row["size"] += cycle
    candidate["candidate"]["visible_tree_inventory_sha256"] = document_sha256(candidate["candidate"]["visible_tree_inventory"])
    prior_sha = document_sha256(prior_result)
    lineage = {
        "prior_result_path": f".research/map-review/result-{cycle - 1}.json",
        "prior_result_sha256": prior_sha,
        "from_candidate_map_sha256": prior_result["candidate_map_sha256"],
        "to_candidate_map_sha256": candidate_sha,
        "findings_sha256": document_sha256({"repairs": prior_result["repairs"], "unresolved": prior_result["unresolved"]}),
        "repair_summary": "Applied the immutable prior findings to a new candidate.",
    }
    ticket = {
        "schema": "math-research-map-review-ticket/v1",
        "ticket_id": f"ticket-{cycle}",
        "packet_sha256": document_sha256(candidate),
        "protocol_sha256": candidate["protocol"]["sha256"],
        "project_id": candidate["project"]["project_id"],
        "candidate_map_sha256": candidate_sha,
        "visible_tree_inventory_sha256": candidate["candidate"]["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": candidate["authority"]["manifest_sha256"],
        "authority_inventory_sha256": candidate["authority"]["inventory_sha256"],
        "structural_receipt_sha256": candidate["structural_validation"]["sha256"],
        "author_principal": "fixture-author",
        "reviewer_principal": reviewer,
        "reviewer_mode": REVIEWER_MODE,
        "dispatch_id": f"dispatch-{cycle}",
        "cycle": cycle,
        "max_cycles": MAX_CYCLES,
        "prior_result_sha256": prior_sha,
        "repair_lineage": lineage,
        "result_contract_sha256": result_contract_sha256(),
        "retrieval_request_sha256": None,
    }
    ticket["ticket_id"] = ticket_id_for(ticket)
    return candidate, ticket, result_for(candidate, ticket, verdict)


def evidence_only_round(packet, prior_result, cycle, reviewer, verdict):
    candidate = copy.deepcopy(packet)
    slice_content = "Bounded proposition and quantifier summary requested by the reviewer."
    candidate["evidence_boundary"]["retrieval_request_sha256"] = document_sha256({"request": cycle})
    candidate["evidence_boundary"]["evidence_slices"] = [{
        "slice_id": f"bounded-slice-{cycle}",
        "source_category": "bounded-authority-summary",
        "sha256": sha256(slice_content.encode("utf-8")),
        "content": slice_content,
    }]
    prior_sha = document_sha256(prior_result)
    lineage = {
        "prior_result_path": f".research/map-review/result-{cycle - 1}.json",
        "prior_result_sha256": prior_sha,
        "from_candidate_map_sha256": prior_result["candidate_map_sha256"],
        "to_candidate_map_sha256": prior_result["candidate_map_sha256"],
        "findings_sha256": document_sha256({"repairs": prior_result["repairs"], "unresolved": prior_result["unresolved"]}),
        "repair_summary": "Supplied the smallest bounded evidence slice requested by the prior reviewer.",
    }
    ticket = {
        "schema": "math-research-map-review-ticket/v1",
        "ticket_id": f"ticket-{cycle}",
        "packet_sha256": document_sha256(candidate),
        "protocol_sha256": candidate["protocol"]["sha256"],
        "project_id": candidate["project"]["project_id"],
        "candidate_map_sha256": prior_result["candidate_map_sha256"],
        "visible_tree_inventory_sha256": candidate["candidate"]["visible_tree_inventory_sha256"],
        "authority_manifest_sha256": candidate["authority"]["manifest_sha256"],
        "authority_inventory_sha256": candidate["authority"]["inventory_sha256"],
        "structural_receipt_sha256": candidate["structural_validation"]["sha256"],
        "author_principal": "fixture-author",
        "reviewer_principal": reviewer,
        "reviewer_mode": REVIEWER_MODE,
        "dispatch_id": f"dispatch-{cycle}",
        "cycle": cycle,
        "max_cycles": MAX_CYCLES,
        "prior_result_sha256": prior_sha,
        "repair_lineage": lineage,
        "result_contract_sha256": result_contract_sha256(),
        "retrieval_request_sha256": candidate["evidence_boundary"]["retrieval_request_sha256"],
    }
    ticket["ticket_id"] = ticket_id_for(ticket)
    return candidate, ticket, result_for(candidate, ticket, verdict)


class MapSemanticReviewTests(unittest.TestCase):
    def test_sufficient_condition_register_enters_minimized_packet_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            map_root = root / "研究地图"
            register_rel = Path(".research/sufficient-conditions/example-topic.json")
            register = {"schema": "math-research-sufficient-condition-register/v1", "fixture": True}
            register_raw = (json.dumps(register, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            (map_root / register_rel).parent.mkdir(parents=True, exist_ok=True)
            (map_root / register_rel).write_bytes(register_raw)
            (map_root / "01-主研究地图.md").write_text(
                "## 充分条件\n\n"
                f'<!-- research-map-sufficient-condition-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{"a" * 64}","register_path":".research/sufficient-conditions/example-topic.json","register_sha256":"{sha256(register_raw)}"}} -->\n',
                encoding="utf-8",
            )
            control = map_root / ".research/research-map.json"
            control.parent.mkdir(parents=True, exist_ok=True)
            control.write_text("{}\n", encoding="utf-8")
            rows, documents = _visible_rows(
                root,
                lambda rel: root.joinpath(*Path(rel).parts).read_bytes(),
                "研究地图/.research/research-map.json",
            )
            expected = "研究地图/.research/sufficient-conditions/example-topic.json"
            self.assertIn(expected, {row["path"] for row in rows})
            self.assertIn(expected, {row["path"] for row in documents})

    def test_sufficient_condition_register_cannot_expand_to_raw_project_data(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            map_root = root / "研究地图"
            map_root.mkdir(parents=True, exist_ok=True)
            (map_root / "01-主研究地图.md").write_text(
                "## 充分条件\n\n"
                f'<!-- research-map-sufficient-condition-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{"a" * 64}","register_path":"../raw/full-project.json","register_sha256":"{"b" * 64}"}} -->\n',
                encoding="utf-8",
            )
            control = map_root / ".research/research-map.json"
            control.parent.mkdir(parents=True, exist_ok=True)
            control.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ReviewError, "closed map location"):
                _visible_rows(
                    root,
                    lambda rel: root.joinpath(*Path(rel).parts).read_bytes(),
                    "研究地图/.research/research-map.json",
                )

    def test_thin_pass_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, ticket, _ = valid_fixture(Path(td))
            with self.assertRaises(ReviewError):
                validate_result_document(packet, ticket, {"verdict": "PASS"})

    def test_ticket_id_binds_every_closed_ticket_field(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, ticket, result = valid_fixture(Path(td))
            ticket["dispatch_id"] = "substituted-dispatch"
            result["dispatch_id"] = ticket["dispatch_id"]
            with self.assertRaisesRegex(ReviewError, "Ticket ID must bind"):
                validate_result_document(packet, ticket, result)

    def test_author_reviewer_and_mode_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, ticket, result = valid_fixture(Path(td))
            ticket["reviewer_principal"] = ticket["author_principal"]
            ticket["ticket_id"] = ticket_id_for(ticket)
            result["reviewer_principal"] = ticket["reviewer_principal"]
            result["ticket_id"] = ticket["ticket_id"]
            with self.assertRaisesRegex(ReviewError, "Reviewer principal"):
                validate_result_document(packet, ticket, result)
            _, packet, ticket, result = valid_fixture(Path(td))
            ticket["reviewer_mode"] = result["reviewer_mode"] = "single_agent_fallback"
            ticket["ticket_id"] = ticket_id_for(ticket)
            result["ticket_id"] = ticket["ticket_id"]
            with self.assertRaises(ReviewError):
                validate_result_document(packet, ticket, result)

    def test_complete_coverage_and_all_eight_roles_are_required(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, ticket, result = valid_fixture(Path(td))
            result["authority_coverage"].pop()
            with self.assertRaisesRegex(ReviewError, "Every authority"):
                validate_result_document(packet, ticket, result)
            result = result_for(packet, ticket)
            result["synthesis_checks"].pop()
            with self.assertRaisesRegex(ReviewError, "eight synthesis"):
                validate_result_document(packet, ticket, result)

    def test_pass_cannot_contain_repairs_or_unresolved(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, ticket, result = valid_fixture(Path(td))
            result["repairs"] = ["still open"]
            with self.assertRaisesRegex(ReviewError, "PASS requires"):
                validate_result_document(packet, ticket, result)

    def test_packet_and_inventory_hash_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet, _, _ = valid_fixture(Path(td))
            packet["candidate"]["visible_documents"][0]["content"] += "tamper"
            with self.assertRaises(ReviewError):
                validate_packet_document(packet)
            _, packet, _, _ = valid_fixture(Path(td))
            packet["authority"]["entries"][0]["sha256"] = "0" * 64
            with self.assertRaises(ReviewError):
                validate_packet_document(packet)

    def test_map_byte_change_invalidates_old_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            closure, _, _, _ = valid_fixture(root)
            self.assertTrue(validate_closure_document(root, closure)["ok"])
            map_path = root / closure["bindings"]["map_control_path"]
            map_path.write_bytes(map_path.read_bytes() + b" ")
            result = validate_closure_document(root, closure)
            self.assertFalse(result["ok"])
            self.assertIn("closure_binding_stale", {row["code"] for row in result["issues"]})

    def test_fail_repair_fresh_reviewer_pass_forms_closure(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet1, ticket1, _ = valid_fixture(Path(td))
            result1 = result_for(packet1, ticket1, "FAIL")
            packet2, ticket2, result2 = next_round(packet1, result1, 2, "fresh-reviewer-2", "PASS")
            closure = finalize_documents([(packet1, ticket1, result1), (packet2, ticket2, result2)])
            self.assertEqual(closure["final_pass"]["cycle"], 2)
            self.assertEqual(len(closure["repair_lineage"]), 1)

    def test_inconclusive_can_resume_same_candidate_only_with_bounded_new_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            _, packet1, ticket1, _ = valid_fixture(Path(td))
            result1 = result_for(packet1, ticket1, "INCONCLUSIVE")
            packet2, ticket2, result2 = evidence_only_round(packet1, result1, 2, "fresh-reviewer-2", "PASS")
            closure = finalize_documents([(packet1, ticket1, result1), (packet2, ticket2, result2)])
            self.assertEqual(closure["rounds"][0]["candidate_map_sha256"], closure["rounds"][1]["candidate_map_sha256"])
            ticket2["retrieval_request_sha256"] = None
            packet2["evidence_boundary"]["retrieval_request_sha256"] = None
            packet2["evidence_boundary"]["evidence_slices"] = []
            ticket2["packet_sha256"] = document_sha256(packet2)
            ticket2["ticket_id"] = ticket_id_for(ticket2)
            result2 = result_for(packet2, ticket2, "PASS")
            with self.assertRaisesRegex(ReviewError, "bounded new evidence"):
                finalize_documents([(packet1, ticket1, result1), (packet2, ticket2, result2)])

    def test_reviewer_reuse_and_three_failures_do_not_close(self):
        with tempfile.TemporaryDirectory() as td:
            _, p1, t1, _ = valid_fixture(Path(td))
            r1 = result_for(p1, t1, "FAIL")
            p2, t2, r2 = next_round(p1, r1, 2, t1["reviewer_principal"], "PASS")
            with self.assertRaisesRegex(ReviewError, "new reviewer"):
                finalize_documents([(p1, t1, r1), (p2, t2, r2)])
            p2, t2, r2 = next_round(p1, r1, 2, "fresh-reviewer-2", "FAIL")
            p3, t3, r3 = next_round(p2, r2, 3, "fresh-reviewer-3", "FAIL")
            with self.assertRaisesRegex(ReviewError, "final exact-candidate PASS"):
                finalize_documents([(p1, t1, r1), (p2, t2, r2), (p3, t3, r3)])

    def test_packet_excludes_unrelated_and_forbidden_trees(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_project(root)
            (root / "README.md").write_text("UNRELATED-SECRET\n", encoding="utf-8")
            for rel in (".research/raw-objects/raw.md", "imports/import.md", "recovery-tree/recover.md", "logs/run.md"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("FORBIDDEN-SECRET\n", encoding="utf-8")
            closure = build_test_closure(root)
            packet = closure["rounds"][0]["packet"]
            serialized = json.dumps(packet, ensure_ascii=False)
            self.assertNotIn("UNRELATED-SECRET", serialized)
            self.assertNotIn("FORBIDDEN-SECRET", serialized)
            visible_paths = [row["path"] for row in packet["candidate"]["visible_documents"]]
            self.assertTrue(all(path.startswith("研究地图/") for path in visible_paths))


if __name__ == "__main__":
    unittest.main()
