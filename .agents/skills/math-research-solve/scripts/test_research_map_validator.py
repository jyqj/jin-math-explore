#!/usr/bin/env python3
"""Synthetic success and blocked-path tests for validate_research_map.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).with_name("validate_research_map.py")
SPEC = importlib.util.spec_from_file_location("validate_research_map", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

OBJECTIVE = "1" * 64
HEAD = "2" * 64
EVIDENCE = "3" * 64


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_fixture(root: Path) -> None:
    asset = root / ".research" / "assets" / "route-a" / "evidence.txt"
    write(asset, "synthetic immutable evidence\n")
    write(
        root / "00-研究地图契约.md",
        f"## 永久目标与来源\n\n目标指纹 `{OBJECTIVE}`。\n\n[[01-主研究地图]]\n",
    )
    write(
        root / "01-主研究地图.md",
        f"目标指纹 `{OBJECTIVE}`。\n\n"
        "## 研究主线\n\n[[20-路线-example]]\n\n"
        "## 当前研究判断\n\n当前路线仍处于工作状态。\n\n"
        "## 如何审计\n\n[[00-研究地图契约]]、[[02-阅读说明与证据规则]]、"
        "[[40-当前候选路线与下一步]]、[[90-资产索引]]。\n",
    )
    write(
        root / "02-阅读说明与证据规则.md",
        "## 三层结构\n\n地图、节点、资产。\n\n"
        "## 证据词的含义\n\n工作结果不是证明。\n\n"
        "## 原始资产与解释页\n\n资产保持原字节。\n\n"
        "## AI 启动规则\n\n按需读取。\n",
    )
    write(
        root / "40-当前候选路线与下一步.md",
        "## 候选路线\n\n[[20-路线-example]]。\n\n"
        "## 恢复研究时的读取集合\n\n先读主地图，再读当前路线。\n",
    )
    write(
        root / "90-资产索引.md",
        "## 路线资产\n\n[[20-路线-example]]。\n\n"
        "## 哈希与来源\n\n机器清单文件：`99-资产清单.json`。\n",
    )
    write(
        root / "20-路线-example.md",
        "## 路线入口\n\n"
        "数学对象：冻结的合成对象。\n\n"
        "连接最终目标的机制：测试一条已登记的通用机制。\n\n"
        "已有证据：只有一个有限输入检查。\n\n"
        "尚缺内容：缺少全称桥梁。\n\n"
        "下一步成败判据：资产尚未冻结判据。\n\n"
        "## 快速结论\n\nSENTINEL_PRIVATE_BODY 工作中。\n\n"
        "## 路线位置与动机\n\n用于测试一个通用机制。\n\n"
        "## 数学对象与精确范围\n\n只处理冻结的合成对象。\n\n"
        "## 完整数学论证\n\n当前只得到一个明确的未闭合步骤。\n\n"
        "## 计算机辅助边界\n\n程序只核对有限输入。\n\n"
        "## 审计与复现入口\n\n证据文件：`evidence.txt`。\n\n"
        "## 不能推出什么与重开条件\n\n不能推出全称结论。\n",
    )
    controls = {}
    for key, rel in MODULE.CONTROL_PATHS.items():
        controls[key] = {"path": rel, "sha256": digest(root / rel)}
    manifest = {
        "schema": "math-research-map-asset-manifest/v1",
        "map_id": "synthetic-map",
        "source_head_sha256": HEAD,
        "assets": [
            {
                "path": ".research/assets/route-a/evidence.txt",
                "size": asset.stat().st_size,
                "sha256": digest(asset),
                "source_locator": "object:synthetic",
                "source_sha256": digest(asset),
                "role": "synthetic evidence",
                "node_ids": ["route-a"],
            }
        ],
    }
    (root / "99-资产清单.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    data = {
        "schema": "math-research-map/v2",
        "map_id": "synthetic-map",
        "map_version": 1,
        "project_id": "synthetic-project",
        "project_schema": "math-research-project/v12",
        "objective_sha256": OBJECTIVE,
        "source_head_sha256": HEAD,
        "status": "current",
        "control_notes": controls,
        "asset_manifest": "99-资产清单.json",
        "active_route_ids": ["route-a"],
        "nodes": [
            {
                "id": "route-a",
                "kind": "route",
                "state": "active",
                "note": "20-路线-example.md",
                "note_sha256": digest(root / "20-路线-example.md"),
                "sections": {
                    "summary": "快速结论",
                    "motivation": "路线位置与动机",
                    "scope": "数学对象与精确范围",
                    "argument": "完整数学论证",
                    "computer_boundary": "计算机辅助边界",
                    "audit": "审计与复现入口",
                    "limits_reopen": "不能推出什么与重开条件",
                },
                "route_entry": {
                    "heading": "路线入口",
                    "fields": {
                        "mathematical_object": {
                            "asset_status": "supported",
                            "source_refs": ["memory:synthetic-memory"],
                            "gap": "",
                        },
                        "objective_mechanism": {
                            "asset_status": "supported",
                            "source_refs": ["asset:.research/assets/route-a/evidence.txt"],
                            "gap": "",
                        },
                        "evidence_boundary": {
                            "asset_status": "supported",
                            "source_refs": [f"evidence:{EVIDENCE}"],
                            "gap": "",
                        },
                        "missing_work": {
                            "asset_status": "supported",
                            "source_refs": ["memory:synthetic-memory"],
                            "gap": "",
                        },
                        "success_failure_gate": {
                            "asset_status": "missing_from_assets",
                            "source_refs": ["memory:synthetic-memory"],
                            "gap": "No frozen gate exists in the synthetic record.",
                        },
                    },
                },
                "memory_ids": ["synthetic-memory"],
                "evidence_sha256s": [EVIDENCE],
                "required_assets": [".research/assets/route-a/evidence.txt"],
            }
        ],
    }
    (root / "research-map.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def arguments(root: Path, **overrides: object) -> SimpleNamespace:
    values = {
        "map_root": str(root),
        "expected_objective_sha256": OBJECTIVE,
        "expected_source_head_sha256": HEAD,
        "expected_project_schema": "math-research-project/v12",
        "allow_stale": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ResearchMapValidatorTests(unittest.TestCase):
    def test_valid_map_passes_without_emitting_note_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            result = MODULE.validate_map(arguments(root))
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["counts"]["nodes"], 1)
            self.assertNotIn("SENTINEL_PRIVATE_BODY", json.dumps(result, ensure_ascii=False))

    def test_tampered_asset_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            write(root / ".research" / "assets" / "route-a" / "evidence.txt", "tampered\n")
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("asset_hash_mismatch", codes)

    def test_wrong_objective_binding_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            result = MODULE.validate_map(arguments(root, expected_objective_sha256="9" * 64))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("expected_binding_mismatch", codes)

    def test_route_without_grounded_entry_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            data = json.loads((root / "research-map.json").read_text(encoding="utf-8"))
            del data["nodes"][0]["route_entry"]
            (root / "research-map.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("invalid_route_entry", codes)

    def test_unbound_route_entry_source_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            data = json.loads((root / "research-map.json").read_text(encoding="utf-8"))
            data["nodes"][0]["route_entry"]["fields"]["mathematical_object"]["source_refs"] = [
                "memory:not-bound-to-this-node"
            ]
            (root / "research-map.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("unbound_route_entry_source", codes)

    def test_missing_asset_explanation_requires_explicit_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            data = json.loads((root / "research-map.json").read_text(encoding="utf-8"))
            data["nodes"][0]["route_entry"]["fields"]["success_failure_gate"]["gap"] = ""
            (root / "research-map.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("missing_route_entry_gap", codes)


    def test_non_markdown_local_hyperlink_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            note = root / "20-路线-example.md"
            text = note.read_text(encoding="utf-8")
            text = text.replace("证据文件：`evidence.txt`。", "[证据](.research/assets/route-a/evidence.txt)。")
            write(note, text)
            data = json.loads((root / "research-map.json").read_text(encoding="utf-8"))
            data["nodes"][0]["note_sha256"] = digest(note)
            (root / "research-map.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("non_markdown_local_hyperlink", codes)

    def test_visible_assets_directory_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_fixture(root)
            (root / "assets").mkdir()
            result = MODULE.validate_map(arguments(root))
            self.assertFalse(result["ok"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("visible_assets_directory_forbidden", codes)


if __name__ == "__main__":
    unittest.main()
