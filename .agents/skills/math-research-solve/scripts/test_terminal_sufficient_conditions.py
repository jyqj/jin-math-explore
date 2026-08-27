#!/usr/bin/env python3
"""Deterministic success and blocked paths for terminal sufficient-condition registers."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("research_map_v1.py")
SPEC = importlib.util.spec_from_file_location("research_map_v1_sufficient_test", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

MANIFEST = "a" * 64
OBJECTIVE = "b" * 64


def register_fixture() -> dict:
    evidence = ["memory:synthetic-terminal-analysis"]
    return {
        "schema": MODULE.SUFFICIENT_REGISTER_SCHEMA,
        "topic_id": "example-topic",
        "project_id": "synthetic-project",
        "project_objective_sha256": OBJECTIVE,
        "authority_manifest_sha256": MANIFEST,
        "coverage_claim": "The complete current authority inventory was checked for non-equivalent terminal propositions and material near-misses.",
        "difficulty_basis": "Compare the number and kind of still-open quantified bridges while preserving evidence-backed incomparability.",
        "conditions": [
            {
                "condition_id": "criterion-zero",
                "statement": "A general effective certificate with a strict terminal rate holds.",
                "objective_implication": "The registered general theorem directly yields the immutable objective.",
                "terminality": "direct",
                "kind": "criterion",
                "closed_prerequisites": [],
                "open_obligations": ["Instantiate the criterion in a concrete construction."],
                "route_ids": [],
                "evidence_refs": evidence,
                "difficulty_disposition": {
                    "status": "criterion_scale",
                    "rationale": "This is a criterion layer, not an independent construction program on the route scale.",
                },
            },
            {
                "condition_id": "route-alpha-certificate",
                "statement": "Route alpha closes its global estimate and strict terminal inequality.",
                "objective_implication": "It implies criterion-zero through the registered implication edge.",
                "terminality": "via_registered_condition",
                "kind": "actionable",
                "closed_prerequisites": ["An integer object is already available."],
                "open_obligations": ["Prove a uniform global estimate."],
                "route_ids": ["route-alpha"],
                "evidence_refs": evidence,
                "difficulty_disposition": {
                    "status": "ranked",
                    "rationale": "It participates in the evidence-based partial order.",
                },
            },
            {
                "condition_id": "route-beta-certificate",
                "statement": "Route beta closes its nonvanishing amplitude and strict terminal inequality.",
                "objective_implication": "It implies criterion-zero through the registered implication edge.",
                "terminality": "via_registered_condition",
                "kind": "actionable",
                "closed_prerequisites": ["A recurrence is already available."],
                "open_obligations": ["Prove a stable nonzero amplitude."],
                "route_ids": ["route-beta"],
                "evidence_refs": evidence,
                "difficulty_disposition": {
                    "status": "ranked",
                    "rationale": "It participates in the evidence-based partial order.",
                },
            },
        ],
        "logical_relations": [
            {
                "source_id": "route-alpha-certificate",
                "relation": "implies",
                "target_id": "criterion-zero",
                "rationale": "Closing route alpha supplies every premise of the general criterion.",
                "evidence_refs": evidence,
            },
            {
                "source_id": "route-beta-certificate",
                "relation": "implies",
                "target_id": "criterion-zero",
                "rationale": "Closing route beta supplies every premise of the general criterion.",
                "evidence_refs": evidence,
            },
        ],
        "difficulty_relations": [
            {
                "source_id": "route-alpha-certificate",
                "relation": "incomparable_with",
                "target_id": "route-beta-certificate",
                "basis": "The remaining bridges belong to different analytic mechanisms and evidence gives no total order.",
                "evidence_refs": evidence,
            }
        ],
        "exclusions": [
            {
                "candidate_id": "local-decay-bound",
                "description": "A local decay estimate for one component.",
                "exclusion_reason": "It does not close the coefficient, nonvanishing, or terminal-rate obligations.",
                "evidence_refs": evidence,
            }
        ],
        "candidate_source_coverage": [
            {
                "source_id": "route-alpha-success-gate",
                "source_kind": "route_success_gate",
                "candidate_summary": "The route-alpha success gate is itself a terminal candidate once its global estimate is closed.",
                "disposition": "condition",
                "target_ids": ["route-alpha-certificate"],
                "route_ids": ["route-alpha"],
                "evidence_refs": evidence,
                "rationale": "The source candidate is represented by the exact actionable condition rather than compressed into the general criterion.",
            },
            {
                "source_id": "route-beta-review-candidate",
                "source_kind": "route_review",
                "candidate_summary": "The route-beta review states a terminal amplitude-and-rate certificate.",
                "disposition": "condition",
                "target_ids": ["route-beta-certificate"],
                "route_ids": ["route-beta"],
                "evidence_refs": evidence,
                "rationale": "The review candidate is separately represented and remains distinct from its individual premises.",
            },
        ],
    }


def write_fixture(
    root: Path,
    register: dict,
    *,
    register_hash: str | None = None,
    omit_entry: str | None = None,
    plain_entry: str | None = None,
    omit_definition_card: bool = False,
    stale_definition_hash: bool = False,
    hidden_definition_text: bool = False,
) -> None:
    register_rel = Path(".research") / "sufficient-conditions" / "example-topic.json"
    path = root / register_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = MODULE.canonical(register)
    path.write_bytes(raw)
    bound_hash = register_hash or MODULE.digest(raw)
    route_dir = root / "路线"
    evidence_dir = root / "证据"
    route_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (route_dir / "alpha.md").write_text(
        "# Alpha route\n\n## Route alpha\n\nroute-alpha is the complete synthetic alpha construction.\n",
        encoding="utf-8",
        newline="\n",
    )
    (route_dir / "beta.md").write_text(
        "# Beta route\n\n## Route beta\n\nroute-beta is the complete synthetic beta construction.\n",
        encoding="utf-8",
        newline="\n",
    )
    (evidence_dir / "synthetic.md").write_text(
        "# Synthetic evidence\n\n## Evidence\n\nThe fixture evidence supports the declared disposition.\n\n"
        "## Exact failure boundary\n\nThe local candidate stops before global nonvanishing and the strict terminal rate.\n",
        encoding="utf-8",
        newline="\n",
    )
    entries = "\n".join(
        f'### {row["condition_id"]}：Synthetic terminal proposition\n'
        f'<!-- research-map-sufficient-condition-entry:v1 {{"condition_id":"{row["condition_id"]}"}} -->\n'
        + (
            f'{row["statement"]}\n{row["objective_implication"]}\n'
            if row["condition_id"] == plain_entry
            else f'> [!proposition] Standalone terminal proposition for {row["condition_id"]}\n'
                 f'> **Hypothesis.** {row["statement"]}\n'
                 f'>\n'
                 f'> **Conclusion.** {row["objective_implication"]}\n'
        )
        for row in register["conditions"] if row["condition_id"] != omit_entry
    )
    exclusions = "\n".join(
        f'### 排除：{row["candidate_id"]}\n'
        f'<!-- research-map-sufficient-condition-exclusion:v1 {{"candidate_id":"{row["candidate_id"]}"}} -->\n'
        f'- **被排除候选：** {row["candidate_id"]}，{row["description"]}\n'
        f'- **排除范围：** 只排除该局部估计作为终端充分命题；{row["exclusion_reason"]}\n'
        f'- **路线保留：** 是，完整 alpha 路线仍可继续补齐全局义务。\n'
        f'- **路线：** [[路线/alpha#Route alpha|alpha 路线说明]]\n'
        f'- **证据：** [[证据/synthetic#Evidence|实际障碍证据]]\n'
        f'- **失败边界：** [[证据/synthetic#Exact failure boundary|精确失败边界]]\n'
        f'- **对应终端命题：** [[01-主研究地图#{register["conditions"][1]["condition_id"]}：Synthetic terminal proposition|{register["conditions"][1]["condition_id"]}]]\n'
        for row in register["exclusions"]
    )
    source_blocks = []
    for row in register["candidate_source_coverage"]:
        route_id = row["route_ids"][0]
        route_name = "alpha" if route_id == "route-alpha" else "beta"
        route_heading = "Route alpha" if route_id == "route-alpha" else "Route beta"
        terminal_links = "、".join(
            f'[[01-主研究地图#{target_id}：Synthetic terminal proposition|{target_id}]]'
            for target_id in row["target_ids"] if target_id in {item["condition_id"] for item in register["conditions"]}
        )
        source_blocks.append(
            f'### 来源：{row["source_id"]}\n'
            f'<!-- research-map-sufficient-condition-source:v1 {{"source_id":"{row["source_id"]}"}} -->\n'
            f'- **路线：** [[路线/{route_name}#{route_heading}|{route_id} 路线说明]]\n'
            f'- **证据：** [[证据/synthetic#Evidence|实际研究证据]]\n'
            f'- **失败边界：** [[证据/synthetic#Exact failure boundary|精确失败边界]]\n'
            f'- **对应终端命题：** {terminal_links}\n'
            f'- **登记处置：** {row["disposition"]} → {", ".join(row["target_ids"])}\n'
            f'- **说明：** {row["candidate_summary"]} {row["rationale"]}\n'
        )
    sources = "\n".join(source_blocks)
    definition_title = "Shared notation for the terminal propositions"
    definition_body = (
        "> The symbols $X_n$, $Y_n$, and the strict terminal rate are fixed once here for every proposition below.\n"
        "> A copied research target is portable only together with this definition card and its selected proposition callout.\n"
    )
    if hidden_definition_text:
        definition_body = "> <!-- Hidden definitions must never satisfy the visible shared-definition contract. -->\n"
    definition_hash = MODULE.sufficient_definition_digest(definition_title, definition_body)
    if stale_definition_hash:
        definition_hash = "d" * 64
    definition_card = "" if omit_definition_card else (
        f'<!-- research-map-sufficient-condition-definitions:v1 {{"topic_id":"example-topic","definition_id":"shared-notation","definition_sha256":"{definition_hash}"}} -->\n'
        f'> [!definition] {definition_title}\n'
        + definition_body
        + "\n"
    )
    note = (
        "## 普通专题状态\n\n"
        f'<!-- research-map-tracked-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{MANIFEST}"}} -->\n\n'
        "- **状态：** 当前目标开放，现有证据不能推出终局结论。\n"
        "- **进度：** 已闭合若干结构层，仍有全量词桥梁未完成。\n"
        "- **排序：** 按证据成熟度描述位置，不构成路线选择。\n\n"
        "## 终端充分命题分析\n\n"
        f'<!-- research-map-sufficient-condition-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{MANIFEST}","register_path":".research/sufficient-conditions/example-topic.json","register_sha256":"{bound_hash}"}} -->\n\n'
        + definition_card
        + "- **充分命题清单：** 以下逐项列出非等价终端充分命题，并区分上层判据与具体施工路线。\n"
        "- **逻辑关系：** 有向边只记录经证据支持的蕴含，未证等价和不可比性保持显式。\n"
        "- **难度排序：** 按剩余量词桥的数量和类型给出部分序，不表达成功概率。\n"
        "- **排除项：** 局部估计和单项前提另列，不冒充终端充分命题。\n\n"
        "- **来源覆盖：** 每个路线成功门和路线审查候选都逐条映射到命题或排除项。\n\n"
        + entries + "\n" + exclusions + "\n" + sources
    )
    (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8", newline="\n")


def validate(root: Path) -> list[dict[str, str]]:
    return MODULE.validate_terminal_sufficient_condition_sections(
        root,
        project_id="synthetic-project",
        project_objective_sha256=OBJECTIVE,
        authority_manifest_sha256=MANIFEST,
        route_ids={"route-alpha", "route-beta"},
        require_definition_card=True,
    )


class TerminalSufficientConditionTests(unittest.TestCase):
    def test_project_established_uppercase_ids_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            replacements = {
                "criterion-zero": "CriterionA",
                "route-alpha-certificate": "RouteB",
                "route-beta-certificate": "RouteC",
                "local-decay-bound": "X-LOCAL-DECAY",
            }
            for condition in register["conditions"]:
                condition["condition_id"] = replacements[condition["condition_id"]]
            for relation_group in (register["logical_relations"], register["difficulty_relations"]):
                for relation in relation_group:
                    relation["source_id"] = replacements[relation["source_id"]]
                    relation["target_id"] = replacements[relation["target_id"]]
            for source in register["candidate_source_coverage"]:
                source["target_ids"] = [replacements.get(target, target) for target in source["target_ids"]]
            register["exclusions"][0]["candidate_id"] = replacements["local-decay-bound"]
            write_fixture(root, register)
            self.assertEqual(validate(root), [])

    def test_complete_register_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            self.assertEqual(validate(root), [])

    def test_shared_definition_card_allows_concise_propositions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["conditions"][1]["statement"] = "Under the shared notation, route alpha closes its strict terminal inequality."
            write_fixture(root, register)
            self.assertEqual(validate(root), [])

    def test_missing_shared_definition_card_is_blocked_for_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), omit_definition_card=True)
            self.assertIn("sufficient_condition_definition_card_missing", {row["code"] for row in validate(root)})

    def test_stale_shared_definition_hash_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), stale_definition_hash=True)
            self.assertIn("sufficient_condition_definition_hash_stale", {row["code"] for row in validate(root)})

    def test_hidden_shared_definition_text_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), hidden_definition_text=True)
            codes = {row["code"] for row in validate(root)}
            self.assertIn("sufficient_condition_definition_hidden_text", codes)
            self.assertIn("sufficient_condition_definition_not_substantive", codes)

    def test_legacy_map_without_definition_card_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), omit_definition_card=True)
            issues = MODULE.validate_terminal_sufficient_condition_sections(
                root,
                project_id="synthetic-project",
                project_objective_sha256=OBJECTIVE,
                authority_manifest_sha256=MANIFEST,
                route_ids={"route-alpha", "route-beta"},
                require_definition_card=False,
            )
            self.assertEqual(issues, [])

    def test_plain_prose_instead_of_proposition_callout_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), plain_entry="route-alpha-certificate")
            self.assertIn("sufficient_condition_visible_callout_missing", {row["code"] for row in validate(root)})

    def test_non_descriptive_proposition_callout_title_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            text = text.replace(
                "> [!proposition] Standalone terminal proposition for route-alpha-certificate",
                "> [!proposition] route-alpha-certificate",
                1,
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_visible_callout_title_missing", {row["code"] for row in validate(root)})

    def test_proposition_callout_body_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            write_fixture(root, register)
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            text = text.replace(register["conditions"][1]["objective_implication"], "A different conclusion is shown.", 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_visible_callout_body_mismatch", {row["code"] for row in validate(root)})

    def test_hidden_html_comment_cannot_satisfy_callout_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            write_fixture(root, register)
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            statement = register["conditions"][1]["statement"]
            text = text.replace(statement, f"<!-- {statement} -->", 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            codes = {row["code"] for row in validate(root)}
            self.assertIn("sufficient_condition_visible_callout_hidden_text", codes)
            self.assertIn("sufficient_condition_visible_callout_body_mismatch", codes)

    def test_hidden_obsidian_comment_cannot_satisfy_callout_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            write_fixture(root, register)
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            statement = register["conditions"][1]["statement"]
            text = text.replace(statement, f"%% {statement} %%", 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            codes = {row["code"] for row in validate(root)}
            self.assertIn("sufficient_condition_visible_callout_hidden_text", codes)
            self.assertIn("sufficient_condition_visible_callout_body_mismatch", codes)

    def test_short_descriptive_chinese_title_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            text = text.replace(
                "> [!proposition] Standalone terminal proposition for route-alpha-certificate",
                "> [!proposition] 素数定理",
                1,
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertEqual(validate(root), [])

    def test_heading_between_marker_and_callout_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            needle = '<!-- research-map-sufficient-condition-entry:v1 {"condition_id":"route-alpha-certificate"} -->\n'
            text = text.replace(needle, needle + "### Detached heading\n\n", 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_visible_callout_not_immediate", {row["code"] for row in validate(root)})

    def test_marker_attached_to_previous_record_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            heading = "### route-alpha-certificate：Synthetic terminal proposition\n"
            marker = '<!-- research-map-sufficient-condition-entry:v1 {"condition_id":"route-alpha-certificate"} -->\n'
            text = text.replace(heading + marker, marker + heading, 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_entry_marker_position_invalid", {row["code"] for row in validate(root)})

    def test_exclusion_scope_and_route_retention_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            text = text.replace(
                "- **排除范围：** 只排除该局部估计作为终端充分命题；It does not close the coefficient, nonvanishing, or terminal-rate obligations.",
                "- **排除范围：** 短",
                1,
            ).replace("- **路线保留：** 是，完整 alpha 路线仍可继续补齐全局义务。", "- **路线保留：** 未说明", 1)
            main.write_text(text, encoding="utf-8", newline="\n")
            codes = {row["code"] for row in validate(root)}
            self.assertIn("sufficient_condition_exclusion_scope_missing", codes)
            self.assertIn("sufficient_condition_exclusion_route_retention_missing", codes)

    def test_missing_visible_route_link_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8").replace(
                "[[路线/alpha#Route alpha|alpha 路线说明]]", "alpha 路线说明", 1
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_exclusion_link_missing", {row["code"] for row in validate(root)})

    def test_missing_or_ambiguous_evidence_target_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8").replace(
                "[[证据/synthetic#Evidence|实际研究证据]]", "[[证据/not-present#Evidence|实际研究证据]]", 1
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_visible_link_missing_or_ambiguous", {row["code"] for row in validate(root)})

    def test_missing_failure_boundary_anchor_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8").replace(
                "#Exact failure boundary|精确失败边界", "#Unknown boundary|精确失败边界", 1
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            self.assertIn("sufficient_condition_visible_link_anchor_missing", {row["code"] for row in validate(root)})

    def test_visible_source_disposition_and_terminal_link_must_match_register(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            main = root / MODULE.MAIN_SURVEY
            text = main.read_text(encoding="utf-8")
            text = text.replace(
                "- **登记处置：** condition → route-alpha-certificate",
                "- **登记处置：** exclusion → local-decay-bound",
                1,
            ).replace(
                "#route-alpha-certificate：Synthetic terminal proposition|route-alpha-certificate",
                "#route-beta-certificate：Synthetic terminal proposition|route-beta-certificate",
                2,
            )
            main.write_text(text, encoding="utf-8", newline="\n")
            codes = {row["code"] for row in validate(root)}
            self.assertIn("sufficient_condition_source_disposition_mismatch", codes)
            self.assertIn("sufficient_condition_source_terminal_link_mismatch", codes)

    def test_missing_register_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture())
            (root / ".research/sufficient-conditions/example-topic.json").unlink()
            self.assertIn("sufficient_condition_register_missing", {row["code"] for row in validate(root)})

    def test_stale_register_hash_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), register_hash="c" * 64)
            self.assertIn("sufficient_condition_register_hash_stale", {row["code"] for row in validate(root)})

    def test_conjuncts_without_terminal_path_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["logical_relations"] = []
            write_fixture(root, register)
            self.assertIn("terminal_condition_not_terminal", {row["code"] for row in validate(root)})

    def test_missing_difficulty_coverage_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["difficulty_relations"] = []
            write_fixture(root, register)
            self.assertIn("terminal_condition_difficulty_uncovered", {row["code"] for row in validate(root)})

    def test_difficulty_cycle_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            evidence = ["memory:synthetic-terminal-analysis"]
            register["difficulty_relations"] = [
                {"source_id": "route-alpha-certificate", "relation": "easier_than", "target_id": "route-beta-certificate", "basis": "Synthetic directed comparison.", "evidence_refs": evidence},
                {"source_id": "route-beta-certificate", "relation": "easier_than", "target_id": "route-alpha-certificate", "basis": "Synthetic reverse comparison.", "evidence_refs": evidence},
            ]
            write_fixture(root, register)
            self.assertIn("sufficient_condition_difficulty_cycle", {row["code"] for row in validate(root)})

    def test_dangling_relation_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["logical_relations"][0]["target_id"] = "unknown-condition"
            write_fixture(root, register)
            self.assertIn("sufficient_condition_relation_dangling", {row["code"] for row in validate(root)})

    def test_duplicate_statement_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["conditions"][2]["statement"] = register["conditions"][1]["statement"]
            write_fixture(root, register)
            self.assertIn("sufficient_condition_duplicate_statement", {row["code"] for row in validate(root)})

    def test_visible_inventory_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, register_fixture(), omit_entry="route-beta-certificate")
            self.assertIn("sufficient_condition_visible_inventory_mismatch", {row["code"] for row in validate(root)})

    def test_route_review_terminal_candidate_must_be_source_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["candidate_source_coverage"] = register["candidate_source_coverage"][:1]
            write_fixture(root, register)
            self.assertIn("sufficient_condition_route_source_uncovered", {row["code"] for row in validate(root)})

    def test_every_route_has_an_actionable_terminal_condition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            register = register_fixture()
            register["conditions"][2]["route_ids"] = []
            write_fixture(root, register)
            self.assertIn("sufficient_condition_route_terminal_uncovered", {row["code"] for row in validate(root)})

    def test_registered_obligation_cannot_be_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as previous_dir, tempfile.TemporaryDirectory() as candidate_dir:
            previous = Path(previous_dir)
            candidate = Path(candidate_dir)
            write_fixture(previous, register_fixture())
            (candidate / MODULE.MAIN_SURVEY).write_text("## 普通地图\n\n没有充分条件登记。\n", encoding="utf-8")
            codes = {row["code"] for row in MODULE.validate_sufficient_condition_downgrade(previous, candidate)}
            self.assertIn("sufficient_condition_obligation_downgraded", codes)

    def test_ordinary_tracked_topic_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = (
                "## 普通专题\n\n"
                f'<!-- research-map-tracked-topic:v1 {{"topic_id":"ordinary-topic","authority_manifest_sha256":"{MANIFEST}"}} -->\n\n'
                "- **状态：** 当前仍开放，证据范围保持不变。\n"
                "- **进度：** 已闭合局部桥梁，仍缺全量词证明。\n"
                "- **排序：** 按证据成熟度描述地图位置，不作路线选择。\n"
            )
            (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8")
            self.assertEqual(validate(root), [])


if __name__ == "__main__":
    unittest.main()
