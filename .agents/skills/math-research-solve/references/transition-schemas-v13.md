# Transition schemas v13

This reference is the human index for the closed payloads enforced by `scripts/math_research_state_v13.py`. The Python validator is the byte-level machine definition. Every payload has `schema` plus exactly the fields listed here; unknown or missing fields fail closed. Every authoritative prepare also requires `goal_state=active` as a local gate, which never substitutes for the Host's fresh `get_goal`.

The public `prepare` CLI requires `--output`. Full candidate bytes go only to that local plan file; stdout contains status, transition, authority, generations and hashes, never raw candidate objects, archives, logs, cognition bodies or evidence bodies.

| Transition | Payload schema | Exact non-schema fields | Authority |
| --- | --- | --- | --- |
| `WINDOW_PLAN` | `math-research-window-plan/v13` | `window_id, planning_owner, source_binding, route_portfolio, proposed_attempt_ids, counter_snapshot, budget_reservation` | execution |
| `WINDOW_PLANNING_BLOCK` | `math-research-window-planning-block/v13` | `reason, missing_regions, reopen_condition, source_binding_sha256` | execution |
| `WINDOW_PLANNING_RESUME` | `math-research-window-planning-resume/v13` | `source_binding_sha256, release_evidence_refs` | execution |
| `WINDOW_PLANNING_SUPERSEDE` | `math-research-window-planning-supersede/v13` | `reason, superseded_proposed_attempt_ids, zero_attempts_committed, planning_closure` | execution |
| `ATTEMPT_START_PREPARE` | `math-research-attempt-start-prepare/v13` | `project_id, window_id, proposed_attempt_id, portfolio_member_id, objective_commitment_sha256, source_binding_sha256, portfolio_sha256, route_decision, ticket, cognition, selected_rendering, route_card, route_card_contract, capsule, capsule_contract, budget, queue_item, queue_item_contract, access_check, input_check, staging_check` | none |
| `WINDOW_ACTIVATE` | `math-research-window-activate/v13` | `prepare_records, activation_receipt` | execution |
| `CHECKPOINT` | `math-research-checkpoint/v13` | `attempt_id, frozen_bindings, prior_capsule_sha256, successor_capsule, successor_capsule_contract, last_verified_checkpoint` | execution |
| `ATTEMPT_CLOSE` / `SEMANTIC_RESET` | `math-research-attempt-closing/v13` | `attempt_id, closing_reason, outcome, candidate, dependencies, artifact_refs, evidence_refs, final_capsule, budget_usage, semantic_reset_directive, cannot_imply, reopen_conditions` | execution |
| `QUEUED_PREFLIGHT_REBIND` | `math-research-queued-preflight-rebind/v13` | `window_id, expected_execution_head_sha256, compatibility_reason, rebinds` | execution |
| `VERIFICATION_QUEUE` | `math-research-verification-queue/v13` | `attempt_id, verifier_ticket, candidate_sha256, dependency_sha256s, independence_mode, consumer_principal` | execution |
| `VERIFICATION_RESULT` | `math-research-verification-result/v13` | `attempt_id, verifier_ticket_sha256, candidate_sha256, dependency_sha256s, verdict, checked_scope, earliest_error, unresolved, context_isolated` | execution |
| `LIMITED_REPAIR` | `math-research-limited-repair/v13` | `attempt_id, repair_ticket, old_candidate_sha256, new_candidate, new_dependencies, new_artifact_refs, frozen_semantics` | execution |
| `ATTEMPT_END` | `math-research-attempt-end/v13` | `attempt_id, package, close_receipt` | execution |
| `WINDOW_RECONCILE` | `math-research-window-reconciliation/v13` | `package_sha256s, new_math_performed, conflict_set, candidate_research_authority_head, candidate_manifest, map_validation_receipt, semantic_review_receipt, reconciliation_receipt` | execution staging only |
| `WINDOW_RECONCILIATION_FAIL` | `math-research-window-reconciliation-failure/v13` | `package_sha256s, new_math_required, failure_receipt, review_gate` | execution |
| `WINDOW_CLOSE` | `math-research-window-close/v13` | `reconciliation_receipt_sha256, candidate_research_authority_head, candidate_execution_state_head, queue_clear_proof, terminal_candidate` | both |
| `SUSPEND` | `math-research-window-suspend/v13` | `resume_capsule, frozen_state_sha256, reason` | execution |
| `RESUME` | `math-research-window-resume/v13` | `resume_capsule_sha256, integrity_check, frozen_bindings_unchanged` | execution |
| `SOURCE_REVIEW_START` | `math-research-source-review-start/v13` | `source_binding_sha256, review_ticket, review_gate` | execution |
| `SOURCE_REVIEW_CONFIRM` | `math-research-source-review-confirm/v13` | `review_receipt, source_binding_sha256, gate_release_evidence_refs` | execution |
| `SOURCE_INVALIDATE` | `math-research-source-invalidation/v13` | `review_receipt, source_binding_sha256, dependency_closure, invalidation_id` | execution |
| `SOURCE_INTEGRITY_RECONCILE` | `math-research-source-integrity-reconciliation/v13` | `new_math_performed, candidate_research_authority_head, candidate_execution_state_head, withdrawals, dependency_impact, queue_clear_proof, semantic_review_receipt, close_receipt` | both |
| `MAINTENANCE_START` | `math-research-maintenance-start/v13` | `input_records, reason, origin_phase, new_math_performed` | execution |
| `MAINTENANCE_RECONCILE` / `MAINTENANCE_FAIL` | `math-research-maintenance-reconciliation/v13` | `new_math_performed, candidate_research_authority_head, candidate_execution_state_head, promotion_or_withdrawal, dependency_impact, semantic_review_receipt, maintenance_receipt, next_phase, review_gate` | both on success; execution on failure |
| `TERMINAL_AUDIT_START` | `math-research-terminal-audit-start/v13` | `completion_candidate_sha256, audit_tickets, context_isolation` | execution |
| `TERMINAL_AUDIT_RESULT` | `math-research-terminal-audit-result/v13` | `audit_kind, ticket_sha256, completion_candidate_sha256, verdict, receipt, impact_classification, new_math_performed` | execution |
| `COMPLETION_PUBLISH` | `math-research-completion-publication/v13` | `completion_candidate_sha256, terminal_summary, completion_plan, candidate_research_authority_head, candidate_execution_state_head` | both, terminal |

## Embedded closed objects

- Every `semantic_review_receipt` field is a pointer to `math-research-map-review-closure/v1`, never an arbitrary JSON result or PASS label. The closure contains one to three ordered rounds of `math-research-map-review-packet/v1`, `math-research-map-review-ticket/v1`, and `math-research-map-review-result/v1`; it binds the final exact candidate, complete authority and visible-tree inventories, candidate authority manifest, protocol and structural receipt, unique fresh-subagent reviewers distinct from the author, repair lineage, all eight synthesis checks, complete coverage, and final PASS with empty repairs/unresolved. See [map semantic review v1](map-semantic-review-v1.md).
- A map-authority transition with a changed map or map receipt cannot be prepared from a legacy thin receipt. The matching failure transition carries the existing scoped `review_gate`; no review artifact creates a new lifecycle state or advances research authority on failure.

- `route_portfolio` has exactly three members with distinct `(proof_object, mechanism_family, quantifier_strategy)` fingerprints. A discovery member is a normal counted member and carries the same bounded question, outputs, stop rule, failure boundary, and budget obligations.
- A prepare embeds hash-bound route-card, continuity-capsule, and queue-item contracts. The pointers must hash to their canonical contract bytes. All three prepares bind one source, portfolio, window and counter snapshot.
- `ATTEMPT_CLOSE`/`SEMANTIC_RESET` `artifact_refs`, and `LIMITED_REPAIR.new_artifact_refs`, contain exactly one pointer ending in `attempt-package-preflight.json`. The commit Harness must validate its `math-research-attempt-package-preflight/v1` bytes against the complete immutable package tree and the closing candidate/dependencies before the transition can commit. `ATTEMPT_END` preserves the same bound artifact refs. This is not a new lifecycle transition.
- `QUEUED_PREFLIGHT_REBIND.rebinds` has exactly three rows, one for each current attempt, and each row has exactly `attempt_id, old_candidate_sha256, old_dependency_sha256s, old_verifier_ticket_sha256, new_candidate, new_dependencies, new_artifact_refs, frozen_semantics`. It accepts only an all-legacy three-item verifier queue with no existing preflight receipt, requires reason `v13-attempt-package-preflight-backfill`, binds the current execution-head hash, preserves counters and repair counts, and clears the old verifier queue atomically. Every `new_artifact_refs` list contains exactly one fresh preflight receipt. It cannot be used partially or twice.
- The activation receipt binds expected project/execution heads, source, portfolio, ordered prepare hashes, counters before/after, and a non-circular candidate-execution manifest hash.
- A reconciliation package contains attempt/window/source/member/decision identity, outcome, artifacts, evidence, verification, final capsule, route delta, result proposals, obstacles, `cannot_imply`, reopen conditions, budget use, semantic-reset directive, source-invalidated status, and promotion eligibility.
- A scoped review gate has exactly `scope, owner_lifecycle, blocked_transition, dependency_closure, release_condition, evidence_refs`; only transitions intersecting its blocked set are stopped, and release must return to its owner lifecycle.

## Publication boundary

An authority=`both` plan returns the candidate execution bytes, candidate research pointer and complete candidate `project.json`. The execution pointer SHA must equal the canonical candidate execution bytes. The commit plan separately binds expected project, execution and research heads, a complete staging inventory hash, per-target expected-old hashes, immutable flags, and `project.json` last. No transition exists after `COMPLETION_PUBLISH`.
