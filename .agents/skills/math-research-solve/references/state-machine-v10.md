# Math Research state machine v10

## Contents

- Authority and compatibility
- Production entries
- Project state
- Ticket lifecycle
- Attempt transitions
- Research checkpoint
- Evidence promotion
- Successor creation
- Publication order
- Startup classifications
- Failure modes

## Authority and compatibility

The v10 engine validates files, hashes, schemas, counters, and transition legality. It never proves Goal state. The current task must call `get_goal` immediately before any authoritative mutation and pass `GoalStatus=active` only as the final caller assertion to the commit helper.

Projects with `math-research-project/v3` through `/v9` remain under their frozen implementation. Startup v5 delegates them to Startup v4 and earlier classifiers. Never rewrite an old project head, manifest, state file, ticket, or event as v10.

## Production entries

Windows entries:

- `scripts/invoke_math_research_startup_v5.ps1`
- `scripts/invoke_math_research_worker_dispatch_preflight.ps1`
- `scripts/invoke_math_research_execution_topology.ps1`
- `scripts/invoke_math_research_ticket_preflight_v10.ps1`
- `scripts/prepare_math_research_successor_v10.ps1`
- `scripts/prepare_math_research_transition_v10.ps1`
- `scripts/commit_math_research_transition_v10.ps1`

The shared Python implementation is `scripts/math_research_state_v10.py`. Preparation writes only outside the project. Commit publishes immutable files create-new and replaces `project.json` last under an expected-head cooperative CAS check.

Worker-dispatch preflight is a separate read-free topology planner. It checks that the ticket path stays under the project root and that the chosen transport is compatible with the Host workspace roots. For a project outside every Host workspace root it rejects ordinary collaboration dispatch and accepts only a context-free process whose execution workspace equals the project root. It does not read the ticket, grant filesystem access, prove user authorization, launch a worker, or replace the execution-topology round trip and ticket preflight.

Execution-topology proof runs in the exact future worker, ingest/publisher, and long-lived desktop/application consumer boundaries. It hashes every input, creates worker- and publisher-owned probes, requires publisher readback plus recursive consumer readback under the frozen OS principal, and only then produces one short-lived generation-bound receipt. After every publication, the same consumer boundary must recursively reopen the published tree and match `project.json`. Probes, receipts, and consumer results are data-plane evidence, never Goal authority.

On POSIX, use the dispatcher documented in `platform-runtime.md`. A missing or old runtime fails closed; the Skill does not install one.

## Project state

The v10 head schema is `math-research-project/v10`. It binds:

- `project_id` and `control_generation`;
- current `math-research-state/v10`;
- current `math-research-event/v10`;
- current `math-research-archive-manifest/v10`;
- last full-audit generation and time.

The v10 state contains:

- active run and immutable envelope hashes;
- independent `current_attempt` and `current_ticket`;
- current continuity capsule and active route card;
- optional structured strategy action;
- optional route-reset lifecycle facts: earliest trigger generation and codes, accepted portfolio generation and pointer, predecessor attempt and lead, selected route, successor capsule, and the single successor attempt ID;
- run-local and cumulative counters;
- verifier-bound evidence and typed references.

The active attempt additionally binds `lead_id`, an exact SHA-256 fingerprint of `attempt_scope`, and `checkpoint_count`.

## Ticket lifecycle

The lifecycle is:

```text
planned -> active -> solver_completed -> verifier_completed -> closed
```

`RESEARCH_CHECKPOINT` self-loops on `active`. A non-promoting negative attempt may transition from `active` or `solver_completed` directly to `closed`. Promoted evidence requires `verifier_completed`.

Every v10 ticket binds:

- typed source requirements and complete input artifacts;
- exact `allowed_reads` closure;
- ticket-local staging root;
- decision question, tools, caps, outputs, and failure return;
- continuity capsule and route card pointers;
- persistent lead identity;
- attempt-scope fingerprint fields.

The capsule and route card must appear as typed input artifacts. Every capsule `required_full_artifact` must also be present. Preflight fails as `ticket_full_context_missing` before dispatch when a summary is supplied instead.

Ticket isolation and OS sandbox topology are separate gates. Run dispatch planning, the exact-topology round trip, and ticket preflight before a counted start and dispatch. When project-root rebinding is required, keep the worker context ticket-only, let the Goal Host own the approval request, and perform all reads of worker-created staging bytes inside the same project-root boundary. Copying bound inputs into a different workspace invalidates the intended evidence closure.

## Attempt transitions

### `ATTEMPT_START`

Requires a preparing run, planned ticket, no current attempt, a valid capsule/route binding, remaining budget for one attempt plus the reserved terminal-audit round, and one current `math-research-execution-topology-receipt/v1`. The receipt must bind the live head generation, exact ticket and inputs, exact staging root, worker topology, and independent ingest/publisher readback; it must be unexpired and live inside ticket staging. Validation occurs before counters change. Payload `attempt_kind` must equal the frozen ticket-scope kind. An unchanged scope cannot be closed and reopened as a fresh attempt. The transition increments attempt and total-round counters once, records the receipt as a typed reference, records the lead and scope fingerprint, and makes the ticket active.

### `SOLVER_COMPLETE`

Binds one immutable solver result and advances to `solver_completed`. Use it when an immutable result is ready for independent verification. Ordinary progress stays under `RESEARCH_CHECKPOINT`.

### `VERIFIER_COMPLETE`

Requires `solver_completed`. It binds one `math-research-verifier-completion/v10` and typed evidence for the exact attempt and ticket. Verdict is `PASS`, `FAIL`, or `INCONCLUSIVE`; any published mathematical evidence requires `PASS`, and candidate evidence must equal the completion's candidate pointer.

### `ATTEMPT_END`

Disposition is `candidate`, `no_candidate_with_evidence`, `no_candidate`, `inconclusive`, or `blocked`.

- `candidate` requires PASS plus candidate evidence.
- `no_candidate_with_evidence` requires PASS plus verified-partial evidence.
- any promoted `candidate`, `verified_partial`, or `failure_boundary` requires a matching verifier completion.
- a non-promoting negative outcome may have no verifier.

The attempt record schema is `math-research-attempt-record/v10` and binds the optional verifier pointer explicitly. The transition closes the current ticket and either installs one fresh planned ticket or enters `audit_due`/`awaiting_input`.

### `ROUTE_RESET_TRIGGER`

Requires an active attempt, one reset assessment whose deterministic result is required, and an active capsule directive whose trigger matches that assessment. An explicit user ban must name at least one forbidden mechanism family. It records the first accepted trigger-event generation, ordered trigger codes, and predecessor attempt. A second trigger record is rejected until the current reset lifecycle is completed. Semantic truth not derivable from controller history remains an independent strategy-audit obligation.

### `ROUTE_PORTFOLIO_ACCEPT`

Requires a recorded trigger for the current predecessor attempt, the unchanged active reset directive, a valid route portfolio, exactly one active/accepted selected route with a new route ID, and a successor capsule that binds it. The successor capsule must keep the target, all complete terminal claims, every required full artifact, and all forbidden families; admit no new terminal claim without PASS-bound evidence; keep live/rejected/quarantined registries disjoint; retire every superseded live route; carry the canonical inactive reset directive; and use the portfolio-acceptance generation. It records the acceptance generation and immutable pointers. It does not itself consume an attempt. After acceptance, the only legal control sequence is predecessor `ATTEMPT_END` followed directly by successor `ATTEMPT_START`.

The predecessor may then close with one planned ticket. `ATTEMPT_END` validates that ticket against the recorded selected route and successor capsule before publishing it; `ATTEMPT_START` rechecks the same binding, records one distinct successor attempt ID, and activates those pointers. A second successor for the same reset is rejected. When that successor ends, the reset lifecycle becomes completed.

Reset identity replacement is atomic. The planned successor ticket must use a fresh ticket ID, fresh route ID, and fresh lead ID with `persistent_lead.mode=new` and `previous_ticket_id=null`; `ATTEMPT_START` supplies the fresh attempt ID. Both predecessor close and successor start reject a ticket whose lead equals the trigger-time predecessor lead. Continuation outside reset instead preserves the current attempt, ticket, lead, and route together.

### `CHECKPOINT_COMMIT`

This legacy-compatible v10 operation binds typed references outside the research-continuity semantics. It does not alter counters. Use `RESEARCH_CHECKPOINT` for active proof work.

### `ASSET_REGISTRY_UPDATE`

Requires a nonterminal run and one validated `math-research-asset-index/v1` pointer. The exact payload keys are `schema`, `asset_index`, and `occurred_at_utc`. It updates only the optional state `asset_index`, generation/timestamp, event, and archive manifest. It consumes no attempt, audit, total round, checkpoint, budget, evidence promotion, or route reset. Existing v10 states without `asset_index` remain readable; new research assets or formal asset dependencies require the pointer before use. See [research assets and export](research-assets-and-export.md).

## Research checkpoint

`RESEARCH_CHECKPOINT` requires an active attempt and active ticket. Payload keys are:

- `schema=math-research-transition-payload/v10`;
- new capsule pointer;
- typed references;
- reason code;
- timestamp.

Reason is `material_result`, `agent_handoff`, `context_compaction`, `cadence_30m`, or `route_internal_revision`.

The new capsule generation must equal the prepared transition generation. Project, run, target, ticket scope, lead, resource envelope, and counters remain fixed. A newly verified/refuted proof-spine claim must already point to PASS-verifier-bound evidence in state. Existing terminal claims are immutable complete records. During a triggered reset, the directive cannot be rewritten; after portfolio acceptance, checkpoints are forbidden. The transition increments only `checkpoint_count`.

## Evidence promotion

Evidence kinds remain:

- `candidate`;
- `verified_partial`;
- `failure_boundary`;
- `source_claim`;
- `exact_computation`.

Only the first three are mathematical promotion events and require verifier binding when newly asserted as proof status. Source claims and computations retain their own reproducibility records and do not become proof merely by being present.

Completion cannot use `working` or `conditional` claims. Terminal audit must inspect the exact candidate, complete dependencies, capsule, route history, and quantifier coverage.

## Live v8 incremental migration

An explicitly authorized nonterminal v8 schema upgrade is not `RUN_SUCCESSOR` and
does not fake a terminal v8 event.  Read
`references/incremental-v8-to-v10-migration.md`.  Generation 1 of the separate v10
successor uses event type `V8_INCREMENTAL_MIGRATION`, a `migration` state record,
the exact inherited cumulative counters, zero run-local counters, remaining (not
refreshed) budgets, a complete predecessor inventory, and the inherited asset index.
The active-run predecessor status is `superseded_by_v10_migration` only after the
same create-new freeze record has been written into v8.

The v8 freeze marker is operational authority, not mathematical evidence and not a
Goal attestation.  Official v8 startup becomes read-only and its head publisher
rejects all further commits.  A migrated v10 `ATTEMPT_START` reopens the sibling
marker and predecessor head before topology-receipt validation or counter changes.
Missing or different bytes fail as `predecessor_not_frozen` or
`predecessor_changed_after_migration` and consume no attempt.

## Terminal successor creation

Use one `math-research-successor-spec/v10` in a separate empty successor root. It binds:

- terminal predecessor identity and live head hash;
- unchanged semantic, permission, privacy/external-effect, and resource-envelope hashes;
- remaining attempt and round budgets;
- inherited cumulative counters;
- initial ticket, capsule, and route card;
- creation reason and timestamp.

The successor keeps the same `project_id`, receives a new `run_id`, and never writes the predecessor. Budgets may not exceed the predecessor remainder. Any envelope change requires new authority and a new contract rather than automatic successor creation.

## Publication order

1. Write payload-referenced candidate artifacts inside the project but leave them unmanifested.
2. Run the prepare helper outside the project. It validates the live head and permits only payload pointers as temporary unmanifested inputs.
3. Inspect the returned plan and exact hashes.
4. Call `get_goal` freshly.
5. Commit with `GoalStatus=active`.
6. The helper creates immutable state/event/manifest files and replaces `project.json` last.
7. Read back startup state before dispatching or reporting authority.

The lock and CAS protect cooperating writers only. They are not a security boundary against arbitrary same-account edits.

## Startup classifications

- `fresh_project_slot`: `project.json` is absent.
- `v10_ready`: v10 head, state, manifest, capsule, route, ticket, and hashes validate.
- `delegate_startup_v4`: an older schema is present.

`v10_ready` reports run status, ticket lifecycle, capsule pointer, route pointer, audit mode, and audit notes. The model Host decides the next permitted action only after a fresh Goal check.

## Failure modes

Important fail-closed codes include:

- `ticket_full_context_missing`;
- `ticket_scope_changed`;
- `semantic_reset_required`;
- `route_reset_sequence_invalid`;
- `partial_reset_identity`;
- `surface_route_reset`;
- `coverage_bridge_missing`;
- `unverified_claim_promotion`;
- `verification_required`;
- `worker_access_out_of_scope`;
- `worker_staging_escape`;
- `worker_workspace_mismatch`;
- `execution_workspace_mismatch`;
- `topology_receipt_required`;
- `topology_receipt_invalid`;
- `topology_receipt_mismatch`;
- `topology_receipt_stale`;
- `topology_changed`;
- `worker_input_unreadable`;
- `worker_staging_unwritable`;
- `host_or_ingest_readback_unavailable`;
- `publisher_topology_unavailable`;
- `consumer_principal_mismatch`;
- `consumer_readback_unavailable`;
- `consumer_scandir_unavailable`;
- `consumer_file_unreadable`;
- `consumer_head_mismatch`;
- `acl_authority_not_propagated`;
- `ticket_path_escape`;
- `strategy_audit_new_math`;
- `budget_exhausted`;
- `manifest_unexpected_file`;
- `archive_hash_mismatch`;
- `cas_conflict`;
- `goal_not_active`.

On any nonzero result, preserve project and staging bytes, do not fabricate a transition, and repair only the stated invariant.
