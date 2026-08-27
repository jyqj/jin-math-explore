# Persistent research-project archive

This reference defines the durable file model for `math-research-solve`. It is an archive and recovery aid, not a substitute for the product Goal control plane. New v10 runs are owned directly by the current Goal task and use collaboration subagents only. The detailed v8 sections below remain authoritative for existing v8 projects.

## v10 continuity additions

Before route selection or computation, a project query entrypoint must expose the current `math-research-asset-index/v1` when one exists. Store v10 authoritative registries under `state/assets/` and bind them through `ASSET_REGISTRY_UPDATE`. For v8 and earlier projects without an active Goal, store only an `auxiliary_non_authoritative` index under `state/agent-query/` and leave the old head and counters byte-identical. See [research assets and private export](research-assets-and-export.md).

A v10 run adds immutable, manifest-bound files under the active run:

```text
runs/<run-id>/
├── continuity/
│   └── capsule-gNNNN.json
├── routes/
│   ├── route-<id>.json
│   └── portfolio-<id>.json
├── strategy/
│   └── action-gNNNN.json
└── tickets/
    └── <ticket-id>.json
```

Startup reads the v10 state, then the current capsule and route card. It loads every complete proof artifact named by `required_full_artifacts`, even when a shorter result summary exists. This is the authoritative proof-spine recovery path; `README.md`, `CURRENT.md`, and human summaries remain orientation only.

`RESEARCH_CHECKPOINT` publishes a new capsule generation and typed references without ending the current attempt. The manifest records all referenced full artifacts. A successor inherits the last capsule, active/quarantined/rejected route registries, verified evidence, failures, counters, and remaining budget; it never copies only the summaries.

## Authorization and initialization

Read-only discovery may locate a project. Authoritative initialization or research requires explicit launch intent for the exact Contract v8 envelope and a fresh `get_goal` result showing the intended current Goal is active.

While active, genesis freezes the Contract, run identity, Goal/problem bindings, counters, checkpoint, advisory host state, and initial ticket before any worker starts. If the Goal is absent, cancelled, paused, blocked, or complete, do not initialize, repair, publish, or backfill project state.

Fresh v8 genesis requires startup's exact `fresh_project_slot`: `project.json` is absent and no conflicting partial tree exists. An existing pre-v8 head with no bound active Contract/run is fail-closed/read-only; it cannot use the absent-head genesis path. An existing legacy head with a bound Contract/run may enter only the normalized same-target/nonexpanded `LEGACY_SUCCESSOR` protocol below.

## Canonical layout

```text
project-root/
├── README.md
├── project.json
├── contracts/
│   └── contract-vN.md
├── state/
│   ├── goal-host-v8.json              # legacy/fixed-path input only
│   ├── checkpoint.json                # legacy/fixed-path input only
│   ├── generations/
│   │   └── g0001/
│   │       ├── checkpoint.json        # immutable generation file
│   │       └── goal-host-v8.json      # immutable generation file
│   ├── successors/
│   │   ├── g0001.json                 # immutable legacy-successor lineage
│   │   └── g0001-predecessor-project.json # exact old project.json bytes
│   ├── successor-baselines/
│   │   └── g0001.json                 # immutable inherited counter/budget baseline
│   ├── project-events/
│   │   └── g0001.json                 # immutable chained project event
│   ├── problem.md
│   ├── status.md
│   ├── open-routes.md
│   └── best-partial-results.md
├── runs/
│   └── <run-id>/
│       ├── run.json                    # immutable v8 RUN_GENESIS record
│       ├── host-bindings/
│       │   └── host-bind-g0001.json    # immutable chained event
│       ├── events.ndjson
│       ├── tickets/
│       ├── attempts/
│       ├── audits/
│       ├── failures/
│       ├── evidence/
│       │   ├── effective-predecessor-envelope.json # successor only; immutable
│       │   ├── control-migration-map.json          # successor only; immutable
│       │   └── inherited-artifacts.json            # successor only; immutable
│       ├── routes/
│       ├── staging/
│       └── handoff.md
├── history/
│   ├── contracts/
│   ├── runs/
│   └── legacy/
└── CURRENT.md
```

Additional files are allowed but must be indexed by an authoritative record before use. Human-readable Markdown summarizes machine records; it never overrides them.

## Read order

Use the smallest sufficient read set:

1. `project.json`;
2. for a v8 head, the exact generation-unique checkpoint and Goal-host state paths/hashes named by `project.json`, plus its project-event head;
3. for a legacy project without those v8 pointers, the fixed `state/checkpoint.json` and any fixed legacy state only for read-only classification;
4. the exact Contract and run named there;
5. the current ticket/attempt/audit and their referenced artifacts;
6. `CURRENT.md` and human state views only for orientation.

Do not recursively load all history. Startup v3 performs strict, read-only classification and returns bounded pointers. It never grants execution authority.

## `project.json`

Record immutable project identity and mutable pointers separately. For v8, `project.json` has the exact top-level key set shown below:

- schema and stable `project_id`;
- stable opaque project-identity binding hash;
- exact problem statement path/hash;
- active or last Contract path/version/binding;
- active or last run ID/path;
- run lifecycle status inside `active_run.status`;
- the current control generation and each generation-bound pointer's activation generation.

Timestamps and detailed lifecycle data belong in the referenced project event/checkpoint/advisory state, not as extra v8 project-head keys. New v8 `project.json` is the single authoritative project head:

```json
{
  "schema": "math-research-project/v8",
  "project_id": "stable-project-id",
  "project_identity_sha256": "64 lowercase hex",
  "problem_statement_sha256": "64 lowercase hex",
  "control_generation": 1,
  "active_checkpoint": {
    "path": "state/generations/g0001/checkpoint.json",
    "sha256": "64 lowercase hex",
    "control_generation": 1
  },
  "goal_host_state": {
    "path": "state/generations/g0001/goal-host-v8.json",
    "sha256": "64 lowercase hex",
    "control_generation": 1
  },
  "project_event_head": {
    "path": "state/project-events/g0001.json",
    "sha256": "64 lowercase hex",
    "control_generation": 1
  },
  "host_binding_head": {
    "path": "runs/run-0001/host-bindings/host-bind-g0001.json",
    "sha256": "64 lowercase hex",
    "control_generation": 1
  },
  "active_contract": {
    "path": "contracts/contract-v8.md",
    "version": "v8",
    "binding_sha256": "64 lowercase hex"
  },
  "active_run": {"id": "run-0001", "path": "runs/run-0001", "status": "preparing"},
  "legacy_successor": null
}
```

Generation files are immutable. Prepare and verify both candidate files first, then—after the fresh Goal gate—invoke `scripts/commit_math_research_head_v8.ps1` to replace only `project.json` as the final **cooperative guarded CAS under the sole-writer/helper protocol**. Before that replacement they are unreferenced and non-authoritative. The Goal-agnostic helper supplies a named mutex, expected-old hash/generation check, strict pointer validation, and same-directory flushed atomic replace. Those checks serialize cooperating v8 writers; they do not exclude an arbitrary non-cooperating process, and only the final head-file replacement is atomic. A legacy `project.json` without these fields continues to use its fixed paths for read-only classification only.

`project_identity_sha256` is an opaque 64-hex identity binding frozen at genesis and cross-bound through Contract/project state. This release does not define or verify it as a hash of the absolute filesystem path, so it must not be advertised as proof that a same-named copied directory is the original project. Canonical path containment checks and the fresh Goal/authorization gate remain separate requirements.

The v8 path requires `schema` to equal exactly `math-research-project/v8`. A legacy schema (including schema 1) remains legacy/read-only even if unknown v8-looking pointer keys were appended; startup must never upgrade identity by key presence.

For an activated legacy successor, `project.json.legacy_successor` is non-null and has exactly `path`, `sha256`, and `control_generation`, for example `state/successors/g0002.json`. It points to an immutable lineage object of this exact shape:

```json
{
  "schema": "math-research-legacy-successor-lineage/v8",
  "project_id": "stable-project-id",
  "control_generation": 2,
  "legacy_goal_bindings_obsolete": true,
  "predecessor": {
    "project_head_snapshot": {"path": "state/successors/g0002-predecessor-project.json", "sha256": "64 lowercase hex"},
    "run_id": "legacy-run-id",
    "run_path": "runs/legacy-run-id",
    "contract": {"path": "contracts/legacy-contract.md", "sha256": "64 lowercase hex"},
    "primary_manifest": {"path": "runs/legacy-run-id/run.json", "sha256": "64 lowercase hex"},
    "backup_manifest": {"path": "runs/legacy-run-id/run.json.bak", "sha256": "64 lowercase hex"},
    "checkpoint": {"path": "state/checkpoint.json", "sha256": "64 lowercase hex"},
    "handoff": {"path": "runs/legacy-run-id/handoff.md", "sha256": "64 lowercase hex"}
  },
  "inherited_artifact_index": {
    "path": "runs/run-0002/evidence/inherited-artifacts.json",
    "sha256": "64 lowercase hex"
  },
  "inherited_counter_budget_baseline": {
    "path": "state/successor-baselines/g0002.json",
    "sha256": "64 lowercase hex"
  },
  "successor": {
    "contract": {"path": "contracts/contract-v8.md", "binding_sha256": "64 lowercase hex"},
    "run_id": "run-0002",
    "run_path": "runs/run-0002",
    "run_genesis": {"path": "runs/run-0002/run.json", "sha256": "64 lowercase hex"},
    "host_bind": {"path": "runs/run-0002/host-bindings/host-bind-g0002.json", "sha256": "64 lowercase hex"}
  }
}
```

After a fresh active-Goal check, invoke the current production `scripts/build_math_research_legacy_successor_v8.ps1` with the project, exact raw Goal objective/raw UTF-8 SHA-256, and optional exposed stable task/thread ID. Its exact `math-research-legacy-successor-build-result/v8` must report `built=true`, matching expected-old/new values, and `trust=staging_only_strict_self_consistency_no_hmac_authenticity_not_goal_authorization`. The builder is Goal-agnostic, does not authenticate legacy HMACs, and never replaces `project.json`; its same-project mode writes only additive unreferenced candidates, while `-DryRun` is read-only and `-OutputDirectory` stages in a distinct absent non-nested byte-for-byte copy. It copies the exact predecessor `project.json` bytes to `project_head_snapshot`; that hash is the **activation transition** expected-old hash. An absent predecessor backup/checkpoint/handoff is represented by `null`, never by omitting the key. This immutable lineage file **is** the `LEGACY_SUCCESSOR` record. While staged it and the snapshot are non-authoritative/unreferenced; after a second fresh Goal gate it becomes activated only when the cooperative guarded `project.json.legacy_successor` head transition selects its exact path/hash/activation-generation. On success the old head remains auditable through the snapshot; on failure the live old `project.json` is untouched. There is no separate activation-event hash and no Contract→lineage self-reference. On every later v8 generation, `project.json.legacy_successor` preserves that original pointer byte-for-byte: its `control_generation` is the successor **activation generation**, not the current head generation, and its predecessor snapshot is not compared with later expected-old hashes.

If the legacy head exposes a valid parseable nonnegative-integer `control_generation`, successor activation generation is that value plus one. If the key is absent, the first v8 generation is exactly `1`; if the key is present but malformed, fail closed instead of treating it as absent. That activation number controls the `gNNNN` names in lineage, snapshot, baseline, and the initial successor state files; later ordinary state generations advance while the activated lineage/snapshot/baseline names remain immutable.

### Effective predecessor envelope and control migration

`LEGACY_SUCCESSOR` does not compare the obsolete launcher/control mechanism byte-for-byte with v8. It first materializes two immutable, raw-hash-bound artifacts under `runs/successor-gNNNN/evidence/`. They are not added to the exact lineage, state, or checkpoint schemas. Instead, the immutable successor Contract contains their exact project-relative paths and raw SHA-256 hashes, and the first `LEGACY_SUCCESSOR` project event includes both pointers in `referenced_artifacts`. The production builder performs their dedicated exact-schema/source derivation checks. The head helper and startup apply the generic project-event raw-pointer/hash validator; they do not contain a second dedicated parser for these two schemas and do not re-prove natural-language equivalence. Therefore the protocol requires the exact successful builder result before activation; a hand-assembled lookalike candidate is not an authorized route.

`effective-predecessor-envelope.json` has schema `math-research-effective-predecessor-envelope/v8` and these exact top-level/nested keys:

```json
{
  "schema": "math-research-effective-predecessor-envelope/v8",
  "project_id": "stable-project-id",
  "predecessor_run": {
    "id": "legacy-run-id",
    "path": "runs/legacy-run-id",
    "manifest_revision": 6,
    "manifest_status": "preparing"
  },
  "source_precedence": [
    "strict_self_consistent_current_primary_manifest_payload_after_applied_receipts_hmac_not_authenticated",
    "strict_hash_cross_bound_receipt_chain_compat_then_control_v2",
    "immutable_legacy_contract_semantic_sections_and_machine_blocks",
    "exact_cycle_ledger_checkpoint_counters_no_conflict_allowed"
  ],
  "source_bindings": {
    "project_head_snapshot": {"path": "state/successors/g0001-predecessor-project.json", "sha256": "64 lowercase hex"},
    "contract": {"path": "contracts/legacy-contract.md", "sha256": "64 lowercase hex"},
    "primary_manifest": {"path": "runs/legacy-run-id/run.json", "sha256": "64 lowercase hex"},
    "backup_manifest": {"path": "runs/legacy-run-id/run.json.bak", "sha256": "64 lowercase hex"},
    "cycle_policy": {"path": "runs/legacy-run-id/cycle-policy.json", "sha256": "64 lowercase hex"},
    "initial_tickets": {"path": "runs/legacy-run-id/cycle-tickets-000.json", "sha256": "64 lowercase hex"},
    "ledger_head": {"path": "runs/legacy-run-id/cycle-ledger/00000000.json", "sha256": "64 lowercase hex"}
  },
  "semantic": {
    "problem_statement": {"path": "runs/successor-g0001/evidence/problem-statement.md", "sha256": "64 lowercase hex"},
    "predecessor_goal_objective_sha256": "64 lowercase hex",
    "target_quantifiers_sha256": "64 lowercase hex",
    "assumptions_sha256": "64 lowercase hex",
    "completion_criteria_sha256": "64 lowercase hex",
    "objective_changed": false,
    "quantifiers_changed": false
  },
  "permissions": {
    "approval_mode": "approve_for_me",
    "web_search": "allowed",
    "sandbox": "workspace-write",
    "filesystem_read_scope": "project-index-bounded-plus-required-local-tools",
    "filesystem_write_scope": "active-successor-run-staging_then-goal-host-verified-project-publication",
    "private_data_policy": "no_unrelated_private_files_credentials_or_personal_data_to_external_services",
    "external_messages": "denied",
    "deployments": "denied",
    "purchases": "denied",
    "software_installation": "denied",
    "network_services": "denied",
    "shell_network_access": false,
    "user_plugins_and_mcp_enabled": false
  },
  "resources": {
    "model": "gpt-5.6-sol",
    "reasoning_effort": "xhigh",
    "max_child_agents": 3,
    "max_total_agents": 4,
    "max_runtime_minutes": 0,
    "allowed_tools": [
      "apply_patch",
      "collaboration.spawn_agent",
      "collaboration.send_message",
      "collaboration.wait_agent",
      "shell_command",
      "web__run"
    ]
  },
  "budgets": {
    "audit_interval_attempts": 4,
    "attempt_budget": 24,
    "total_round_budget": 33,
    "max_route_family_attempts_per_cycle": 2,
    "max_repair_batches_per_attempt": 1
  },
  "counters": {
    "attempt_count": 0,
    "audit_count": 0,
    "total_round_count": 0,
    "attempts_since_last_audit": 0,
    "audit_due": false
  },
  "amendments": [
    {
      "protocol": "math-research-legacy-v1-compat-migration/v1",
      "receipt_id": "stable-receipt-id",
      "path": "runs/legacy-run-id/compat-migration-v1/migration-receipt.json",
      "sha256": "64 lowercase hex",
      "applied_at_utc": "RFC 3339 UTC Z timestamp",
      "precedence_rank": 1,
      "objective_changed": false,
      "quantifiers_changed": false,
      "counters_reset": false,
      "permission_effect": "authorized_approval_mode_change"
    },
    {
      "protocol": "math-research-legacy-v1-control-path-amendment/v2",
      "receipt_id": "stable-receipt-id",
      "path": "runs/legacy-run-id/control-path-amendment-v2/control-path-receipt.json",
      "sha256": "64 lowercase hex",
      "applied_at_utc": "RFC 3339 UTC Z timestamp",
      "precedence_rank": 2,
      "objective_changed": false,
      "quantifiers_changed": false,
      "counters_reset": false,
      "permission_effect": "control_argv_only_no_scope_expansion"
    }
  ]
}
```

The four `source_precedence` strings and their order are fixed. First select the strict self-consistent current primary-manifest payload at its highest bound revision, after its embedded applied-receipt entries. The builder checks the recorded payload/HMAC field shapes and hash relations but **does not authenticate the legacy DPAPI HMAC**; neither that field nor the manifest supplies current authority. Then check the hash-cross-bound receipt-file chain in strict `compat-migration/v1` then `control-path-amendment/v2` order. The immutable Contract supplies semantic sections/machine blocks and the unamended baseline. The exact ledger/checkpoint supplies cumulative counters, which must agree with every receipt snapshot. Shared fields do not use a “convenient source wins” rule: any unrecorded disagreement, unknown amendment, receipt-chain break, objective/quantifier/counter reset, or permission expansion fails closed. This makes a recorded `approval_mode: never -> approve_for_me` deterministic only when the hash-cross-bound compat receipt records that amendment and the later control-v2 receipt records no scope expansion. Authority still comes exclusively from the freshly active current Goal.

The file is serialized as compact JSON from the shown insertion order using UTF-8 without BOM and exactly one trailing LF; its binding is SHA-256 of those raw bytes. Integers remain JSON integers and booleans remain JSON booleans.

`control-migration-map.json` has schema `math-research-control-migration-map/v8` and this exact shape:

```json
{
  "schema": "math-research-control-migration-map/v8",
  "project_id": "stable-project-id",
  "predecessor_run_id": "legacy-run-id",
  "successor_run_id": "successor-g0001",
  "control_generation": 1,
  "source_envelope": {"path": "runs/successor-g0001/evidence/effective-predecessor-envelope.json", "sha256": "64 lowercase hex"},
  "mapping_policy": "exact_semantic_and_ceiling_preservation_with_control_plane_retirement/v8",
  "preserved_bindings": [
    {"name": "mathematical_target_quantifiers", "mapping": "preserve_exact_hash", "source_sha256": "64 lowercase hex", "successor": "contract_problem_statement"},
    {"name": "completion_criteria", "mapping": "preserve_exact_hash", "source_sha256": "64 lowercase hex", "successor": "contract_completion_gate"},
    {"name": "permissions_privacy_external_effect_ceilings", "mapping": "preserve_effective_value", "source_sha256": "64 lowercase hex", "successor": "contract_permission_envelope"},
    {"name": "budgets_and_consumption", "mapping": "preserve_effective_value", "source_sha256": "64 lowercase hex", "successor": "contract_and_counter_baseline"}
  ],
  "retired_bindings": [
    {"name": "child_goal_created_inside_codex_exec", "mapping": "retire_without_successor_authority", "successor": null, "reason": "Goal authority belongs only to the current product task"},
    {"name": "legacy_launcher_resume_thread", "mapping": "retire_without_successor_authority", "successor": null, "reason": "No legacy Resume or isolated child-thread continuity"},
    {"name": "dispatcher_daemon_heartbeat_lease", "mapping": "retire_without_successor_authority", "successor": null, "reason": "No external scheduler or daemon authority"},
    {"name": "legacy_goal_controller_state", "mapping": "retire_without_successor_authority", "successor": null, "reason": "Historical control files remain evidence only"}
  ],
  "control_mapping": [
    {"from": "legacy_outer_or_child_goal", "mapping": "replace_with_goal_host_v8", "to": "current_product_goal_host"},
    {"from": "legacy_worker_prompt", "mapping": "replace_with_goal_host_v8", "to": "hash_bound_collaboration_ticket"},
    {"from": "legacy_project_mutation", "mapping": "replace_with_goal_host_v8", "to": "cooperative_guarded_project_head_commit"},
    {"from": "post_v8_contract_or_run_change", "mapping": "fail_closed_unimplemented", "to": "RUN_SUCCESSOR_required"}
  ],
  "unresolved_gaps": [
    {"name": "future_v8_resource_or_semantic_expansion", "mapping": "fail_closed_unimplemented", "effect": "read_only_until_RUN_SUCCESSOR_is_implemented_and_authorized"}
  ]
}
```

The only mapping enum values are `preserve_exact_hash`, `preserve_effective_value`, `retire_without_successor_authority`, `replace_with_goal_host_v8`, and `fail_closed_unimplemented`. Every nested array member has exactly the keys shown for its array. The migration map uses the same compact UTF-8/no-BOM/one-LF raw-hash rule. Only the four enumerated legacy control bindings may retire; any unknown permission/resource difference or unresolved gap is `fail_closed_unimplemented`, never silently mapped.

The independent counter/budget baseline file has this exact top-level schema:

```json
{
  "schema": "math-research-counter-budget-baseline/v8",
  "project_id": "stable-project-id",
  "predecessor_run_id": "legacy-run-id",
  "attempt_count": 12,
  "audit_count": 3,
  "total_round_count": 15,
  "attempts_since_last_audit": 0,
  "audit_due": false,
  "budget_consumption": {
    "attempt_budget_ceiling": 20,
    "attempts_spent": 12,
    "total_round_budget_ceiling": 25,
    "total_rounds_spent": 15,
    "runtime_or_other_cumulative": {
      "runtime_minutes": 0,
      "token_usage_input": 0,
      "token_usage_output": 0
    }
  }
}
```

It is derived only from predecessor records, so Contract v8 may bind its hash without a cycle. The builder derives the five counters by strict full cycle-ledger replay from `00000000.json` through the manifest checkpoint head: no gap/extra JSON, exact envelope/payload hashes, run/sequence/previous-hash chain, and closed legacy event/budget rules. The replayed final counters must equal the manifest checkpoint/head; a compatibility/control receipt instead binds the matching replayed prefix through exact `head_sequence` and `head_payload_sha256`, so later valid ledger progress is allowed. The successor `preparing` state starts exactly at this baseline; every later counter and consumption component must be no lower.

The inherited artifact index has the exact schema below:

```json
{
  "schema": "math-research-inherited-artifact-index/v8",
  "project_id": "stable-project-id",
  "predecessor_run_id": "legacy-run-id",
  "source_snapshot": {
    "primary_manifest_sha256": "64 lowercase hex",
    "backup_manifest_sha256": null,
    "checkpoint_sha256": "64 lowercase hex",
    "handoff_sha256": "64 lowercase hex",
    "authoritative_index_heads": [{"path": "legacy index path", "sha256": "64 lowercase hex"}]
  },
  "inventory_algorithm": "recursive byte inventory v1: strict non-reparse regular files sorted ordinal-ignore-case; original project.json represented by exact successor snapshot; generated successor artifacts excluded",
  "covers": [
    "problem",
    "verified_partial_results",
    "attempts",
    "failures",
    "evidence",
    "routes",
    "audits",
    "handoff",
    "source_artifacts",
    "computation_artifacts",
    "intermediate_artifacts"
  ],
  "entries": [
    {
      "category": "problem",
      "path": "state/problem.md",
      "sha256": "64 lowercase hex",
      "evidence_grade": "not_applicable"
    },
    {
      "category": "verified_partial_results",
      "path": "project-relative predecessor artifact path",
      "sha256": "64 lowercase hex",
      "evidence_grade": "original grade or not_applicable"
    }
  ],
  "category_counts": {
    "problem": 1,
    "verified_partial_results": 1,
    "attempts": 0,
    "failures": 0,
    "evidence": 0,
    "routes": 0,
    "audits": 0,
    "handoff": 0,
    "source_artifacts": 0,
    "computation_artifacts": 0,
    "intermediate_artifacts": 0
  },
  "entry_count": 2,
  "complete_source_inventory": true
}
```

`source_snapshot` hashes must equal the matching predecessor pointers in the lineage (`null` only when the corresponding nullable pointer is `null`), and every authoritative index head has a verified path/hash. `covers` is the exact canonical ordered list above. Every `entries[].category` must be one of those names; `category_counts` must have every name and sum to `entry_count`. The index must contain at least the problem plus every discovered predecessor record/artifact—no empty shell, omitted category key, omitted authoritative-index entry, transitive-reference gap, duplicate, or evidence-grade promotion is allowed.

Current Goal identities do not belong in immutable Contract bytes. They are carried by the active run's external `RUN_GENESIS`/`HOST_BIND` chain, checkpoint, and advisory state.

The immutable `runs/<run-id>/run.json` genesis record has schema `math-research-run-genesis/v8` and exact keys `schema,project_id,control_generation,contract,run,host_binding,host_goal`. Contract is the full three-key pointer, run is the full `{id,path,status}` pointer, host binding is the raw `{path,sha256}` pointer to the immutable initial binding file, and host goal is the exact three-key optional-ID/objective-hash object. It is distinct from the generation project event whose `event_type` may be `RUN_GENESIS`.

Changing the directory, problem identity, or project ID is a material operation and cannot be inferred from a similarly named folder.

## Goal-host generation state

For new v8 heads this is the generation-unique file named by `project.json.goal_host_state`; `state/goal-host-v8.json` is only a fixed-path legacy/early input. It is an ordinary hash-bound advisory snapshot with schema `math-research-goal-host-state/v8` and the exact top-level keys represented below. It binds:

- project ID and control generation;
- Contract path/version/binding hash;
- run ID/path/status;
- exact `host_goal` object with `thread_id_available`, `thread_id`, and required `objective_raw_sha256`; use `false`/`null` for the first two when the platform exposes no stable ID;
- canonical problem hash;
- monotone counters and audit gate;
- current frozen ticket `{id,path,sha256,status,contract_initial_tickets_sha256,counter_snapshot,source_event}`; `source_event` is `null` for an initial ticket and exact `{path,sha256}` for a derived ticket, and the whole object may be `null` only for closed/terminal state with no pending lifecycle object;
- update timestamp.

For a fresh run, `successor` is exactly `null`. For a legacy successor it is exactly:

```json
{
  "lineage": {"path": "state/successors/g0002.json", "sha256": "64 lowercase hex"},
  "inherited_artifact_index": {"path": "runs/run-0002/evidence/inherited-artifacts.json", "sha256": "64 lowercase hex"},
  "counter_budget_baseline": {"path": "state/successor-baselines/g0002.json", "sha256": "64 lowercase hex"}
}
```

These three pointers must equal the activated project-head lineage and its referenced objects.

## Checkpoint generation schema

The immutable file named by `project.json.active_checkpoint` has this exact shape:

```json
{
  "schema": "math-research-checkpoint/v8",
  "project_id": "stable-project-id",
  "control_generation": 1,
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001", "status": "preparing"},
  "problem_statement_sha256": "64 lowercase hex",
  "host_binding_head": {"path": "runs/run-0001/host-bindings/host-bind-g0001.json", "sha256": "64 lowercase hex"},
  "host_goal": {"thread_id_available": false, "thread_id": null, "objective_raw_sha256": "64 lowercase hex"},
  "counters": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0, "audit_due": false},
  "current_lifecycle": {"kind": "initial_ticket", "id": "C1-T1", "path": "runs/run-0001/tickets/C1-T1.json", "sha256": "64 lowercase hex"},
  "successor": null,
  "completion_ready": false,
  "pending_goal_update": false,
  "last_run_event": {"id": "RUN_GENESIS", "sha256": "64 lowercase hex"},
  "updated_at_utc": "RFC 3339 UTC timestamp"
}
```

`completion_ready` and `pending_goal_update` are valid only as `false/false` or `true/true`. Once both are true, this head and all project state are permanently read-only; neither flag may be cleared. For a successor, `counters` starts at the independent inherited baseline and `successor` is the same exact three-pointer summary used in Goal-host state. Checkpoint and Goal-host state must share project/generation/Contract/run/problem/host-goal/counters/successor/current-ticket identities; the checkpoint's raw two-key `host_binding_head` must equal the project head's binding path/hash and resolve to that same `host_goal`. Differences fail closed.

It is not cryptographically signed and does not prove a `get_goal` call, current Goal activity, permission, process isolation, or worker dispatch. Startup may reject mismatches; only the current model host can obtain fresh Goal state.

## Checkpoint and counters

The checkpoint and Goal-host generation files named by `project.json`, together with the run ledger, must agree on:

- `attempt_count`;
- `audit_count`;
- `total_round_count = attempt_count + audit_count`;
- `attempts_since_last_audit`;
- `audit_due`;
- run status and current lifecycle object;
- last committed event ID/hash.

Counters are monotone. Resume, rebind, migration, retry, pause, supersede, or any future separately implemented Contract/run successor can never rewrite historical consumption.

The run-status enum is:

```text
not_started | preparing | attempt_running | audit_due | auditing |
completion_candidate | awaiting_input | paused |
goal_continuity_terminal | superseded | closed
```

## Events and lifecycle records

Use an append-only run `events.ndjson` chain plus generation-unique immutable project-event files under `state/project-events/`. Each project event has this exact shape; its file hash is stored externally in `project.json.project_event_head` and the checkpoint:

```json
{
  "schema": "math-research-project-event/v8",
  "project_id": "stable-project-id",
  "control_generation": 2,
  "event_id": "ATTEMPT_END-0001",
  "event_type": "ATTEMPT_END",
  "updated_at_utc": "RFC 3339 UTC Z timestamp",
  "previous_event_sha256": "64 lowercase hex",
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001", "status": "preparing"},
  "counters": {"attempt_count": 1, "audit_count": 0, "total_round_count": 1, "attempts_since_last_audit": 1, "audit_due": false},
  "referenced_artifacts": [{"path": "runs/run-0001/attempts/attempt-0001/attempt.json", "sha256": "64 lowercase hex"}]
}
```

`event_type` is exactly one of `RUN_GENESIS`, `LEGACY_SUCCESSOR`, `CHECKPOINT_COMMIT`, `ATTEMPT_START`, `ATTEMPT_END`, `AUDIT_START`, `AUDIT_END`, `HOST_REBIND`, `PAUSE`, `RESUME`, or `COMPLETION_READY`. The first v8 activation uses `previous_event_sha256=null`; every later generation equals the old authoritative `project_event_head.sha256`. Contract/run/counters equal the activated generation, every artifact is a verified raw `{path,sha256}` pointer, and `project.json.project_event_head` selects the authoritative head. Goal bindings use immutable files under `runs/<run-id>/host-bindings/`; `project.json.host_binding_head` preserves the current binding's activation-generation pointer until a valid rebind replaces it. Immutable Contract bytes carry only the binding policy.

Every `ATTEMPT_END` has exactly one first referenced artifact: an immutable `math-research-attempt-outcome/v8` with exact keys `schema,project_id,contract,run,attempt_id,outcome,candidate,verifier_completion,completed_at_utc`. Its outcome is one of `candidate_found`, `no_candidate`, `inconclusive`, `failed`, or `awaiting_input`; only `candidate_found` has non-null candidate/verifier-completion pointers. That case must close the current derived verifier ticket and cross-check one immutable candidate with the ticket's `candidate_artifact` and an exact PASS verifier result or closed verifier completion, including identical ticket ID, Contract, and run. Verifier records do not contain attempt ID; outcome `attempt_id` is only required to be a safe ID distinct from the current verifier ticket ID, and its Attempt-record binding remains Host-maintained/unmechanized in this helper release.

Every `ATTEMPT_START`, not just an interval-hitting one, is admitted only when the old counters satisfy `attempt_count + 1 <= attempt_budget` and `total_round_count + 2 <= total_round_budget`. The reserved second round is the mandatory terminal-audit capacity if that attempt yields `candidate_found`.

The builder's `source_event=null` initial solver ticket is an undispatched `preparing` seed. The `ATTEMPT_START` generation replaces it with a new active derived solver ticket and non-null ticket event whose state pointer, envelope, and event all bind the post-start counters; only that activated/read-back derived ticket may be dispatched.

Every `AUDIT_START` references exactly one immutable cycle-audit plan with exact keys `schema,project_id,contract,run,audit_kind,candidate,snapshot,active_ticket,tickets,started_at_utc`: terminal uses the candidate from that locked Attempt outcome, while scheduled/early use null. Every `AUDIT_END` references exactly one immutable summary, and plan/summary/three ordered reports bind the same candidate and snapshot. A candidate found on an interval or final attempt keeps `audit_due=true`, but terminal audit takes priority and its one `AUDIT_END` clears the gate. Before terminal audit, a `completion_candidate` may advance only through `AUDIT_START` or a `HOST_REBIND` that preserves the exact Attempt outcome pointer. Terminal non-PASS returns to a noncompletion state and cannot authorize `COMPLETION_READY`.

Every host-binding file has this exact nine-key schema:

```json
{
  "schema": "math-research-host-binding/v8",
  "project_id": "stable-project-id",
  "control_generation": 1,
  "event_type": "HOST_BIND",
  "prior_host_binding": null,
  "retirement": null,
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001"},
  "host_goal": {"thread_id_available": false, "thread_id": null, "objective_raw_sha256": "64 lowercase hex"}
}
```

Initial `HOST_BIND` requires `prior_host_binding=null` and `retirement=null`. A `HOST_REBIND` uses the same exact key set, with:

```json
{
  "event_type": "HOST_REBIND",
  "prior_host_binding": {"path": "runs/run-0001/host-bindings/host-bind-g0001.json", "sha256": "64 lowercase hex", "control_generation": 1},
  "retirement": {"authority": "user-explicit-revocation", "reason": "nonempty reason"}
}
```

The second block shows the three changed member values, not a standalone file. The remaining six members retain the exact full-file schema above, with the new generation and new `host_goal`. No separate `HOST_RETIRE` event exists in v8.

Keep event layers distinct. The generation project-head transition uses only the exact closed `event_type` set above. The run `events.ndjson`/domain ledger may additionally name records such as `PUBLICATION`, `COMPLETION_CANDIDATE`, `SUPERSEDE`, or `CLOSE`, but those names never appear in `project_event_head.event_type` and grant no transition authority. A legitimate domain record is included as a raw referenced artifact under the applicable canonical project event—for example ordinary publication or completion-candidate staging under `CHECKPOINT_COMMIT`, and durable completion flags under `COMPLETION_READY`. Merely recording `SUPERSEDE`/`CLOSE` does not implement `RUN_SUCCESSOR` or bypass the current lifecycle gate. External `HOST_BIND`/`HOST_REBIND` files remain the separate exact host-binding schema above.

The immutable `state/successors/gNNNN.json` lineage file is the `LEGACY_SUCCESSOR` record. It binds the predecessor-head snapshot, immutable predecessor, complete inherited research index, independent cumulative resource baseline, new Contract/run/genesis/host-bind hashes, and activation generation. Separately, the successor Contract binds the immutable effective-predecessor-envelope and retired-control-mapping artifacts by path/hash, and the first `LEGACY_SUCCESSOR` project event lists both as raw `referenced_artifacts`; the exact lineage/state/checkpoint key sets do not change. The Host verifies normalized research-envelope equivalence, the mandatory safe contraction of legacy control authority, current-Goal authorization, and no unfinished authoritative commit before staging and again before the fresh Goal gate. The lineage is non-authoritative while staged and becomes activated only when the single project head points to its exact path/hash/activation-generation.

Startup classification and read-only diagnostics are not research events and do not consume counters.

## Tickets and staging

Tickets are immutable, hash-bound collaboration records, not signatures, capabilities, or process leases. A ticket binds exact inputs/hashes, role, decision question, allowed tools, source/network policy, filesystem scope, writable staging directory, tool/runtime/output-size caps, stop rule, evidence grade, dependencies, required output paths/schemas/hashes, and a fixed failure-return schema. Policy keys `allowed_worker_tools`, `max_ticket_tool_calls`, and `max_ticket_output_bytes` are exact: global tools are `apply_patch`, collaboration spawn/send/wait, and `shell_command`, with `web__run` only when web is allowed; ticket tools form a unique allowlist subset and cannot name Goal/control/dispatcher/launcher/lease/`exec`/retired routes, while caps cannot exceed policy. Any raw pointer used as lifecycle authority must resolve to an immutable non-staging file; staging is never authority.

Ticket kind follows lifecycle plus `source_event`, not run status alone. `source_event=null` is an initial solver ticket and startup deep-compares its exact inner content to the selected Contract initial-ticket machine-block member and counter snapshot. A derived ticket has a non-null source-event path/hash, is not required to equal an initial Contract member, and still receives the same full schema/limit validation. A verifier is derived only and has nonempty exact `{ticket_id,path,sha256}` dependencies resolving to closed solver `math-research-ticket-completion/v8` records, plus exactly one extra `candidate_artifact={path,sha256}` matching exactly one input artifact; it cannot self-reference or use a dependency hash as a candidate disguise.

The immutable frozen-ticket file has this exact wrapper shape and complete inner ticket schema:

```json
{
  "schema": "math-research-frozen-ticket/v8",
  "project_id": "stable-project-id",
  "control_generation": 1,
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001", "status": "preparing"},
  "cycle_id": "cycle-1",
  "contract_initial_tickets_sha256": "64 lowercase hex",
  "counter_snapshot": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0, "audit_due": false},
  "ticket": {
    "ticket_id": "C1-T1",
    "role": "solver",
    "planned_lifecycle_slot": "first_attempt",
    "route_id": "route-1",
    "route_fingerprint_sha256": "64 lowercase hex",
    "attempt_kind": "route_execution",
    "route_family_id": "family-1",
    "mechanism_id": "mechanism-1",
    "bottleneck_id": "bottleneck-1",
    "decision_question": "one falsifiable bounded question",
    "input_artifacts": [{"path": "state/problem.md", "sha256": "64 lowercase hex"}],
    "search_domain": "exact bounded domain",
    "success_signal": "inspectable success signal",
    "stop_signal": "exact stop signal",
    "allowed_tools": ["apply_patch"],
    "source_network_policy": {"web": "denied", "allowed_source_classes": ["project archive"], "network_destinations": []},
    "filesystem_scope": {"read_paths": ["state/problem.md"], "writable_staging_path": "runs/run-0001/staging/C1-T1/solver-1"},
    "resource_caps": {"child_agents": 1, "tool_calls": 10, "runtime_minutes": 30, "max_output_bytes": 100000},
    "dependencies": [],
    "evidence_grade_required": "proved",
    "required_outputs": [{"path": "solver-report.md", "schema": "math-research-solver-report/v1", "sha256_on_return": "required"}],
    "failure_return": {"schema": "math-research-ticket-failure/v1", "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]},
    "reopen_condition": "one falsifiable reopen condition"
  }
}
```

Do not add `source_event` to the wrapper. The ticket file cannot contain its own hash.

Each derived ticket is issued by an immutable event with these exact top-level/nested shapes:

```json
{
  "schema": "math-research-ticket-event/v8",
  "project_id": "stable-project-id",
  "control_generation": 2,
  "event_id": "TICKET_ISSUED-C1-V1",
  "ticket_id": "C1-V1",
  "ticket": {"path": "runs/run-0001/tickets/C1-V1.json", "sha256": "64 lowercase hex"},
  "role": "verifier",
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001"},
  "counters": {"attempt_count": 1, "audit_count": 0, "total_round_count": 1, "attempts_since_last_audit": 1, "audit_due": false},
  "input_artifacts": [{"path": "runs/run-0001/attempts/attempt-0001/candidate.md", "sha256": "64 lowercase hex"}],
  "dependencies": [{"ticket_id": "C1-T1", "path": "runs/run-0001/completions/C1-T1.json", "sha256": "64 lowercase hex"}],
  "updated_at_utc": "RFC 3339 UTC Z timestamp"
}
```

`ticket` is the raw two-key pointer to the frozen ticket bytes; `run` intentionally omits mutable status. Every nonempty inner/event dependency has exact `{ticket_id,path,sha256}` shape and identifies an immutable ticket-completion record. `ticket_id`, `role`, `input_artifacts`, and `dependencies` must deep-equal the frozen ticket's inner members; Contract/run/counters must equal issuance state. State `current_ticket.source_event` selects this event path/hash. This one-way event→ticket binding avoids a hash cycle.

Workers write only under `runs/<run-id>/staging/<ticket-id>/<worker-id>/`. They cannot update Goal state, authoritative counters, route selection, ledger, publication, or handoff. Returned material stays untrusted until the host validates its files and hashes and commits one lifecycle event.

The initial ticket exists after genesis. The attempt ID is assigned only at `ATTEMPT_START`; do not report an attempt ID before that event. A verifier always receives an independent derived ticket with a distinct ID/hash/role/path and exact candidate-artifact binding.

## Attempt records

Every AttemptEnd record binds:

- attempt ID, attempt kind, and frozen decision question;
- `tickets`, an array of solver/verifier ticket IDs, roles, ticket hashes, input/candidate hashes, and output artifact hashes;
- solver-report paths/hashes;
- independent candidate-verification paths/hashes and verdicts;
- preregistered repair count;
- final result artifact and evidence grade;
- source-claim records and any route portfolio;
- counter snapshots before/after;
- failure record when the result is negative or inconclusive.

A claimed candidate, subclaim, route refutation, or bounded negative result requires a separate verifier report bound to the exact final artifact hash. Solver and verifier reports cannot be the same file or hash.

## Failure, evidence, and route records

A failure record states the exact failed step, failure type, affected scope, what does **not** follow, artifact hashes, retry fingerprint, and falsifiable reopen condition. Route records use stable fingerprints so a duplicate route cannot be restarted without qualified new evidence recorded before AttemptStart.

Evidence records grade conclusions honestly: `proved`, `verified_computation`, `conditional`, `heuristic`, `bounded_negative`, `refuted`, or `unknown`. Computations preserve code/input/tool/version/domain/precision/output/error checks and reproduction instructions. Source claims preserve primary locators and as-of dates.

## Audit records

One audit freezes one Contract binding, ledger/counter snapshot, candidate/evidence set, and trigger. It contains separate reports from `skeptic_quantifiers`, `skeptic_strategy`, and `theory_tool_scout`, each returning PASS, FAIL, or INCONCLUSIVE without new proof work.

Completion requires all three PASS against the same frozen candidate and all required certificates. An audit lead is quarantined for a future registered attempt; it is not edited into the audited result.

## Publication, pause, and close

Publication is an authoritative mutation, so the host calls `get_goal` immediately before it. While the Goal remains active, update machine records first, verify them, then publish Markdown views.

For an intentional pause, fresh-check active Goal only while the run is `attempt_running` or `auditing`, persist/activate/read back the new generation `PAUSE` resume capsule/checkpoint, gates, counters, artifact hashes, and handoff, then stop dispatching and return. Any nonrunning pause fails closed. A paused head's only legal next event is `RESUME` or an exact capsule-preserving `HOST_REBIND`; `CHECKPOINT_COMMIT` and every other event fail closed. Pause performs no product Goal update; `blocked` is not a pause surrogate. A resumed attempt or audit must preserve its capsule ticket/lifecycle/counters, and `audit_due` is true exactly when the frozen gate requires it. For completion, persist/activate/read back closing state with both completion flags true. That activation permanently freezes project/head mutation. Startup then returns `goal_host_completion_pending`; perform another fresh `get_goal` immediately before `update_goal(status=complete)` and call it only when active/matching, with no project write. Never clear either flag, resume, audit, or republish. `Goal=complete` becomes read-only `goal_host_closed_review`; any other non-active final check remains read-only pending. `blocked` is used only under the platform's independent repeated-blocker rule.

## Explicit v8 host rebind

A different task may bind an existing v8 run only through the special rebind gate: user-explicit revocation of the old binding plus new Goal/rebind authorization, fresh active new Goal, no unfinished authoritative commit, and unchanged Contract semantics/permissions. User revocation is sufficient; never query the old task. The new Host stages one exact-schema `HOST_REBIND` whose `prior_host_binding` equals the old head and whose `retirement={authority:"user-explicit-revocation",reason:<nonempty>}`, plus generation files, then increments `control_generation` through the cooperative guarded head transition. The new raw objective need not equal the obsolete binding. All counters, routes, failures, evidence, and cumulative resources remain; pre-audit completion rebind preserves the exact Attempt outcome pointer, while post-audit completion rebind preserves the exact terminal summary/history. A changed target, quantifier, permission, external effect, or Contract/run identity fails closed/read-only pending a separately implemented and authorized `RUN_SUCCESSOR` protocol.

## Legacy boundary and additive successor

Prompt v3-v7 runs remain frozen under their original files, Goal/thread history, Contract, counters, and receipts. Every legacy Goal binding is retired. Historical copies belong under `history/legacy/` and are read-only.

If strict startup classification finds `goal_continuity_failed`, `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`, or failed child Goal continuity with `persistence_verified=false`, mark the plan `goal_continuity_terminal -> stop_no_retry_preserve_run`. Do not Resume, Tick, recreate a Goal, rewrite a manifest, repeat migration, reset counters, or silently convert the old run to v8.

That stop/no-op is scoped to the old run. Under a user-explicit new active Goal, the Host may add the one prescribed legacy-to-v8 Contract/run in the same project only when a deterministic effective predecessor envelope is equivalent to the new v8 Contract in target/domain/quantifiers/dependencies/assumptions/completion, model/reasoning, privacy/external effects, and every agent/runtime/attempt/audit/round/cumulative ceiling, with no permission or resource expansion. Retiring the legacy child-Goal/launcher/dispatcher/lease/migration/control-receipt path and replacing it with direct-current-task/v8 + bounded collaboration + the guarded head helper is mandatory and is the sole permitted control-mechanism contraction. A same-project `/goal $math-research-solve … continue until proved or disproved` supplies launch intent for that normalized nonexpanded envelope; do not request repeated confirmation, hashes, or commands. The current active Goal is authority; old HMACs/receipts are only bound evidence. Any other envelope difference, unresolved normalization gap, or any additional Contract/run transition beyond that `LEGACY_SUCCESSOR` is outside this implemented gate; confirmation alone does not make it executable, so remain read-only pending a separately implemented and authorized `RUN_SUCCESSOR` protocol.

The successor sequence is:

1. freeze an inherited-index manifest covering the canonical problem, verified partial results, every attempt/failure/evidence/route/audit/handoff/source/computation artifact, and all hashes/evidence grades;
2. freeze the cumulative counter, spent-budget, and remaining-ceiling baseline; never reset it;
3. snapshot exact old `project.json` bytes, then create and verify a new v8 Contract/run, external host binding, successor checkpoint/advisory state, independent baseline, complete inherited index, and immutable `state/successors/gNNNN.json` lineage entirely as staged/unreferenced material; `RUN_GENESIS` starts at the inherited baseline;
4. verify unchanged semantics/permissions and no unfinished authoritative commit, then publish the verified files without changing the old active head; the lineage binds predecessor/new-run hashes, inherited index/baseline, obsolete old bindings, and incremented control generation;
5. before the gate, bind the effective-envelope/control-mapping artifacts in the successor Contract and the first `LEGACY_SUCCESSOR` project event; after the fresh Goal gate, call `scripts/commit_math_research_head_v8.ps1` last with predecessor snapshot hash/generation as expected-old; this cooperative guarded head switch activates the new run/checkpoint/advisory state and lineage record;
6. update `CURRENT.md` and human views only after activation.

The predecessor run/manifest bytes never change. If preparation or the final guarded head transition fails, active pointers stay on the previous durable state and all successor material remains staged/unreferenced recovery-only. This is a new run continuing the same research archive, not old-Goal recovery.

## Write discipline

For each authoritative commit:

1. obtain a fresh active Goal check;
2. serialize the commit in the sole model Host and verify that no prior authoritative commit is unfinished;
3. write all proposed artifacts to non-authoritative same-directory staging names;
4. verify exact bytes/hashes and cross-file invariants;
5. perform another fresh Goal gate when the lifecycle requires it;
6. atomically publish each final artifact file one by one;
7. publish exactly one authoritative project head last via `scripts/commit_math_research_head_v8.ps1`, then human views;
8. report the durable paths/hashes before scheduling another authoritative commit.

This sequence is crash-recoverable but is not described as a multi-file atomic transaction. Until the final head/pointer is published, staged or individually placed files are non-authoritative.

Reject path escape, reparse ambiguity, duplicate JSON keys, identity/hash mismatch, counter regression, dirty audit gates, duplicate routes, or publication from a child staging area.

Local hashes and ledgers provide ordinary integrity only. They do not cryptographically attest Goal activity or model actions.
