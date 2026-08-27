# Shared state engine and v9 protocol

On Linux or macOS, first read `platform-runtime.md` and replace the PowerShell examples below with the matching `sh scripts/math_research.sh ...` command. The dispatcher calls this same state engine directly for v9 operations and does not change any state-machine rule. Windows continues to use the existing PowerShell wrappers unchanged.

Read this reference before v8 worker dispatch, every v9 startup, v9 transition, v8-to-v9 successor, or v9 publication. The Python engine in `scripts/math_research_state_v9.py` is the single machine definition for v9 ticket closure, state validation, transition legality, typed evidence, manifests, audit escalation, and guarded publication. Do not reproduce those rules in a startup or commit wrapper.

## Compatibility boundary

- v3-v8 projects remain byte-preserved and are classified by Startup v3 through the v4 delegating wrapper.
- Never reinterpret a v8 project as v9 or rewrite its `project.json`.
- A v9 successor uses a new project root with the same project lineage ID, a new run ID, and an immutable predecessor head-hash record. Preparing or committing it never writes the predecessor root.
- The existing v8 legacy-successor builder and v8 head helper remain the only writers for an already-v8 project.

## v8 pre-dispatch closure

Before dispatching or resuming any v8 solver or verifier ticket, run `scripts/invoke_math_research_ticket_preflight_v8.ps1`. The command requires:

- the project root;
- the exact frozen-ticket wrapper;
- one `math-research-source-requirements/v1` manifest whose own path/hash is already a ticket `input_artifacts` member;
- optionally, a returned worker-access log.

The source-requirements manifest has exact keys:

```json
{
  "schema": "math-research-source-requirements/v1",
  "requirements": [
    {
      "id": "stable-source-id",
      "role": "primary_source",
      "path": "project/relative/source.ext",
      "sha256": "64 lowercase hex",
      "required": true
    }
  ]
}
```

Allowed roles are `primary_source`, `formula_extract`, `prior_proof`, `computation_output`, `task_contract`, `candidate`, `dependency`, and `other`. Every ticket input other than the manifest itself needs exactly one typed requirement; every required entry must be an exact ticket input; every input must be covered by `read_paths`. A frozen Contract pointer may be a control read without being duplicated as a mathematical input. Any other readable path is invalid.

When available, a worker return includes:

```json
{
  "schema": "math-research-worker-access-log/v1",
  "reads": ["project/relative/source.ext"]
}
```

An unbound reported read invalidates the entire worker return. The preflight result emits a capsule with `required_fork_turns="none"`; dispatch the collaboration worker with exactly that value and only the ticket/capsule inputs. This is protocol isolation on a shared filesystem, not a platform capability or filesystem sandbox. The access log is worker-reported and cannot prove that an unreported read did not occur.

## v9 ticket

A v9 frozen ticket uses exact top-level keys:

```text
schema, ticket_id, role, initial_lifecycle, source_requirements,
input_artifacts, allowed_reads, writable_staging_path, decision_question,
allowed_tools, resource_caps, required_outputs, failure_return
```

Its schema is `math-research-ticket/v9`, role is `attempt|audit`, and `initial_lifecycle` is `planned`. Each `input_artifacts` entry has exact `id,role,path,sha256`; each `source_requirements` entry has exact `id,role,required`. Required IDs and roles must match inputs, input IDs are unique, and the set of `allowed_reads` must exactly equal the set of input paths. The writable path must lie under a `staging` directory.

Dispatch always uses `fork_turns="none"`. The Goal Host supplies only the immutable ticket, bound inputs, fixed stop rule, and required output contract. Goal state, other conversation history, evaluator-private records, and unrelated project files stay outside the worker context.

## v9 project head

`project.json` has exact keys:

```text
schema, project_id, control_generation, state, event_tail,
archive_manifest, last_full_audit_generation, last_full_audit_at_utc
```

The schema is `math-research-project/v9`. State, event tail, and archive manifest are exact project-relative path/SHA-256 pointers. The head contains no mutable proof claim and is not Goal authority.

The state has exact keys:

```text
schema, project_id, control_generation, active_run, current_attempt,
current_ticket, counters, evidence_items, typed_references, updated_at_utc
```

`active_run` binds the run ID, status, semantic/permission/resource envelope hashes, predecessor, and run-local budgets. Counters have separate `run_local` and `cumulative` snapshots. Each snapshot contains `attempt_count`, `audit_count`, `total_round_count`, and `attempts_since_last_audit`; totals are mechanically checked.

## Ticket and attempt lifecycle

The only ticket lifecycle is:

```text
planned -> active -> solver_completed -> verifier_completed -> closed
```

The shared engine enforces these transition preconditions:

- `ATTEMPT_START`: a preparing run, no current attempt, and one planned ticket; consumes one attempt and one round while preserving one terminal-audit round.
- `SOLVER_COMPLETE`: an active attempt ticket and an immutable solver-result pointer.
- `VERIFIER_COMPLETE`: `solver_completed`, an exact verifier-completion identity binding, and typed evidence bound to the same run/attempt/ticket.
- `ATTEMPT_END`: `verifier_completed`, an exact attempt record with the same disposition and evidence, plus an optional fresh planned next ticket.
- `CHECKPOINT_COMMIT`: typed references only; arbitrary untyped blobs are rejected.

Attempt disposition is exactly `candidate`, `no_candidate_with_evidence`, `no_candidate`, `inconclusive`, or `blocked`. `candidate` requires a PASS verifier completion and candidate evidence. `no_candidate_with_evidence` requires PASS and at least one `verified_partial`. Closing without a next ticket yields `audit_due` for a candidate and `awaiting_input` otherwise.

Typed evidence is `candidate`, `verified_partial`, `failure_boundary`, `source_claim`, or `exact_computation`. Typed checkpoint references are restricted to attempt, solver, verifier, partial-result, candidate, failure, audit, route, and handoff records. Every pointer is path/hash checked and every applicable attempt/ticket binding is mechanical.

## Prepare and commit

Use:

```powershell
scripts/prepare_math_research_transition_v9.ps1 \
  -ProjectPath <v9-project> -Transition <event> \
  -PayloadPath <payload.json> -OutputPath <non-authoritative-stage> \
  -AuditMode Auto

scripts/commit_math_research_transition_v9.ps1 \
  -PlanPath <transition-plan.json> -GoalStatus active
```

Preparation is Goal-agnostic and writes only outside the project. It canonicalizes JSON, preserves UTC strings, builds the next state/event/manifest/head, hashes every byte, and binds the expected old head. Publication requires a fresh product `get_goal` immediately before the wrapper. The literal `GoalStatus` argument is only a fail-closed Host assertion; it is not Goal evidence.

Commit uses a cooperative lock, verifies the expected old head, publishes immutable files create-new, rechecks the old head, then replaces and reads back only `project.json`. A retry reuses exact bytes. A competing valid plan loses the CAS. The lock does not exclude a non-cooperating writer and publication is not a multi-file transaction.

## RUN_SUCCESSOR

Use `scripts/prepare_math_research_successor_v9.ps1` with a terminal predecessor project, a separate empty successor project root, and one `math-research-successor-spec/v9` file. The spec binds:

- predecessor project/run IDs, live head hash, final status, three envelope hashes, and remaining attempt/round budgets;
- successor project/run IDs, the same three envelope hashes, and budgets no greater than the predecessor remainder;
- inherited cumulative counters;
- reason `budget_exhausted|route_exhausted|schema_upgrade|operator_request`;
- one complete planned v9 ticket and RFC3339 UTC time.

The successor begins with zero run-local counters and exact inherited cumulative counters. Any semantic, permission, privacy, external-effect, or resource-envelope hash difference fails closed. The prepared `RUN_SUCCESSOR` event and lineage artifact contain the predecessor head hash but no authority to resume the predecessor Goal.

## AuditMode

`scripts/invoke_math_research_startup_v4.ps1` accepts `Auto|Full` and delegates v3-v8 projects byte-for-byte to Startup v3.

For v9, every startup hashes the current head, state, event tail, archive manifest, current ticket, and newest generation. `Auto` checks the names, sizes, and nanosecond mtimes of older manifest entries. It escalates to full hashing on metadata drift, after ten generations without a full audit, after seven days, or when the Host explicitly chooses `Full`. Unknown authoritative files fail closed. A same-byte metadata drift may pass only after full hashing and is reported as an escalation; a historical content mismatch fails.

The immutable manifest and local hashes detect ordinary corruption. They do not defend against a person with full access to the Windows account who deliberately replaces the engine and all records. Cache/metadata checks are advisory acceleration and never override a hash mismatch.
