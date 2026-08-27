#!/usr/bin/env python3
"""Success and blocked-path tests for the v1 publication synthesis gate."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("research_map_v1.py")
SPEC = importlib.util.spec_from_file_location("research_map_v1_synthesis_test", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def synthesis_note(*, omit: str | None = None, short: str | None = None) -> str:
    sections = []
    for index, role in enumerate(MODULE.SYNTHESIS_ROLES, start=1):
        if role == omit:
            continue
        prose = "本节重新综合全部权威记忆、路线证据、历史转折与边界，说明对象之间的因果关系，并区分已验证事实、有限证据、推断和未知桥梁。" * 4
        if role == short:
            prose = "过短。"
        sections.append(f"## 综合章节 {index}\n\n<!-- research-map-synthesis:{role} -->\n\n{prose}\n")
    return "研究综述入口，术语集中见[[./03-术语与记号|术语与记号]]。\n\n" + "\n".join(sections)


def glossary_note(*, incomplete: bool = False) -> str:
    entries = []
    for index in range(MODULE.MIN_GLOSSARY_ENTRIES):
        confusion = "" if incomplete and index == 0 else "- **不要混淆：** 这不是普通索引，也不自动代表证据已经通过独立验证。\n"
        entries.append(
            f"### 术语 {index + 1}\n\n"
            "- **定义：** 这是一个范围明确并在当前研究项目中稳定使用的数学对象。\n"
            "- **在本项目中的作用：** 它连接具体证明步骤、证据范围和最终目标。\n"
            + confusion
        )
    return "<!-- research-map-glossary:v1 -->\n\n" + "\n".join(entries)


class ResearchMapSynthesisTests(unittest.TestCase):
    def test_complete_global_synthesis_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text(synthesis_note(), encoding="utf-8")
            self.assertEqual(MODULE.validate_global_synthesis(root), [])

    def test_append_only_map_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text("## 最新结果\n\n只登记一项新结果。\n", encoding="utf-8")
            codes = {issue["code"] for issue in MODULE.validate_global_synthesis(root)}
            self.assertIn("global_synthesis_role_missing", codes)
            self.assertIn("global_synthesis_note_too_short", codes)

    def test_shallow_role_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text(
                synthesis_note(short="cross-route-structure"), encoding="utf-8"
            )
            issues = MODULE.validate_global_synthesis(root)
            self.assertTrue(any(
                issue["code"] == "global_synthesis_role_too_short"
                and "cross-route-structure" in issue.get("detail", "")
                for issue in issues
            ))

    def test_duplicate_role_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = synthesis_note() + (
                "\n## 重复章节\n\n<!-- research-map-synthesis:frontier -->\n\n"
                + "重复内容用于证明门禁能够拒绝同一职责出现两次。" * 12
            )
            (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8")
            codes = {issue["code"] for issue in MODULE.validate_global_synthesis(root)}
            self.assertIn("global_synthesis_role_duplicate", codes)

    def test_complete_project_glossary_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text(synthesis_note(), encoding="utf-8")
            (root / MODULE.GLOSSARY_NOTE).write_text(glossary_note(), encoding="utf-8")
            self.assertEqual(MODULE.validate_project_glossary(root), [])

    def test_missing_project_glossary_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text(synthesis_note(), encoding="utf-8")
            codes = {issue["code"] for issue in MODULE.validate_project_glossary(root)}
            self.assertIn("project_glossary_missing", codes)

    def test_incomplete_glossary_entry_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text(synthesis_note(), encoding="utf-8")
            (root / MODULE.GLOSSARY_NOTE).write_text(glossary_note(incomplete=True), encoding="utf-8")
            codes = {issue["code"] for issue in MODULE.validate_project_glossary(root)}
            self.assertIn("project_glossary_field_missing", codes)

    def test_glossary_must_be_linked_from_main_survey(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / MODULE.MAIN_SURVEY).write_text("没有术语表链接。", encoding="utf-8")
            (root / MODULE.GLOSSARY_NOTE).write_text(glossary_note(), encoding="utf-8")
            codes = {issue["code"] for issue in MODULE.validate_project_glossary(root)}
            self.assertIn("project_glossary_main_link_missing", codes)

    def test_current_tracked_topic_section_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = "a" * 64
            note = synthesis_note() + (
                "\n## 专题追踪\n\n"
                f'<!-- research-map-tracked-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{manifest}"}} -->\n\n'
                "- **状态：** 当前仍是开放问题，已核验证据不能推出终局结论。\n"
                "- **进度：** 已闭合一项有限范围桥梁，仍缺全量词渐近估计。\n"
                "- **排序：** 按证据成熟度位于第一层，这不是下一窗口选路。\n"
            )
            (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8")
            self.assertEqual(
                MODULE.validate_tracked_topic_sections(root, authority_manifest_sha256=manifest),
                [],
            )

    def test_stale_tracked_topic_binding_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = (
                "## 专题追踪\n\n"
                f'<!-- research-map-tracked-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{"a" * 64}"}} -->\n\n'
                "- **状态：** 当前仍是开放问题，已核验证据不能推出终局结论。\n"
                "- **进度：** 已闭合一项有限范围桥梁，仍缺全量词渐近估计。\n"
                "- **排序：** 按证据成熟度位于第一层，这不是下一窗口选路。\n"
            )
            (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8")
            codes = {
                issue["code"]
                for issue in MODULE.validate_tracked_topic_sections(
                    root, authority_manifest_sha256="b" * 64
                )
            }
            self.assertIn("tracked_topic_manifest_binding_stale", codes)

    def test_incomplete_tracked_topic_section_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = "a" * 64
            note = (
                "## 专题追踪\n\n"
                f'<!-- research-map-tracked-topic:v1 {{"topic_id":"example-topic","authority_manifest_sha256":"{manifest}"}} -->\n\n'
                "- **状态：** 当前仍是开放问题，已核验证据不能推出终局结论。\n"
                "- **进度：** 已闭合一项有限范围桥梁，仍缺全量词渐近估计。\n"
            )
            (root / MODULE.MAIN_SURVEY).write_text(note, encoding="utf-8")
            issues = MODULE.validate_tracked_topic_sections(
                root, authority_manifest_sha256=manifest
            )
            self.assertTrue(any(
                issue["code"] == "tracked_topic_field_missing" and issue["detail"] == "排序"
                for issue in issues
            ))


if __name__ == "__main__":
    unittest.main()
