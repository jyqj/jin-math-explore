# Research assets, attribution, and private export

This protocol makes third-party and project-produced research material discoverable, callable, citable, attributable, and exportable without changing mathematical evidence grades. Registration is provenance control, not proof verification, Goal authority, a redistribution license, or a claim of originality.

## Fixed entry point

The fixed machine entry is one `math-research-asset-index/v1` JSON file:

```json
{
  "schema": "math-research-asset-index/v1",
  "project_id": "project-id",
  "authority": "authoritative",
  "asset_registry": {"path": "state/assets/registry.json", "sha256": "<sha256>"},
  "contribution_ledger": {"path": "state/assets/contributions.json", "sha256": "<sha256>"},
  "export_policy": {"path": "state/assets/export-policy.json", "sha256": "<sha256>"},
  "created_at_utc": "2026-08-13T00:00:00Z"
}
```

`authority` is `authoritative` only when the current versioned state points to the exact index. For v8 and earlier projects without an active Goal, use `auxiliary_non_authoritative` under `state/agent-query/`; do not change `project.json`, counters, evidence, or tickets. A later active Goal may bind that unchanged index through the version's non-counting checkpoint/publication operation.

## Asset registry

`math-research-asset-registry/v1` has exact keys `schema`, `project_id`, `registry_id`, `assets`, and `created_at_utc`. Every asset has exact keys:

- `asset_id`, `kind`, `title`, `origin`, and nonempty `creators`;
- `source`: `locator`, stable `identifier`, `version`, `upstream_commit`, and `acquired_at_utc`;
- `local_artifacts`: role plus project-relative path, raw SHA-256, and byte count;
- `license`: `status` (`spdx`, `custom`, or `unknown`), identifier, registered license artifact, and redistribution status;
- `citation`: whether required, citation key, human text, and BibTeX;
- `supported_claims`: only the statements this asset supports;
- `usage`: exact entrypoints, environment, and verification/test record;
- `limitations`; and
- `export`: separate booleans for `mother_bundle` and `paper_support_bundle`.

Kinds are `paper`, `code`, `data`, `computation`, `proof_attachment`, `software_environment`, or `source_record`. Origins are `external`, `user`, `ai_assisted`, `mixed`, `project`, or `unknown`. External assets require a locator, stable identifier, and acquisition date. Code and computation require a reproducible invocation and verification record.

Unknown license status is allowed only for private research. Record it as `unknown` with redistribution `unknown` or `private_only`; never infer public redistribution from availability, an arXiv page, a DOI, or a code download.

## Contribution ledger

`math-research-contribution-ledger/v1` has exact keys `schema`, `project_id`, `ledger_id`, `contributions`, and `created_at_utc`. Each contribution records one claim, algorithm, or code component; a precise statement; origin; relationship (`copied`, `adapted`, `reimplemented`, `reproved`, `independent`, or `unknown`); contributors and source asset IDs; exact artifact path/hash/symbol references; citation requirement; evidence grade; and limitations.

`project_original` is legal only with no upstream asset and relationship `independent`. Reimplementation from a paper is not an original algorithm. A project may independently derive an already known statement, but the ledger must preserve both the independent derivation record and the discovered external source; publication wording must not claim novelty without a separate novelty review.

Ticket inputs, continuity-capsule full artifacts, formal code dependencies, and paper claims that rely on research assets must resolve through the current index. An unregistered asset cannot be called project-original, cannot become a formal runtime dependency, and cannot enter an export.

## Export policy and commands

`math-research-export-policy/v1` binds scan roots, exclusions, and exactly two private profiles. Run:

```text
python -B scripts/math_research_assets.py scan --project PROJECT --index INDEX
python -B scripts/math_research_assets.py validate --project PROJECT --index INDEX
python -B scripts/math_research_assets.py export-plan --project PROJECT --index INDEX --output PLAN
python -B scripts/math_research_assets.py export --project PROJECT --index INDEX --output NEW_DIRECTORY
```

On Windows use `scripts/invoke_math_research_assets.ps1`. `scan` discovers likely papers, code, data, computations, licenses, and citation files beneath policy roots. `validate` fails closed on duplicate IDs/paths, bad hashes or sizes, missing source/citation/license status, unknown parents, originality conflicts, unregistered dependencies, missing code invocation/test records, and unregistered scanned assets.

`export-plan` is deterministic and writes no project state. `export` refuses an existing destination and any destination inside the project. It creates a private `mother_bundle` containing the canonical project archive plus registered assets, and a private `paper_support_bundle` containing only selected paper dependencies. Staging, caches, VCS metadata, credentials, and machine-temporary state are excluded.

Each bundle contains `RESEARCH_ASSET_INDEX.json`, `CLAIM_PROVENANCE.json`, `REFERENCES.bib`, `THIRD_PARTY_NOTICES.md`, `AI_CONTRIBUTION_DISCLOSURE.md`, `REPRODUCE.md`, `MANIFEST.json`, and `SHA256SUMS`. Both profiles are private. `--visibility public` fails closed: a public package requires a separate `$package-dev-projects` license, privacy, secrets, and redistribution review.

## State integration

New v10 state may contain optional `asset_index`, either null or an exact `{path,sha256}` pointer. Existing v10 state without the key remains valid. Before adding a new research asset, establish and validate the index, then publish `ASSET_REGISTRY_UPDATE` with exact payload:

```json
{
  "schema": "math-research-transition-payload/v10",
  "asset_index": {"path": "state/assets/index.json", "sha256": "<sha256>"},
  "occurred_at_utc": "2026-08-13T00:00:00Z"
}
```

This transition is allowed only for a nonterminal v10 run, updates only the pointer, generation, event/manifest, and timestamp, and consumes no attempt, audit, round, checkpoint, or evidence promotion. The exact index must validate and be manifest-bound. Old v10 projects remain readable until they add or formally depend on a research asset.

For a v8 or earlier live project, do not alter old schemas. With an active matching Goal, use `CHECKPOINT_COMMIT` to bind the validated index as a typed auxiliary reference under that version's existing rules. Without an active Goal, create only a clearly marked auxiliary index and human/query-guide pointers.

## Discovery and paper handoff

The root query guide must identify the current asset index before route selection or computation. A paper handoff reads the index, contribution ledger, cited source artifacts, claim-source map, tests, and limitations before drafting novelty, attribution, citation, software, data, or AI-disclosure text. Registration does not replace independent mathematical verification or a publication-specific citation check.
