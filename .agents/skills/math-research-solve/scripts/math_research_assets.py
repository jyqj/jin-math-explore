#!/usr/bin/env python3
"""Register, validate, discover, and privately export Math Research assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ASSET_SUFFIXES = {
    ".pdf", ".py", ".ipynb", ".sage", ".wl", ".m", ".r", ".jl", ".c", ".cc",
    ".cpp", ".h", ".hpp", ".rs", ".go", ".java", ".js", ".ts", ".csv", ".tsv",
    ".parquet", ".feather", ".zip", ".tar", ".gz", ".jsonl", ".bib", ".cff",
}
SPECIAL_ASSET_NAMES = {"license", "license.md", "license.txt", "citation.cff", "requirements.txt"}
DEFAULT_EXCLUSIONS = {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "staging", "cache", "caches"}


class AssetError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise AssetError(code, message)


def _no_dupes(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        fail(key in out, "duplicate_json_key", f"Duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_dupes)
    except AssetError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AssetError("json_read_failed", f"Cannot read JSON {path}: {exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                h.update(chunk)
    except OSError as exc:
        raise AssetError("asset_unreadable", f"Cannot read asset {path}: {exc}") from exc
    return h.hexdigest()


def require_exact(value: Any, keys: tuple[str, ...], label: str) -> dict[str, Any]:
    fail(not isinstance(value, dict) or set(value) != set(keys), "schema_keys", f"{label} has missing or unexpected keys.")
    return value


def require_id(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not SAFE_ID.fullmatch(value), "schema_invalid", f"{label} is invalid.")
    return value


def require_hash(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not HEX64.fullmatch(value), "schema_invalid", f"{label} is not lowercase SHA-256.")
    return value


def safe_relative(value: Any, label: str) -> str:
    fail(not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value) is not None, "path_escape", f"{label} must be a project-relative POSIX path.")
    parts = Path(value).parts
    fail(any(part in ("", ".", "..") for part in parts), "path_escape", f"{label} escapes or is not canonical.")
    return Path(*parts).as_posix()


def resolve_under(root: Path, rel: str, label: str) -> Path:
    relative = safe_relative(rel, label)
    base = root.resolve()
    path = (base / relative).resolve()
    fail(path == base or base not in path.parents, "path_escape", f"{label} resolves outside the project.")
    return path


def validate_pointer(pointer: Any, root: Path, label: str) -> tuple[str, Path]:
    require_exact(pointer, ("path", "sha256"), label)
    rel = safe_relative(pointer["path"], f"{label} path")
    expected = require_hash(pointer["sha256"], f"{label} hash")
    path = resolve_under(root, rel, label)
    fail(not path.is_file(), "asset_missing", f"{label} is absent: {rel}")
    fail(sha_file(path) != expected, "asset_hash_mismatch", f"{label} hash differs: {rel}")
    return rel, path


def _validate_creators(creators: Any, label: str) -> None:
    fail(not isinstance(creators, list) or not creators, "creator_missing", f"{label} needs at least one creator.")
    for creator in creators:
        require_exact(creator, ("type", "name", "role"), f"{label} creator")
        fail(creator["type"] not in ("person", "organization", "user", "ai_system", "mixed"), "schema_invalid", f"{label} creator type is invalid.")
        fail(not all(isinstance(creator[k], str) and creator[k].strip() for k in ("name", "role")), "schema_invalid", f"{label} creator is incomplete.")


def validate_registry(value: Any, root: Path, project_id: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]], set[str]]:
    require_exact(value, ("schema", "project_id", "registry_id", "assets", "created_at_utc"), "asset registry")
    fail(value["schema"] != "math-research-asset-registry/v1" or value["project_id"] != project_id, "registry_invalid", "Asset registry schema or project binding is invalid.")
    require_id(value["registry_id"], "registry_id")
    fail(not isinstance(value["created_at_utc"], str) or not value["created_at_utc"], "schema_invalid", "Registry timestamp is missing.")
    fail(not isinstance(value["assets"], list), "schema_invalid", "assets must be an array.")
    assets: dict[str, dict[str, Any]] = {}
    registered_paths: set[str] = set()
    for asset in value["assets"]:
        require_exact(asset, ("asset_id", "kind", "title", "origin", "creators", "source", "local_artifacts", "license", "citation", "supported_claims", "usage", "limitations", "export"), "asset")
        aid = require_id(asset["asset_id"], "asset_id")
        fail(aid in assets, "duplicate_asset_id", f"Duplicate asset ID: {aid}")
        fail(asset["kind"] not in ("paper", "code", "data", "computation", "proof_attachment", "software_environment", "source_record"), "schema_invalid", f"Asset {aid} kind is invalid.")
        fail(asset["origin"] not in ("external", "user", "ai_assisted", "mixed", "project", "unknown"), "schema_invalid", f"Asset {aid} origin is invalid.")
        fail(not isinstance(asset["title"], str) or not asset["title"].strip(), "schema_invalid", f"Asset {aid} title is missing.")
        _validate_creators(asset["creators"], aid)
        source = require_exact(asset["source"], ("locator", "identifier", "version", "upstream_commit", "acquired_at_utc"), f"asset {aid} source")
        if asset["origin"] == "external":
            fail(not source["locator"] or not source["identifier"] or not source["acquired_at_utc"], "source_missing", f"External asset {aid} lacks locator, stable identifier, or acquisition date.")
        for key in source:
            fail(source[key] is not None and not isinstance(source[key], str), "schema_invalid", f"Asset {aid} source field {key} is invalid.")
        fail(not isinstance(asset["local_artifacts"], list) or not asset["local_artifacts"], "asset_missing", f"Asset {aid} has no local artifacts.")
        for artifact in asset["local_artifacts"]:
            require_exact(artifact, ("role", "path", "sha256", "bytes"), f"asset {aid} artifact")
            rel = safe_relative(artifact["path"], f"asset {aid} artifact path")
            require_hash(artifact["sha256"], f"asset {aid} artifact hash")
            fail(rel in registered_paths, "duplicate_asset_path", f"Artifact path is registered twice: {rel}")
            path = resolve_under(root, rel, f"asset {aid} artifact")
            fail(not path.is_file(), "asset_missing", f"Registered artifact is absent: {rel}")
            fail(type(artifact["bytes"]) is not int or artifact["bytes"] < 0 or path.stat().st_size != artifact["bytes"], "asset_size_mismatch", f"Registered byte size differs: {rel}")
            fail(sha_file(path) != artifact["sha256"], "asset_hash_mismatch", f"Registered hash differs: {rel}")
            registered_paths.add(rel)
        license_rec = require_exact(asset["license"], ("status", "identifier", "license_artifact", "redistribution"), f"asset {aid} license")
        fail(license_rec["status"] not in ("spdx", "custom", "unknown"), "license_status_missing", f"Asset {aid} license status is invalid.")
        fail(license_rec["redistribution"] not in ("public_allowed", "private_only", "unknown"), "license_status_missing", f"Asset {aid} redistribution status is invalid.")
        if license_rec["status"] in ("spdx", "custom"):
            fail(not isinstance(license_rec["identifier"], str) or not license_rec["identifier"].strip(), "license_status_missing", f"Asset {aid} license identifier is missing.")
        if license_rec["license_artifact"] is not None:
            lrel = safe_relative(license_rec["license_artifact"], f"asset {aid} license artifact")
            fail(lrel not in registered_paths, "license_artifact_unregistered", f"Asset {aid} license file is not a registered local artifact.")
        citation = require_exact(asset["citation"], ("required", "key", "text", "bibtex"), f"asset {aid} citation")
        fail(type(citation["required"]) is not bool, "schema_invalid", f"Asset {aid} citation.required is invalid.")
        if citation["required"]:
            fail(not all(isinstance(citation[k], str) and citation[k].strip() for k in ("key", "text", "bibtex")), "citation_missing", f"Asset {aid} requires a complete citation.")
        fail(not isinstance(asset["supported_claims"], list) or any(not isinstance(x, str) or not x.strip() for x in asset["supported_claims"]), "schema_invalid", f"Asset {aid} supported_claims is invalid.")
        usage = require_exact(asset["usage"], ("entrypoints", "environment", "verification"), f"asset {aid} usage")
        fail(not isinstance(usage["entrypoints"], list), "schema_invalid", f"Asset {aid} entrypoints is invalid.")
        if asset["kind"] in ("code", "computation"):
            fail(not usage["entrypoints"] or any(not isinstance(x, str) or not x.strip() for x in usage["entrypoints"]), "reproduction_entrypoint_missing", f"Asset {aid} lacks a reproducible invocation.")
            fail(not isinstance(usage["verification"], str) or not usage["verification"].strip(), "test_record_missing", f"Asset {aid} lacks a verification record.")
        fail(not isinstance(asset["limitations"], list) or any(not isinstance(x, str) or not x.strip() for x in asset["limitations"]), "schema_invalid", f"Asset {aid} limitations is invalid.")
        export = require_exact(asset["export"], ("mother_bundle", "paper_support_bundle"), f"asset {aid} export")
        fail(any(type(export[k]) is not bool for k in export), "schema_invalid", f"Asset {aid} export flags are invalid.")
        assets[aid] = asset
    return value, assets, registered_paths


def validate_ledger(value: Any, project_id: str, assets: dict[str, dict[str, Any]], registered_paths: set[str]) -> dict[str, Any]:
    require_exact(value, ("schema", "project_id", "ledger_id", "contributions", "created_at_utc"), "contribution ledger")
    fail(value["schema"] != "math-research-contribution-ledger/v1" or value["project_id"] != project_id, "ledger_invalid", "Contribution ledger schema or project binding is invalid.")
    require_id(value["ledger_id"], "ledger_id")
    fail(not isinstance(value["contributions"], list), "schema_invalid", "contributions must be an array.")
    seen: set[str] = set()
    for item in value["contributions"]:
        require_exact(item, ("contribution_id", "kind", "statement", "origin", "relation", "contributors", "source_asset_ids", "artifact_refs", "citation_required", "verification_grade", "limitations"), "contribution")
        cid = require_id(item["contribution_id"], "contribution_id")
        fail(cid in seen, "duplicate_contribution_id", f"Duplicate contribution ID: {cid}")
        seen.add(cid)
        fail(item["kind"] not in ("claim", "algorithm", "code_component"), "schema_invalid", f"Contribution {cid} kind is invalid.")
        fail(item["origin"] not in ("external", "user", "ai_generated_candidate", "ai_assisted", "mixed", "project_original"), "schema_invalid", f"Contribution {cid} origin is invalid.")
        fail(item["relation"] not in ("copied", "adapted", "reimplemented", "reproved", "independent", "unknown"), "schema_invalid", f"Contribution {cid} relation is invalid.")
        _validate_creators(item["contributors"], cid)
        fail(not isinstance(item["source_asset_ids"], list) or any(x not in assets for x in item["source_asset_ids"]), "unknown_parent_asset", f"Contribution {cid} references an unknown source asset.")
        if item["origin"] == "project_original":
            fail(bool(item["source_asset_ids"]) or item["relation"] != "independent", "originality_conflict", f"Contribution {cid} is labelled original but has an upstream relation.")
        if item["relation"] in ("copied", "adapted", "reimplemented", "reproved"):
            fail(not item["source_asset_ids"], "unknown_parent_asset", f"Derived contribution {cid} has no parent asset.")
        fail(type(item["citation_required"]) is not bool, "schema_invalid", f"Contribution {cid} citation flag is invalid.")
        if item["citation_required"]:
            fail(not item["source_asset_ids"] or any(not assets[x]["citation"]["required"] for x in item["source_asset_ids"]), "citation_missing", f"Contribution {cid} lacks a citable source asset.")
        fail(not isinstance(item["artifact_refs"], list) or not item["artifact_refs"], "artifact_reference_missing", f"Contribution {cid} lacks an artifact reference.")
        for ref in item["artifact_refs"]:
            require_exact(ref, ("path", "sha256", "symbol"), f"contribution {cid} artifact")
            rel = safe_relative(ref["path"], f"contribution {cid} artifact path")
            require_hash(ref["sha256"], f"contribution {cid} artifact hash")
            fail(rel not in registered_paths, "unregistered_dependency", f"Contribution {cid} uses an unregistered artifact: {rel}")
        fail(item["verification_grade"] not in ("source_claim", "verified_computation", "verified_partial", "proved", "heuristic", "candidate", "unknown"), "schema_invalid", f"Contribution {cid} verification grade is invalid.")
    return value


def validate_policy(value: Any, project_id: str) -> dict[str, Any]:
    require_exact(value, ("schema", "project_id", "default_visibility", "scan_roots", "scan_exclusions", "profiles", "created_at_utc"), "export policy")
    fail(value["schema"] != "math-research-export-policy/v1" or value["project_id"] != project_id, "policy_invalid", "Export policy schema or project binding is invalid.")
    fail(value["default_visibility"] != "private", "public_export_requires_review", "Math Research asset exports are private; use $package-dev-projects for public release review.")
    fail(not isinstance(value["scan_roots"], list) or not value["scan_roots"], "schema_invalid", "scan_roots must be nonempty.")
    for rel in value["scan_roots"]:
        safe_relative(rel, "scan root")
    fail(not isinstance(value["scan_exclusions"], list), "schema_invalid", "scan_exclusions must be an array.")
    profiles = require_exact(value["profiles"], ("mother_bundle", "paper_support_bundle"), "export profiles")
    for name, profile in profiles.items():
        require_exact(profile, ("visibility", "description"), f"profile {name}")
        fail(profile["visibility"] != "private", "public_export_requires_review", f"Profile {name} is not private.")
    return value


def load_index(project: Path, index_path: Path) -> dict[str, Any]:
    value = load_json(index_path)
    require_exact(value, ("schema", "project_id", "authority", "asset_registry", "contribution_ledger", "export_policy", "created_at_utc"), "asset index")
    fail(value["schema"] != "math-research-asset-index/v1", "index_invalid", "Asset index schema is invalid.")
    project_id = require_id(value["project_id"], "project_id")
    fail(value["authority"] not in ("authoritative", "auxiliary_non_authoritative"), "index_invalid", "Asset index authority is invalid.")
    _, registry_path = validate_pointer(value["asset_registry"], project, "asset registry pointer")
    _, ledger_path = validate_pointer(value["contribution_ledger"], project, "contribution ledger pointer")
    _, policy_path = validate_pointer(value["export_policy"], project, "export policy pointer")
    registry, assets, registered = validate_registry(load_json(registry_path), project, project_id)
    ledger = validate_ledger(load_json(ledger_path), project_id, assets, registered)
    policy = validate_policy(load_json(policy_path), project_id)
    return {"index": value, "registry": registry, "ledger": ledger, "policy": policy, "assets": assets, "registered_paths": registered}


def scan_candidates(project: Path, policy: dict[str, Any]) -> list[str]:
    exclusions = DEFAULT_EXCLUSIONS | {str(x).casefold() for x in policy["scan_exclusions"]}
    found: set[str] = set()
    for root_rel in policy["scan_roots"]:
        root = resolve_under(project, root_rel, "scan root")
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(project).as_posix()
            parts = {part.casefold() for part in Path(rel).parts}
            if parts & exclusions or path.suffix.casefold() == ".pyc":
                continue
            if path.suffix.casefold() in ASSET_SUFFIXES or path.name.casefold() in SPECIAL_ASSET_NAMES:
                found.add(rel)
    return sorted(found)


def validate_project(project: Path, index_path: Path, require_clean_scan: bool = True) -> dict[str, Any]:
    loaded = load_index(project, index_path)
    candidates = scan_candidates(project, loaded["policy"])
    unregistered = sorted(set(candidates) - loaded["registered_paths"])
    fail(require_clean_scan and bool(unregistered), "unregistered_asset", f"Unregistered research assets exist: {unregistered[:5]}")
    return {
        "classification": "asset_index_valid",
        "project_id": loaded["index"]["project_id"],
        "authority": loaded["index"]["authority"],
        "asset_count": len(loaded["assets"]),
        "contribution_count": len(loaded["ledger"]["contributions"]),
        "candidate_count": len(candidates),
        "unregistered": unregistered,
    }


def export_plan(project: Path, index_path: Path) -> dict[str, Any]:
    loaded = load_index(project, index_path)
    candidates = scan_candidates(project, loaded["policy"])
    unregistered = sorted(set(candidates) - loaded["registered_paths"])
    fail(bool(unregistered), "unregistered_asset", f"Export blocked by unregistered assets: {unregistered[:5]}")
    profiles: dict[str, Any] = {}
    for profile, flag in (("mother_bundle", "mother_bundle"), ("paper_support_bundle", "paper_support_bundle")):
        assets = sorted(aid for aid, item in loaded["assets"].items() if item["export"][flag])
        artifact_paths = sorted({a["path"] for aid in assets for a in loaded["assets"][aid]["local_artifacts"]})
        profiles[profile] = {"visibility": "private", "asset_ids": assets, "artifact_paths": artifact_paths}
    excluded = ["staging", "caches", "VCS metadata", "credentials", "machine-temporary state"]
    return {"schema": "math-research-export-plan/v1", "project_id": loaded["index"]["project_id"], "index_sha256": sha_file(index_path), "profiles": profiles, "excluded_classes": excluded}


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)


def _copy(path: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with path.open("rb") as source, target.open("xb") as dest:
        shutil.copyfileobj(source, dest)


def _bundle_metadata(loaded: dict[str, Any], plan: dict[str, Any], profile: str) -> dict[str, bytes]:
    asset_ids = set(plan["profiles"][profile]["asset_ids"])
    assets = [a for a in loaded["registry"]["assets"] if a["asset_id"] in asset_ids]
    contributions = [c for c in loaded["ledger"]["contributions"] if set(c["source_asset_ids"]) <= asset_ids]
    bib = "\n\n".join(a["citation"]["bibtex"].strip() for a in assets if a["citation"]["required"]) + "\n"
    notices = ["# Third-party notices", ""]
    for a in assets:
        notices.append(f"- {a['title']} ({a['asset_id']}): {a['license']['identifier'] or 'unknown'}; redistribution={a['license']['redistribution']}.")
    ai = ["# AI contribution disclosure", ""]
    for c in contributions:
        if c["origin"] in ("ai_generated_candidate", "ai_assisted", "mixed"):
            ai.append(f"- {c['contribution_id']}: {c['origin']}; relation={c['relation']}. {c['statement']}")
    reproduce = ["# Reproduce", "", "This is a private research export. Run only in a reviewed local environment.", ""]
    for a in assets:
        for command in a["usage"]["entrypoints"]:
            reproduce.append(f"- `{command}`")
    asset_index = {"schema": "math-research-export-asset-index/v1", "project_id": loaded["index"]["project_id"], "profile": profile, "visibility": "private", "assets": assets}
    provenance = {"schema": "math-research-export-claim-provenance/v1", "project_id": loaded["index"]["project_id"], "contributions": contributions}
    return {
        "RESEARCH_ASSET_INDEX.json": canonical_bytes(asset_index),
        "CLAIM_PROVENANCE.json": canonical_bytes(provenance),
        "REFERENCES.bib": bib.encode("utf-8"),
        "THIRD_PARTY_NOTICES.md": ("\n".join(notices) + "\n").encode("utf-8"),
        "AI_CONTRIBUTION_DISCLOSURE.md": ("\n".join(ai) + "\n").encode("utf-8"),
        "REPRODUCE.md": ("\n".join(reproduce) + "\n").encode("utf-8"),
    }


def export_bundles(project: Path, index_path: Path, output: Path, visibility: str) -> dict[str, Any]:
    fail(visibility != "private", "public_export_requires_review", "Public export requires a separate $package-dev-projects license/privacy/redistribution review.")
    project = project.resolve()
    output = output.resolve()
    fail(output == project or project in output.parents, "output_inside_project", "Export output must be outside the research project.")
    fail(output.exists(), "output_exists", "Export output already exists; deterministic export never overwrites.")
    loaded = load_index(project, index_path)
    plan = export_plan(project, index_path)
    output.mkdir(parents=True)
    results: dict[str, Any] = {}
    for profile in ("mother_bundle", "paper_support_bundle"):
        root = output / profile
        root.mkdir()
        if profile == "mother_bundle":
            excluded = DEFAULT_EXCLUSIONS
            for path in project.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(project).as_posix()
                if {p.casefold() for p in Path(rel).parts} & excluded or path.suffix.casefold() == ".pyc":
                    continue
                _copy(path, root / "project" / rel)
        else:
            for aid in plan["profiles"][profile]["asset_ids"]:
                for artifact in loaded["assets"][aid]["local_artifacts"]:
                    _copy(resolve_under(project, artifact["path"], "export artifact"), root / "artifacts" / aid / artifact["path"])
        for name, data in _bundle_metadata(loaded, plan, profile).items():
            _write(root / name, data)
        files = sorted(p for p in root.rglob("*") if p.is_file())
        manifest_entries = [{"path": p.relative_to(root).as_posix(), "sha256": sha_file(p), "bytes": p.stat().st_size} for p in files]
        manifest = {"schema": "math-research-private-export-manifest/v1", "project_id": loaded["index"]["project_id"], "profile": profile, "visibility": "private", "source_index_sha256": sha_file(index_path), "entries": manifest_entries}
        _write(root / "MANIFEST.json", canonical_bytes(manifest))
        sums = "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in manifest_entries) + f"{sha_file(root / 'MANIFEST.json')}  MANIFEST.json\n"
        _write(root / "SHA256SUMS", sums.encode("utf-8"))
        results[profile] = {"path": str(root), "manifest_sha256": sha_file(root / "MANIFEST.json"), "file_count": len(manifest_entries) + 2}
    return {"classification": "private_exports_created", "project_id": loaded["index"]["project_id"], "profiles": results}


def emit(data: dict[str, Any]) -> int:
    print(json.dumps({"ok": True, "data": data, "warnings": []}, ensure_ascii=False, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("scan", "validate", "export-plan"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--project", required=True)
        cmd.add_argument("--index", required=True)
        if name == "validate":
            cmd.add_argument("--allow-unregistered", action="store_true")
        if name == "export-plan":
            cmd.add_argument("--output")
    exp = sub.add_parser("export")
    exp.add_argument("--project", required=True)
    exp.add_argument("--index", required=True)
    exp.add_argument("--output", required=True)
    exp.add_argument("--visibility", choices=("private", "public"), default="private")
    return p


def main() -> int:
    args = parser().parse_args()
    project = Path(args.project).resolve()
    index = Path(args.index).resolve()
    try:
        if args.command == "scan":
            loaded = load_index(project, index)
            candidates = scan_candidates(project, loaded["policy"])
            return emit({"classification": "asset_scan", "registered": sorted(loaded["registered_paths"]), "candidates": candidates, "unregistered": sorted(set(candidates) - loaded["registered_paths"])})
        if args.command == "validate":
            return emit(validate_project(project, index, not args.allow_unregistered))
        if args.command == "export-plan":
            value = export_plan(project, index)
            if args.output:
                out = Path(args.output)
                fail(out.exists(), "output_exists", "Export plan output already exists.")
                _write(out, canonical_bytes(value))
            return emit(value)
        return emit(export_bundles(project, index, Path(args.output), args.visibility))
    except AssetError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": "Preserve bytes, repair the stated registry invariant, and validate again."}}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
