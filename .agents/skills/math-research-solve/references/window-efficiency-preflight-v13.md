# v13 window efficiency and authoring preflight

This reference prevents avoidable authoring and reconciliation rework. It does not weaken mathematical verification, change a project schema, or turn a bounded negative result into a workflow error.

## Phase-gated materialization

Generic builders and schema helpers may be prepared early, but do not freeze live-bound plans, tickets, packets, manifests, heads, counters, or provenance hashes until their owning lifecycle is current. A `WINDOW_PLAN` is materialized only from a fresh `window_idle` head and a valid current map-review closure. Reconciliation and close artifacts are materialized only after all three exact packages reach their required state. Never build the next window inside the previous window's reconciliation or close.

Separate semantic authoring provenance from audit/packaging implementation provenance. A checker-only change must not change the candidate map packet or invalidate a semantic review unless its validated bytes or semantic inputs changed.

## Cheapest decisive gates first

Before expensive symbolic work or corpus expansion, audit whether the frozen source closure actually defines every datum needed by the route:

- exact object and normalization;
- domain and quantifier order;
- contour/path, orientation, branch value, and continuation when analytic data matters;
- initial values or a source-derived reconstruction rule;
- output indexing and comparison convention;
- a non-circular route from the bound source bytes to the proposed proof object.

Locator hints are not bound source objects. If a required definition is absent after an exhaustive bounded source audit, close with the precise `no_candidate`, `inconclusive`, or source-sufficiency boundary; do not spend the remaining budget reconstructing answer rows or treating the absence as a mathematical refutation.

## First-checkpoint package readiness

At the first material checkpoint, not only at solver completion:

1. Resolve and validate the worker output root with `window_authoring_preflight_v13.py output-scope`; it must be a proper task-workspace descendant and outside the live project.
2. Validate the exact closed outcome/result-proposal shape, including map role and nonempty `cannot_imply`/reopen boundaries where required.
3. Run the attempt finalizer/checker on a small representative package before producing large ledgers. Keep binary or CR-bearing evidence behind a documented text-safe wrapper when the frozen package contract requires LF-only files.
4. Preserve raw solver output; regenerate a fresh finalized package after any schema or byte repair.

## Standalone proof self-containment

Before proposing `standalone_result`, perform a cold proof audit using only the visible result page. It must define all quantified variables and domains, avoid symbol reuse, freeze paths/orientations/branches, state the exact operator or recurrence and reconstruction rule, prove degree or finite-check bounds, connect normalization to the claimed invariant, exclude oracle/circular definitions, and close with exact scope and `cannot_imply`. Delegating a constitutive proof step to project history is not self-contained.

## Map-wide reconciliation preflight

Before dispatching a map reviewer:

- regenerate counts, generations, current authority/review pointers, result roles, and route states from the candidate head rather than copying prose from the prior map;
- scan every visible page for claims contradicted by newly promoted results, including route pages not directly edited by the attempt;
- validate every standalone page before placing it in the map control;
- normalize parameter and result evidence references to the authority schemes accepted by the map protocol; attempt-local and packaging-only locators remain artifact metadata, not map authority references;
- run structural publication and result-export validation before preparing the semantic packet.

The protocol field `packet_sha256` is the canonical document digest: recursively key-sorted compact UTF-8 JSON plus one final LF. It is not necessarily the packet file's raw-byte digest. Run:

```powershell
python -B scripts/window_authoring_preflight_v13.py review-digests --packet <packet.json> --ticket <ticket.json>
```

The receipt names `packet_document_sha256` and `packet_raw_sha256` separately so reviewers do not report a raw/document distinction as a binding failure.

## Artifact classes and finalize-last

Apply size limits by artifact class. A semantic-review closure legitimately embeds one to three complete rounds and may exceed the ordinary single-artifact budget; the complete authoring tree still has its own aggregate cap. Use project-specific tighter limits when the frozen budget requires them. The preflight defaults are 512,000 bytes for ordinary files, 2 MiB for a map-review closure, and 8 MiB for the whole authoring tree:

```powershell
python -B scripts/window_authoring_preflight_v13.py authoring-tree --root <candidate-tree>
```

Set any `finalized` marker only after the exact candidate, closure, payloads, manifests, planner receipts, and whole-tree audit pass. A partial directory or failed audit is resumable staging, never a finalized authority candidate.

## WINDOW_CLOSE overlay separation

The pure planner and the atomic commit consume different manifests:

- the planning overlay contains only actually changed visible Markdown aliases needed to validate the candidate project while the old research authority is still current;
- the formal commit manifest contains those identical Markdown rows plus the map control, receipt, asset ledger, and every other publication alias required by the new authority.

Passing the full commit manifest into planning can make the old authority validate against new control bytes and fail before the new authority is eligible. Check the separation with:

```powershell
python -B scripts/window_authoring_preflight_v13.py window-close-manifests --planning-manifest <planning.json> --commit-manifest <commit.json>
```

## Diagnostics and progress reporting

Wrappers must preserve a failed child process's exit code and compact stdout/stderr category. Do not replace the first actionable planner error with a generic `CalledProcessError`.

For long windows, report remaining gates rather than a vague percentage: solver/package, independent verification, attempt end, reconciliation/map review, and window close. Once the mathematics is complete, distinguish semantic review rounds from deterministic commit work and update the estimate when a review creates a new repair round.
