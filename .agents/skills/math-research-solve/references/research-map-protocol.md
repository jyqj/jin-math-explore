# Pre-standardization research-map prototype v3 (read-only)

This document and its old `40-当前候选路线与下一步.md` layout are frozen solely for unmigrated-project diagnosis and byte-preserving recovery. They are not an activation contract. New or migrated v13 projects must use official `math-research-map/v1`, `references/research-map-protocol-v1.md`, and `40-路线景观与重排条件.md`; no active v13 workflow may copy the future-command semantics below.

## Contract

A project research map is the bounded reading layer shared by humans and AI. It must recover the project's exact objective, established milestones, attempted routes, evidence boundaries, current candidates, and next decision gates without loading the entire project. It is never the authority for project state or raw evidence.

The visible map tree contains Markdown only. Code, datasets, JSON results, solver/verifier reports, logs, certificates, and project-control records remain in the authoritative research project. Ordinary reading follows Markdown links. Byte-level audit follows an asset ID into the project object store only when necessary.

The invariant is evidence before prose. A map author may explain only what cited project memory, project records, or frozen objects support. A route name cannot carry explanatory work. General mathematical knowledge may clarify notation, but it must not turn an undeveloped suggestion into project history.

## Layout and responsibilities

```text
<map-root>/
  00-研究地图契约.md
  01-主研究地图.md
  02-阅读说明与证据规则.md
  ... route, milestone, experiment, and bridge notes ...
  40-当前候选路线与下一步.md
  90-资产索引.md
  .research/
    research-map.json
    asset-references.json
    validation-receipt.json
```

Every visible file is a nonempty registered Markdown note. `.research/` contains exactly the three control files above. A normal v3 map contains no raw asset file, no asset copy, and no Markdown wrapper whose only purpose is to make a non-Markdown file look readable. A `full-private` export is a separate product and may restore raw assets into its own portable package.

`research-map.json` is the machine control plane. It binds the map to the project ID, objective hash, and exact `project.json` head; registers every control note and node; records node hashes, stable node IDs, route state, relevant memory IDs, project-record references, evidence hashes, and `required_asset_ids`.

`asset-references.json` is also the evidence ledger. For every `asset:<id>` it records an exact display filename, role, source locator, object SHA-256, size, and dependent node IDs. It also enumerates every `memory:<id>` and project record used by nodes. It never contains a map-local raw asset path.

`validation-receipt.json` records the structural result and semantic-audit status. A structurally valid map may remain `review_required`; only an independent mathematical-fidelity audit may promote it to `current`.

## Node writing rule

Each node begins with a short conclusion and enough local context for a first-time reader. It then supplies the complete mathematical derivation available from the project, or states the exact boundary where the project stops. Important results must say what was proved, how it was derived, which parts were computer-assisted, which quantifiers were covered, which files reproduce the claim, and what the claim cannot imply. Exact raw filenames appear as inline code and are not clickable.

Each route node has five explicit entry fields:

- the mathematical object from which the route starts;
- the mechanism connecting that object to the immutable objective;
- the evidence already obtained and its exact scope;
- the missing lemma, computation, certificate, or construction;
- the next success/failure test.

The same five fields appear in `route_entry.fields` as `mathematical_object`, `objective_mechanism`, `evidence_boundary`, `missing_work`, and `success_failure_gate`. Each field has `asset_status`, nonempty `source_refs`, and `gap`. `supported` is allowed only when its sources support the statement. `missing_from_assets` requires a concrete nonempty gap and prose that admits the missing evidence.

Valid source references are `asset:<id>`, `memory:<id>`, `project:<relative-record-path>`, and `evidence:<sha256>`. References must be declared by the same node. A route review that records only a route name supports only the fact that the route was proposed; it does not support a guessed matrix, kernel, recurrence, estimate, or decision threshold.

## Link rule

Every internal wikilink, Markdown link, or embed must resolve unambiguously to a directly readable Markdown note. Local links to non-Markdown files are forbidden. Missing targets, duplicate-stem ambiguity, blank notes, unregistered notes, and thin asset-wrapper notes are hard failures. External web citations are allowed.

Markdown mentions raw materials as purpose plus exact filename, for example: “Independent verifier output (file: `verification.json`)”. It must not use a wikilink or clickable local path for that file. Auditors resolve its asset ID from the hidden ledger and restore the object from `.research/objects/sha256/<prefix>/<sha256>` in the project.

## Creation and update closure

Map construction and maintenance always use this order:

```text
authoritative project Startup
→ evidence inventory
→ evidence-ledger preflight
→ affected node prose and complete mathematics
→ asset index and next-route ranking
→ main map
→ hidden machine controls
→ structural, formula, link, object, and binding validation
→ independent semantic audit
→ publish only if every required gate passes
```

Inventory project memory, evidence records, imported-tree manifests, object hashes, and route review before writing prose. Reuse existing project objects. If a needed raw file is not yet a project object, ingest it with provenance and rebuild the project archive manifest before referring to it. Project memory records use `memory:<id>` and do not masquerade as raw assets.

For a local checkpoint, update only the affected evidence, memory, nodes, indices, and controls. Do not regenerate unrelated mathematics. Write immutable project evidence first; write map Markdown next; replace `asset-references.json`, then `validation-receipt.json`, and replace `research-map.json` last under an expected-head check.

If the project head changes, the map is stale until rebound and revalidated. If a semantic mapping is not mechanical, leave the map `review_required`. Never auto-promote merely to finish a migration.

## v2 to v3 migration

v2 remains historical and read-only. A v2→v3 migration builds a new external stage and never changes v2 semantics in place.

Verify the v2 map and source project first. Inventory every v2 map asset. Reuse content already present in the project object store; convert copied memory records to `memory:<id>`; convert project-control snapshots to project-record references; ingest any remaining process material into the project object store with provenance. Copy only registered Markdown to the v3 stage, rewrite node bindings to `required_asset_ids`, generate the hidden ledger and controls, validate the stage, and run an independent semantic audit. Install with a logged same-volume atomic exchange and retain the old map root under a plan-hash recovery directory.

## Required validation

Run:

```text
python scripts/validate_research_map.py <map-root> --project-root <project-root>
```

The v3 validator fails closed on:

- any map-local raw asset or unexpected hidden file;
- a local link or embed to a non-Markdown target;
- blank, unregistered, missing, ambiguous, or asset-wrapper Markdown;
- an asset ID, memory ID, project record, object hash, or declared size that cannot be resolved in the authoritative project;
- project ID, objective hash, source head, map ID, note hash, or ledger mismatch;
- a route missing any of the five context fields or containing an unresolved evidence reference;
- a route field labelled supported without a resolvable source, or a missing field without an explicit gap.

After this validator passes, validate every formula and wikilink through `$obsidian-vault-notes`, check project Full Startup and object restoration, then run an independent semantic audit. The semantic auditor compares each mathematical explanation with the cited source bytes and project memory. It specifically rejects strengthened quantifiers, invented derivations, and route explanations supplied from model knowledge rather than research assets.

No failed gate may be ignored. Structural success does not imply mathematical correctness, and a map whose semantic audit is pending stays `review_required`.
