#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).with_name("math_research_assets.py")
SPEC = importlib.util.spec_from_file_location("math_research_assets", MODULE)
assets = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(assets)


def write(path: Path, data: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"role": "artifact", "path": path.as_posix(), "sha256": assets.sha_file(path), "bytes": len(data)}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(assets.canonical_bytes(value))


class AssetFixture:
    def __init__(self, base: Path):
        self.root = base / "project"
        self.root.mkdir()
        paper = self.root / "assets/paper.pdf"
        upstream = self.root / "assets/upstream/search.py"
        license_file = self.root / "assets/upstream/LICENSE"
        local = self.root / "code/local_search.py"
        result = self.root / "results/test.json"
        for path, data in ((paper, b"%PDF synthetic\n"), (upstream, b"print('upstream')\n"), (license_file, b"MIT\n"), (local, b"print('derived')\n"), (result, b"{\"ok\":true}\n")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        def artifact(path: Path, role: str) -> dict[str, object]:
            return {"role": role, "path": path.relative_to(self.root).as_posix(), "sha256": assets.sha_file(path), "bytes": path.stat().st_size}
        citation = {"required": True, "key": "Fang2026", "text": "Fang (2026)", "bibtex": "@article{Fang2026, title={Synthetic Fang paper}, author={Fang}}"}
        empty_citation = {"required": False, "key": "", "text": "", "bibtex": ""}
        source = {"locator": "https://arxiv.org/abs/0000.00000", "identifier": "arXiv:0000.00000", "version": "v1", "upstream_commit": None, "acquired_at_utc": "2026-08-13T00:00:00Z"}
        self.registry = {
            "schema": "math-research-asset-registry/v1", "project_id": "proj", "registry_id": "registry-1", "created_at_utc": "2026-08-13T00:00:00Z",
            "assets": [
                {"asset_id": "fang-paper", "kind": "paper", "title": "Synthetic Fang paper", "origin": "external", "creators": [{"type": "person", "name": "Fang", "role": "author"}], "source": source, "local_artifacts": [artifact(paper, "paper_pdf")], "license": {"status": "unknown", "identifier": None, "license_artifact": None, "redistribution": "private_only"}, "citation": citation, "supported_claims": ["The synthetic search theorem."], "usage": {"entrypoints": [], "environment": "PDF reader", "verification": "Source record checked."}, "limitations": ["Synthetic fixture."], "export": {"mother_bundle": True, "paper_support_bundle": True}},
                {"asset_id": "fang-upstream", "kind": "code", "title": "Upstream search", "origin": "external", "creators": [{"type": "person", "name": "Fang", "role": "author"}], "source": {**source, "locator": "https://example.test/code", "identifier": "upstream-v1", "version": "v1.0.0", "upstream_commit": "abc123"}, "local_artifacts": [artifact(upstream, "source_code"), artifact(license_file, "license")], "license": {"status": "spdx", "identifier": "MIT", "license_artifact": "assets/upstream/LICENSE", "redistribution": "public_allowed"}, "citation": citation, "supported_claims": ["Reference implementation."], "usage": {"entrypoints": ["python assets/upstream/search.py"], "environment": "Python 3", "verification": "Smoke test passed."}, "limitations": [], "export": {"mother_bundle": True, "paper_support_bundle": True}},
                {"asset_id": "local-derived", "kind": "code", "title": "Local derived search", "origin": "ai_assisted", "creators": [{"type": "ai_system", "name": "Codex", "role": "implementation assistant"}, {"type": "user", "name": "project user", "role": "director"}], "source": {"locator": None, "identifier": "local-derived-v1", "version": "v1", "upstream_commit": None, "acquired_at_utc": "2026-08-13T00:00:00Z"}, "local_artifacts": [artifact(local, "source_code"), artifact(result, "test_output")], "license": {"status": "unknown", "identifier": None, "license_artifact": None, "redistribution": "private_only"}, "citation": empty_citation, "supported_claims": ["Derived implementation of the theorem."], "usage": {"entrypoints": ["python code/local_search.py"], "environment": "Python 3", "verification": "results/test.json"}, "limitations": ["Not a certified Arb computation."], "export": {"mother_bundle": True, "paper_support_bundle": True}},
            ],
        }
        self.ledger = {
            "schema": "math-research-contribution-ledger/v1", "project_id": "proj", "ledger_id": "ledger-1", "created_at_utc": "2026-08-13T00:00:00Z",
            "contributions": [{"contribution_id": "local-reimplementation", "kind": "code_component", "statement": "AI-assisted local reimplementation based on the paper theorem.", "origin": "ai_assisted", "relation": "reimplemented", "contributors": [{"type": "ai_system", "name": "Codex", "role": "implementation assistant"}], "source_asset_ids": ["fang-paper", "fang-upstream"], "artifact_refs": [{"path": "code/local_search.py", "sha256": assets.sha_file(local), "symbol": "main"}], "citation_required": True, "verification_grade": "verified_computation", "limitations": ["Synthetic fixture."]}],
        }
        self.policy = {"schema": "math-research-export-policy/v1", "project_id": "proj", "default_visibility": "private", "scan_roots": ["assets", "code", "results"], "scan_exclusions": [], "profiles": {"mother_bundle": {"visibility": "private", "description": "Full private archive."}, "paper_support_bundle": {"visibility": "private", "description": "Private paper support."}}, "created_at_utc": "2026-08-13T00:00:00Z"}
        self.registry_path = self.root / "state/assets/registry.json"
        self.ledger_path = self.root / "state/assets/ledger.json"
        self.policy_path = self.root / "state/assets/policy.json"
        dump(self.registry_path, self.registry); dump(self.ledger_path, self.ledger); dump(self.policy_path, self.policy)
        def ptr(path: Path) -> dict[str, str]:
            return {"path": path.relative_to(self.root).as_posix(), "sha256": assets.sha_file(path)}
        self.index = {"schema": "math-research-asset-index/v1", "project_id": "proj", "authority": "authoritative", "asset_registry": ptr(self.registry_path), "contribution_ledger": ptr(self.ledger_path), "export_policy": ptr(self.policy_path), "created_at_utc": "2026-08-13T00:00:00Z"}
        self.index_path = self.root / "state/assets/index.json"
        dump(self.index_path, self.index)

    def rewrite(self) -> None:
        dump(self.registry_path, self.registry); dump(self.ledger_path, self.ledger); dump(self.policy_path, self.policy)
        self.index["asset_registry"]["sha256"] = assets.sha_file(self.registry_path)
        self.index["contribution_ledger"]["sha256"] = assets.sha_file(self.ledger_path)
        self.index["export_policy"]["sha256"] = assets.sha_file(self.policy_path)
        dump(self.index_path, self.index)


class AssetTests(unittest.TestCase):
    def test_valid_and_deterministic_dual_export(self):
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td))
            result = assets.validate_project(f.root, f.index_path)
            self.assertEqual(result["asset_count"], 3)
            one = Path(td) / "export-one"; two = Path(td) / "export-two"
            a = assets.export_bundles(f.root, f.index_path, one, "private")
            b = assets.export_bundles(f.root, f.index_path, two, "private")
            self.assertEqual(a["profiles"]["mother_bundle"]["manifest_sha256"], b["profiles"]["mother_bundle"]["manifest_sha256"])
            self.assertEqual(a["profiles"]["paper_support_bundle"]["manifest_sha256"], b["profiles"]["paper_support_bundle"]["manifest_sha256"])
            for profile in ("mother_bundle", "paper_support_bundle"):
                for name in ("RESEARCH_ASSET_INDEX.json", "CLAIM_PROVENANCE.json", "REFERENCES.bib", "THIRD_PARTY_NOTICES.md", "AI_CONTRIBUTION_DISCLOSURE.md", "REPRODUCE.md", "MANIFEST.json", "SHA256SUMS"):
                    self.assertTrue((one / profile / name).is_file())

    def assert_code(self, fixture: AssetFixture, code: str):
        fixture.rewrite()
        with self.assertRaises(assets.AssetError) as caught:
            assets.validate_project(fixture.root, fixture.index_path)
        self.assertEqual(caught.exception.code, code)

    def test_blocking_invariants(self):
        cases = []
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); f.registry["assets"][0]["local_artifacts"][0]["sha256"] = "0" * 64; self.assert_code(f, "asset_hash_mismatch")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); f.registry["assets"][0]["citation"]["bibtex"] = ""; self.assert_code(f, "citation_missing")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); f.registry["assets"][0]["license"]["status"] = None; self.assert_code(f, "license_status_missing")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); f.ledger["contributions"][0]["source_asset_ids"] = ["missing"]; self.assert_code(f, "unknown_parent_asset")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); c=f.ledger["contributions"][0]; c["origin"]="project_original"; c["relation"]="independent"; self.assert_code(f, "originality_conflict")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); f.registry["assets"][2]["usage"]["entrypoints"] = []; self.assert_code(f, "reproduction_entrypoint_missing")
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td)); extra=f.root/"code/unregistered.py"; extra.write_text("pass\n", encoding="utf-8"); self.assert_code(f, "unregistered_asset")

    def test_public_export_refused(self):
        with tempfile.TemporaryDirectory() as td:
            f = AssetFixture(Path(td))
            with self.assertRaises(assets.AssetError) as caught:
                assets.export_bundles(f.root, f.index_path, Path(td)/"public", "public")
            self.assertEqual(caught.exception.code, "public_export_requires_review")


if __name__ == "__main__":
    unittest.main()
