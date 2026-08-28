"""Facade for jin-math-explore portfolio, knowledge, and core repository contracts.

This module composes the existing mathematical-state validators with the v2
classification, typed-dependency, knowledge-node, and result-feedback layer.
All checks remain mechanical and never establish mathematical truth.
"""
from __future__ import annotations

from pathlib import Path

import research_repo as core
from knowledge_graph import (
    catalog_payload,
    frontier_markdown,
    knowledge_nodes,
    public_knowledge_nodes,
    validate_knowledge_nodes,
)
from portfolio_registry import public_registry_entries, registry_entries, validate_registry
from portfolio_vocab import (
    CLASSIFICATION_STATUSES,
    FEEDBACK_EVENT_TYPES,
    FRONTIER_MOVEMENTS,
    GOAL_TYPES,
    KNOWLEDGE_AUTHORITY_STATUSES,
    KNOWLEDGE_ID,
    KNOWLEDGE_KINDS,
    KNOWLEDGE_RELATION_TYPES,
    MSC_CODE,
    PORTFOLIO_ROLES,
    PROBLEM_CLASSES,
    PROBLEM_ORIGINS,
    PROJECT_ID,
    SHA256,
    SHARED_ID,
    SLUG,
    TAG,
    Problem,
    default_classification,
    default_dependencies,
    default_result_feedback,
    validate_project_classification,
    validate_taxonomy,
)

canonical_json = core.canonical_json
pretty_json = core.pretty_json
sha256_bytes = core.sha256_bytes
sha256_file = core.sha256_file
validate_computation_handoff = core.validate_computation_handoff
validate_verification = core.validate_verification
validate_vendored_skills = core.validate_vendored_skills


def validate_repository(root: Path) -> list[Problem]:
    root = root.resolve()
    problems: list[Problem] = []
    problems.extend(core.validate_repository_metadata(root))
    required_extra = (
        "schemas/knowledge-node.schema.json",
        "taxonomy/facets.json",
        "knowledge/README.md",
    )
    for relative in required_extra:
        if not (root / relative).is_file():
            problems.append(
                Problem(
                    "portfolio_metadata_missing",
                    "required portfolio/knowledge contract is missing",
                    relative,
                )
            )
    problems.extend(validate_taxonomy(root))
    problems.extend(core.validate_skill_dependencies(root))
    problems.extend(core.validate_vendored_skills(root))

    registry_problems = validate_registry(root)
    problems.extend(registry_problems)
    if not any(item.code.startswith("registry_") for item in registry_problems):
        try:
            problems.extend(core.validate_shared_results(root))
        except ValueError as exc:
            problems.append(Problem("shared_result_registry_invalid", str(exc), "registry/shared-results"))
    try:
        problems.extend(validate_knowledge_nodes(root))
    except ValueError as exc:
        problems.append(Problem("knowledge_registry_invalid", str(exc), "knowledge/nodes"))

    projects = root / "projects"
    if projects.is_dir():
        for path in sorted(projects.glob("P-*/**/computation-handoff.json")):
            project_root = projects / path.relative_to(projects).parts[0]
            problems.extend(core.validate_computation_handoff(path, project_root))
        for path in sorted(projects.glob("P-*/**/jin-math-verification.json")):
            project_root = projects / path.relative_to(projects).parts[0]
            problems.extend(core.validate_verification(path, project_root))
    return sorted(problems, key=lambda item: (item.path, item.code, item.message))


__all__ = [
    "CLASSIFICATION_STATUSES",
    "FEEDBACK_EVENT_TYPES",
    "FRONTIER_MOVEMENTS",
    "GOAL_TYPES",
    "KNOWLEDGE_AUTHORITY_STATUSES",
    "KNOWLEDGE_ID",
    "KNOWLEDGE_KINDS",
    "KNOWLEDGE_RELATION_TYPES",
    "MSC_CODE",
    "PORTFOLIO_ROLES",
    "PROBLEM_CLASSES",
    "PROBLEM_ORIGINS",
    "PROJECT_ID",
    "SHA256",
    "SHARED_ID",
    "SLUG",
    "TAG",
    "Problem",
    "canonical_json",
    "catalog_payload",
    "default_classification",
    "default_dependencies",
    "default_result_feedback",
    "frontier_markdown",
    "knowledge_nodes",
    "pretty_json",
    "public_knowledge_nodes",
    "public_registry_entries",
    "registry_entries",
    "sha256_bytes",
    "sha256_file",
    "validate_computation_handoff",
    "validate_knowledge_nodes",
    "validate_project_classification",
    "validate_registry",
    "validate_repository",
    "validate_taxonomy",
    "validate_verification",
    "validate_vendored_skills",
]
