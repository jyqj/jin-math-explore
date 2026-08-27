# State machine v13

Read [transition schemas v13](transition-schemas-v13.md) for the exact public payload fields and authority class of every transition.

## Heads and gates

The project has one CAS head and two independently advancing referenced heads. Research authority contains promoted mathematical cognition; execution state contains work in progress. `review_required` is never a lifecycle state. It is a scoped gate with `scope`, `owner_lifecycle`, `blocked_transition`, dependency closure, release condition and evidence refs. A transition that intersects an open gate fails closed.

`semantic_review_receipt` is valid only when it resolves to a `math-research-map-review-closure/v1` accepted by [map semantic review v1](map-semantic-review-v1.md) for the exact candidate authority. Startup never trusts a PASS label or nonempty pointer. An incomplete idle project with a legacy or invalid receipt reports `map_review_upgrade_required` and cannot enter `WINDOW_PLAN`; an already active window may continue against its frozen source, but any later map publication needs a new closure. A completed project remains immutable.

## Window source

`window_source_binding` is a closed union:

- `validated_map`: objective commitment, map and validation-receipt pointers, frozen research-authority head hash, promoted-memory-index hash and route-review hash;
- `genesis_objective`: objective commitment, genesis-authority hash, eligibility-receipt pointer, `never_created_marker=true`, and a boolean consumption flag.

Genesis can be reserved only when the current authority proves that no map, route review, promoted memory or semantic-review receipt has ever existed. Planning requires `consumed=false`; successful activation persists the same binding with `consumed=true`. A migrated project, or any project with missing/stale/corrupt/invalid prior map bytes, must never use genesis. When idle, source binding is null and no future decision is prewritten.

## Prepare and atomic activation

`window_idle → window_planning` freezes source, budgets and a three-member differentiated route portfolio. Each attempt bundle is produced by `ATTEMPT_START_PREPARE` with a proposed never-before-used ID, route decision, ticket, cognition, selected rendering, capsule, budget and queue item. Prepare records are immutable but non-authoritative.

Only one `WINDOW_ACTIVATE` execution-head CAS makes all three attempts and queue items authoritative. It accepts exactly three distinct valid prepare hashes against the same expected heads/source/window. If preparation or validation of any member fails, activation writes nothing and attempt counters do not move. CAS failure permits only exact-hash idempotent retry; replanning uses new proposed IDs.

Planning blockage is explicit. `WINDOW_PLANNING_BLOCK` preserves the same source and zero counter movement; `WINDOW_PLANNING_RESUME` requires release evidence against that source. A source or authority change requires `WINDOW_PLANNING_SUPERSEDE`, an immutable closure record, retirement of all proposed IDs, and return to idle before maintenance/replanning. It is never an activation retry.

## Attempt execution and closing

`window_running` checkpoints update only local position, open local questions and last verified checkpoint. Objective, source, route, cognition, semantic fingerprint and evidence standard stay frozen. Any change enters `attempt_closing` through semantic reset.

Closing freezes outcome, candidate and complete dependencies before verification. Before that freeze, a deterministic finalizer creates an acyclic canonical package in fresh same-volume staging and a separate checker issues one `attempt_package_preflight_receipt` over the exact inventory, candidate, dependencies and artifact refs. The receipt is a mechanical byte-closure gate, not mathematical verification; a missing, stale or post-receipt-mutated package cannot close or enter the verifier queue. Mechanical remediation before freeze consumes no `LIMITED_REPAIR`. Verification is PASS, FAIL or INCONCLUSIVE on exact bytes. Source invalidation makes the package permanently promotion-ineligible. One verifier-directed repair is permitted only if proof object, mechanism family, quantifier strategy, route and evidence standard are unchanged; it creates a new finalized package, preflight receipt, candidate and verification hashes. A second repair or semantic change ends the attempt.

`ATTEMPT_END` advances only execution state, increments counters once and freezes one reconciliation package. It never promotes memory, changes route review, rebuilds map or advances research authority. Late verifier output for a closed attempt enters maintenance.

The public closing sequence is `ATTEMPT_CLOSE|SEMANTIC_RESET → VERIFICATION_QUEUE → VERIFICATION_RESULT → optional LIMITED_REPAIR → ATTEMPT_END`. Every payload is a closed schema. Queue and result bind the exact candidate, complete dependency hashes, verifier ticket and consumer principal. A repair is accepted only after bound FAIL, at most once, with identical source, portfolio, route decision, evidence standard and three-part semantic fingerprint. `ATTEMPT_END` requires the complete package fields named in the upgrade outline and cannot infer promotion eligibility without a bound PASS.

`QUEUED_PREFLIGHT_REBIND` is a one-time corrective compatibility edge, not part of the ordinary closing sequence. It is legal only for one `window_verifying` head containing exactly three unrepaired `verification_queued` attempts and exactly three old queue items whose closing artifact refs contain no preflight receipt. One closed payload must rebind all three attempts, preserve every frozen semantic field and both counter layers, bind the exact old candidate/dependency/ticket lineage, attach three fresh PASS-receipt artifact closures, clear all three stale verifier queue items and return the attempts to `closing`. Partial, repeated, receipt-bound, repaired, wrong-head or wrong-phase use fails closed. The next step is three fresh `VERIFICATION_QUEUE` transitions; the compatibility edge is neither mathematical verification nor `LIMITED_REPAIR`.

## Window reconciliation

Reconciliation begins only with three ready packages. It performs no new mathematics. It verifies dependency/source/verification hashes, quarantines ineligible claims, promotes eligible memory and standalone results, applies scoped route deltas, writes route review v2, builds and validates a closed map, then prepares a research-authority candidate manifest.

Before that authority candidate can publish, the exact map undergoes the bounded fresh-subagent review loop. The author and reviewer are distinct, each retry uses a new reviewer and ticket, and no more than three rounds may occur in one cycle. Repair or evidence augmentation changes the candidate/packet and invalidates prior review. `FAIL`, `INCONCLUSIVE`, subagent unavailability, or an invalid closure leaves the old research head current and routes through `WINDOW_RECONCILIATION_FAIL` with the existing scoped gate.

Conflict propagates at the smallest sound claim, route, or project scope. If resolution requires a new proof or computation, stop and leave the old research head current. On success publish research authority, then an execution closing head that clears window, queue, attempts, decisions, cognition, capsules and portfolio. The result is `window_idle` with a current activation-eligible map.

`WINDOW_RECONCILE` only stages a bound authority candidate and reconciliation receipt; it does not itself make that research head current. `WINDOW_RECONCILIATION_FAIL` advances execution only and records the owning scoped gate. `WINDOW_CLOSE` is the single both-head publication plan: it accepts the staged reconciliation binding, proves queue clear, names the candidate research head, and returns an idle or `completion_pending` execution head with every active pointer null. Research authority cannot advance on either failure path.

## Suspension, source integrity and maintenance

Suspension records a resumable execution head without changing frozen semantics. Resume proves identical objective/source/attempt bindings. Source review may confirm or invalidate a source. Invalidation closes promotion for every dependent package and opens maintenance/source-integrity reconciliation. Coverage failure preserves sound local results; soundness failure quarantines the affected authority. Maintenance may integrate late verification or source repair but cannot rewrite a closed window's history.

The persisted exception transitions are `SUSPEND`, `RESUME`, `SOURCE_REVIEW_START`, `SOURCE_REVIEW_CONFIRM`, `SOURCE_INVALIDATE`, `SOURCE_INTEGRITY_RECONCILE`, `MAINTENANCE_START`, `MAINTENANCE_RECONCILE`, and `MAINTENANCE_FAIL`. Loss of Goal/authority before a write is not one of them: derive `runtime_suspended_read_only` and write nothing. Source invalidation makes every dependent package effectively promotion-ineligible through an append-only invalidation relation; it never rewrites an already frozen package. Attempts not yet closed must produce explicit `source_invalidated=true`, `promotion_eligible=false` packages, and source-integrity close requires all three packages plus withdrawal/dependency-impact, semantic-review and queue-clear receipts. Maintenance starts only from idle or completion pending, performs no new mathematics or attempt creation, and a failed maintenance publication never advances research authority.

Every source-integrity or maintenance action that changes map bytes, the authority manifest, map inventory, protocol binding, structural receipt, or map receipt must obtain a new closure. It reuses `SOURCE_INTEGRITY_RECONCILE` or `MAINTENANCE_RECONCILE`; failure uses the existing maintenance/failure path and preserves the old research authority. This review is a gate inside the lifecycle, not a new lifecycle.

## Terminal audit and completion

From idle, freeze one immutable completion candidate and run three context-isolated audits: quantifier/coverage, strategy/soundness, and tool/reproducibility. Each must return PASS on the same candidate and dependencies. Failure preserves reliable partial results and returns through maintenance; soundness failure quarantines. Three PASS receipts permit the completion publication pair described in the persistence contract. The final mathematical head is immutable.

The public terminal sequence is `TERMINAL_AUDIT_START → three TERMINAL_AUDIT_RESULT → COMPLETION_PUBLISH`. Each result binds one distinct ticket and the same candidate. Non-PASS must classify impact as coverage or soundness: coverage clears only the completion candidate and returns idle, while soundness opens a project gate in maintenance. `COMPLETION_PUBLISH` is legal only after all three PASS receipts and an active local Goal gate; it returns candidate project bytes with `project_complete=true` and permanent `pending_goal_update=true`. After that CAS no state-machine transition is legal and no project acknowledgement or pending-clear write exists.
