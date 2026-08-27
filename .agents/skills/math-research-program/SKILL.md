---
name: math-research-program
description: Govern the multi-project jin-math-explore research portfolio without performing mathematics. Use when scheduling hard-problem projects, selecting the next closed research window, inspecting verification or computation debt, parking or reopening projects, or rebuilding the global frontier catalog.
---

# Math Research Program

## Role

Own operational coordination across many `$math-research-solve` v13 Projects. Never create, verify, promote, refute, or complete a mathematical claim.

## Startup

1. Read repository `PROGRAM_CHARTER.md` and all files under `program/` relevant to the operation.
2. Run `python scripts/validate_repository.py --root .`.
3. Load `registry/projects/*.json` and the generated catalog. Treat per-Project state as authority and catalog as projection.
4. Inspect only the Projects needed for the scheduling decision. Do not bulk-load proofs, raw objects, archives, or logs.

## Scheduling

Use evidence-backed operational factors:

- frontier clarity;
- decisive experiment availability;
- differentiated proof-object availability;
- verification debt;
- repeated failure mechanism;
- shared-result dependency impact;
- compute/review cost;
- last closed window information gain;
- source freshness.

Do not record model-estimated success probability. A new window must be selected from the Project's current research authority, never from a stale global catalog or prior chat.

## Actions

- `candidate → source_audit`: require a source-audit ticket.
- `source_audit → objective_freeze`: require a PASS receipt and complete six-field objective proposal.
- `objective_freeze → active`: delegate genesis to `$math-research-solve`; never handcraft a v13 head.
- schedule a window: fresh-read Project startup and ensure no active authoritative window.
- `active → parked`: record exact blocker and reopen condition without changing mathematical status.
- reopen: require evidence satisfying the recorded condition.
- terminal scheduling: require the Project's own completion candidate; Program status cannot create it.

## Output

Return proposed registry changes, selected Project/window operation, evidence for the choice, resource envelope, required Skill, and blocked dependencies. Mutate only after validation and user/Goal authority permit it. Rebuild catalog after registry changes.
