# Math Research Contract and artifact templates v10

## Contents

- Contract requirements
- Continuity capsule
- Route card and route portfolio
- Ticket
- Worker access log
- Strategy action
- Reset assessment
- Transition payloads
- Successor spec

## Contract requirements

Freeze these fields before launch:

- canonical statement, domain, quantifier order, dependencies, assumptions, and terminal standard;
- exact evidence standard for proof, disproof, construction, classification, or decision;
- model and reasoning effort;
- current-task Goal binding policy;
- child-agent cap and persistent-lead policy;
- source, web, network, filesystem, tool, private-data, approval, and external-effect policies;
- attempt, audit, total-round, runtime, output, tool-call, and cumulative ceilings;
- audit interval and terminal-audit reservation;
- default same-family ceiling, normally two;
- initial capsule, route card, ticket, and required complete artifacts.

Keep Goal objective/task identity outside immutable Contract bytes to avoid self-reference. Hash the normalized Contract bytes and bind the hash from run state.

## Continuity capsule

Schema: `math-research-continuity-capsule/v1`.

```json
{
  "schema": "math-research-continuity-capsule/v1",
  "project_id": "project-id",
  "run_id": "run-id",
  "generation": 1,
  "target_sha256": "<sha256>",
  "proof_spine": [
    {
      "claim_id": "claim-1",
      "status": "working",
      "statement": "Exact mathematical statement.",
      "dependencies": [],
      "artifact": null
    }
  ],
  "open_bottlenecks": ["One falsifiable bottleneck."],
  "live_routes": ["route-1"],
  "rejected_routes": [],
  "quarantined_routes": [],
  "forbidden_families": [],
  "synthesis_candidates": [
    {"claim_ids": ["claim-1"], "bridge_question": "What exact bridge would combine these claims?"}
  ],
  "required_full_artifacts": [
    {"path": "inputs/problem.md", "sha256": "<sha256>"}
  ],
  "route_reset_directive": {
    "required": false,
    "trigger": "none",
    "forbidden_mechanism_family_ids": [],
    "minimum_distinct_cards": 2,
    "same_family_ceiling": 2
  },
  "updated_at_utc": "<RFC3339-Z>"
}
```

Verified or refuted claims require a complete artifact pointer. Dependencies must name claims in the same proof spine.

## Route card and route portfolio

Route-card schema: `math-research-route-card/v10`.

```json
{
  "schema": "math-research-route-card/v10",
  "route_id": "route-1",
  "status": "active",
  "core_proof_object": "Object manipulated by the proof.",
  "proof_direction": "explicit_construction",
  "quantifier_strategy": "How every frozen quantifier is covered.",
  "mechanism_family_id": "mechanism-family-1",
  "ancestor_route_ids": [],
  "coverage_bridge": {
    "status": "working",
    "statement": "Proposed bridge from the special family to the full domain.",
    "test": "A falsifiable condition that would verify or refute the bridge."
  },
  "forbidden_family_relationship": "Explain overlap or separation from forbidden families.",
  "non_renaming_reason": "Explain the changed proof object or quantifier mechanism.",
  "special_family": false,
  "created_at_utc": "<RFC3339-Z>"
}
```

Route-portfolio schema:

```json
{
  "schema": "math-research-route-portfolio/v10",
  "routes": ["<two or more complete route-card objects during reset>"],
  "created_at_utc": "<RFC3339-Z>"
}
```

## Ticket

Schema: `math-research-ticket/v10`.

```json
{
  "schema": "math-research-ticket/v10",
  "ticket_id": "ticket-1",
  "role": "attempt",
  "initial_lifecycle": "planned",
  "source_requirements": [
    {"id": "capsule", "role": "continuity_capsule", "required": true},
    {"id": "route", "role": "route_card", "required": true},
    {"id": "problem", "role": "task_contract", "required": true}
  ],
  "input_artifacts": [
    {"id": "capsule", "role": "continuity_capsule", "path": "runs/run-id/continuity/capsule-g0001.json", "sha256": "<sha256>"},
    {"id": "route", "role": "route_card", "path": "runs/run-id/routes/route-1.json", "sha256": "<sha256>"},
    {"id": "problem", "role": "task_contract", "path": "inputs/problem.md", "sha256": "<sha256>"}
  ],
  "allowed_reads": [
    "runs/run-id/continuity/capsule-g0001.json",
    "runs/run-id/routes/route-1.json",
    "inputs/problem.md"
  ],
  "writable_staging_path": "runs/run-id/staging/ticket-1/solver",
  "decision_question": "One falsifiable decision question.",
  "allowed_tools": ["shell_command"],
  "resource_caps": {
    "child_agents": 0,
    "tool_calls": 8,
    "runtime_minutes": 30,
    "max_output_bytes": 32768
  },
  "required_outputs": ["solver_report"],
  "failure_return": {
    "schema": "math-research-ticket-failure/v1",
    "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]
  },
  "continuity_capsule": {"path": "runs/run-id/continuity/capsule-g0001.json", "sha256": "<sha256>"},
  "route_card": {"path": "runs/run-id/routes/route-1.json", "sha256": "<sha256>"},
  "persistent_lead": {
    "lead_id": "lead-1",
    "mode": "new",
    "previous_ticket_id": null
  },
  "attempt_scope": {
    "attempt_kind": "route_execution",
    "target_sha256": "<sha256>",
    "route_family_id": "mechanism-family-1",
    "proof_object": "Object manipulated by the proof.",
    "quantifier_strategy": "How every frozen quantifier is covered.",
    "evidence_standard": "Exact independent verification.",
    "resource_envelope_sha256": "<sha256>"
  }
}
```

For `persistent_lead.mode=resume`, set `previous_ticket_id` to the exact prior ticket. During required semantic reset, `attempt_kind` must be `route_discovery` and `required_outputs` must include `route_portfolio`.

For the accepted semantic-reset successor, use a fresh `ticket_id`, `route_id`, and `lead_id`; set `persistent_lead.mode` to `new` and `previous_ticket_id` to null. The later `ATTEMPT_START` adds a fresh `attempt_id`. Do not mix a predecessor lead with a successor attempt, ticket, or route.

## Worker access log

Schema: `math-research-worker-access-log/v2`.

```json
{
  "schema": "math-research-worker-access-log/v2",
  "input_reads": ["inputs/problem.md"],
  "staging_reads": ["runs/run-id/staging/ticket-1/solver/solver-report.md"]
}
```

`input_reads` must be a subset of bound ticket inputs. `staging_reads` must remain inside the ticket's writable staging root.

## Execution topology

Before any counted v10 start, freeze one worker descriptor, one ingest/publisher descriptor, and one long-lived consumer descriptor using `math-research-execution-topology-descriptor/v1`. Also freeze the expected consumer OS principal; for an Obsidian project this is the desktop user running Obsidian, never the sandbox worker owner.

```json
{
  "schema": "math-research-execution-topology-descriptor/v1",
  "role": "worker",
  "transport": "project-root-exec",
  "execution_workspace_root": "<absolute project root>",
  "runner": "codex-exec",
  "sandbox_mode": "workspace-write",
  "runner_arguments": ["-C", "<absolute project root>"]
}
```

Run the three-boundary probe from [the execution-topology protocol](execution-topology-protocol.md). Publisher readback produces only an intermediate receipt; add the pointer to `ATTEMPT_START` only after recursive consumer validation promotes it to final ready state:

```json
{
  "schema": "math-research-transition-payload/v10",
  "attempt_id": "attempt-1",
  "attempt_kind": "route_execution",
  "ticket": {"path": "runs/run-id/tickets/ticket-1.json", "sha256": "<sha256>"},
  "execution_topology_receipt": {"path": "runs/run-id/staging/ticket-1/solver/execution-topology.json", "sha256": "<sha256>"},
  "occurred_at_utc": "<RFC3339-Z>"
}
```

The receipt is short-lived, generation-bound, and one-shot. It is an access/readback record, not a capability, lease, signature, Goal assertion, or permission expansion.

## Strategy action

Schema: `math-research-strategy-action/v1`.

```json
{
  "schema": "math-research-strategy-action/v1",
  "action": "continue",
  "bottleneck_progress": "Evidence-based progress statement.",
  "surface_reset_risk": "none",
  "missing_full_artifacts": [],
  "synthesis_map": [
    {"claim_ids": ["claim-1", "claim-2"], "reason": "Why a later solver should combine them."}
  ],
  "ranked_route_portfolio": [
    {"route_id": "route-1", "rank": 1, "reason": "Evidence-based ranking."}
  ],
  "required_next_inputs": [],
  "new_math_performed": false,
  "created_at_utc": "<RFC3339-Z>"
}
```

## Reset assessment

Input schema: `math-research-route-reset-assessment-input/v1`.

```json
{
  "schema": "math-research-route-reset-assessment-input/v1",
  "explicit_user_ban": false,
  "consecutive_same_family_negative_attempts": 0,
  "consecutive_special_family_successes_without_bridge": 0,
  "strategy_overlap_detected": false,
  "same_family_attempt_count": 1,
  "same_family_ceiling": 2
}
```

The Harness returns `reset_required`, ordered triggers, and `minimum_distinct_cards`.

## Transition payloads

`ROUTE_RESET_TRIGGER`:

```json
{
  "schema": "math-research-transition-payload/v10",
  "assessment": {"schema": "math-research-route-reset-assessment-input/v1", "...": "complete assessment"},
  "occurred_at_utc": "<RFC3339-Z>"
}
```

`ROUTE_PORTFOLIO_ACCEPT`:

```json
{
  "schema": "math-research-transition-payload/v10",
  "portfolio": {"path": "runs/run-id/routes/portfolio-1.json", "sha256": "<sha256>"},
  "selected_route": {"path": "runs/run-id/routes/route-2.json", "sha256": "<sha256>"},
  "successor_capsule": {"path": "runs/run-id/continuity/capsule-g0007.json", "sha256": "<sha256>"},
  "occurred_at_utc": "<RFC3339-Z>"
}
```

The active capsule directive must match the recorded trigger assessment. The state records the first accepted trigger-event generation and the later portfolio-acceptance generation. The selected route must be byte-equivalent to one active/accepted portfolio card. The successor capsule must list it as live, preserve the target, complete terminal claims, required full artifacts, and forbidden families, and retire superseded live routes. After acceptance, close the predecessor with a ticket already bound to that route/capsule and start the one successor immediately; an intervening checkpoint or unrelated transition is invalid. One reset lifecycle can bind only one successor attempt.

The reset lifecycle also records the predecessor lead. The successor ticket must carry a distinct fresh lead in `new` mode with no previous-ticket pointer; predecessor close and successor start both recheck this separation.

`ATTEMPT_START`:

```json
{
  "schema": "math-research-transition-payload/v10",
  "attempt_id": "attempt-1",
  "attempt_kind": "route_execution",
  "ticket": {"path": "runs/run-id/tickets/ticket-1.json", "sha256": "<sha256>"},
  "occurred_at_utc": "<RFC3339-Z>"
}
```

`RESEARCH_CHECKPOINT`:

```json
{
  "schema": "math-research-transition-payload/v10",
  "capsule": {"path": "runs/run-id/continuity/capsule-g0003.json", "sha256": "<sha256>"},
  "references": [],
  "checkpoint_reason": "material_result",
  "occurred_at_utc": "<RFC3339-Z>"
}
```

`ATTEMPT_END` binds `disposition`, an `math-research-attempt-record/v10` pointer, evidence items, optional next-ticket pointer, and timestamp. The attempt record explicitly contains `verifier_completion`, which is null only when no verifier ran.

## Successor spec

Schema: `math-research-successor-spec/v10`. Bind predecessor identity/head/final status/envelope hashes/remaining budgets, successor identity/same envelope hashes/budgets, inherited cumulative counters, reason, initial ticket, initial capsule, initial route card, and timestamp.

The initial ticket must point to the same capsule and route card named by the spec. The capsule project/run IDs must equal the successor. The successor root must not already contain `project.json`.

## Live-v8 migration bootstrap

Schema: `math-research-v8-incremental-migration-bootstrap/v10`. Use exact keys
`schema,successor_run_id,initial_ticket,initial_capsule,initial_route_card,copy_artifacts,occurred_at_utc`.
Each copy entry has exact keys `source_path,target_path,sha256`; both paths are
project-relative, and the source is restricted to the frozen v8 predecessor. The
helper fills and rehashes the generated capsule/route/migration/freeze/envelope
inputs, while every other ticket input must already be listed with its exact target
path and hash. The ticket resource-envelope hash must equal the `inspect` result.
See [incremental migration](incremental-v8-to-v10-migration.md) for ordering and
freeze semantics.
# Asset registry transition

`ASSET_REGISTRY_UPDATE` is a non-counting v10 transition with exact payload:

```json
{
  "schema": "math-research-transition-payload/v10",
  "asset_index": {"path": "state/assets/index.json", "sha256": "<sha256>"},
  "occurred_at_utc": "2026-08-13T00:00:00Z"
}
```

The pointed `math-research-asset-index/v1`, registry, contribution ledger, export policy, and local artifacts must pass `math_research_assets.py validate`. A ticket or continuity capsule that formally depends on a research asset must bind registered artifact bytes, not an unregistered download or copied summary. See [research assets and private export](research-assets-and-export.md).
