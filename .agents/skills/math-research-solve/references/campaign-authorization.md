# Direct Goal campaign boundary

This reference defines long-running work for Contract v8. A campaign is a sequence of lifecycle commits made by the **same current product Goal task**. It is not an external dispatcher, scheduler, service, synthetic heartbeat, or chain of isolated `codex exec` processes.

Historical dispatcher and launcher artifacts remain frozen legacy evidence only. They are not a backend for a new v8 campaign and cannot repair failed child Goal continuity.

Legacy-only compatibility label: the historical `scheduler host`, `child`, and `manifest` are separate frozen records. This sentence preserves old structural interpretation and grants no execution or Goal-continuity authority.

## Authorization envelope

Before launch, freeze one semantic envelope binding:

- project, canonical mathematical target, domain, quantifier order, dependencies, assumptions, and completion standard;
- Contract v8 bytes and `contract_binding_sha256`;
- `goal_binding_policy=direct-current-task/v8` in immutable Contract bytes; keep the actual current Goal objective hash and optional stable task/thread ID only in the external run/host-binding state, separate from the problem hash;
- model/reasoning and every agent/runtime/attempt/audit/round/cumulative ceiling;
- approval/source/web/network/filesystem/tool/private-data policies and external effects;
- launch intent.

The **normalized frozen research envelope** means that whole list. For a legacy successor it is derived from the frozen predecessor Contract/base manifest plus every strict hash-cross-bound recorded amendment in order and bound to an immutable effective-envelope artifact. Legacy HMAC fields are not authenticated and supply no authority. Research semantics, privacy/external effects, cumulative ceilings, and every non-control permission must remain equivalent. Retiring legacy Goal/launcher/dispatcher/lease/control-receipt authority and replacing it with direct-current-task/v8 + bounded collaboration + the head helper is a mandatory safe contraction, not a permission expansion. The user need not echo an internally computed hash. A semantic authorization covers only that envelope and does not bypass platform review. Any material expansion requires new semantic authorization and remains read-only in this release because `RUN_SUCCESSOR` is not implemented.

When the frozen envelope uses `approval_mode=approve_for_me`, the current Host submits each necessary narrow in-scope `require_escalated` request directly to `managed auto-review`. A denial permits only a materially safer in-scope alternative or an honest stop; it never permits bypass.

## Direct-host lifecycle

The current Goal task performs all authoritative transitions:

1. call `get_goal` and require the intended active Goal;
2. freeze Contract v8 and exact campaign envelope;
3. persist genesis, external `HOST_BIND`, generation-unique Goal-host state/checkpoint, and the initial hash-bound ticket;
4. verify all cross-file identities/hashes and, after the fresh Goal gate, invoke `scripts/commit_math_research_head_v8.ps1` for the cooperative guarded single `project.json` head transition last;
5. call `get_goal` again before `ATTEMPT_START` or `AUDIT_START`;
6. spawn bounded collaboration subagents only;
7. validate their proposed artifacts and commit one authoritative lifecycle event;
8. call `get_goal` again before publication, handoff, pause, closing, or completion.

No child calls Goal controls. No local script turns project files into Goal authority. No external process automatically advances the campaign.

## Continuation and interruption

Conversation compaction within the same active Goal task may use the durable archive as its memory. A later turn first runs startup v3 read-only, then performs a fresh `get_goal` check before mutation.

After observing `none`, `paused`, `blocked`, or `complete`, all project/controller/research state is read-only. A cancelled Goal maps to `none`. A timer or monitoring task may report read-only status but must not dispatch work or claim to be a heartbeat of the original Goal.

For an intentional pause while active, only `attempt_running` or `auditing` may publish `PAUSE`; fresh-check Goal, persist/activate/read back its exact resume capsule/checkpoint/handoff, stop dispatching, and return. A nonrunning pause fails closed; a paused head may next publish only `RESUME` or an exact capsule-preserving `HOST_REBIND`, never `CHECKPOINT_COMMIT` or any other event. Do not mutate the product Goal or use `blocked` as pause. On resume the capsule preserves the frozen ticket/lifecycle/counters and `audit_due` follows only the frozen gate. Completion flags are valid only as both false or both true. Completion alone persists both true, permanently freezing project/head mutation, then startup/classification uses `goal_host_completion_pending` and the Host fresh-checks immediately before `update_goal(status=complete)`. Only active/matching may call it, with no project write; any non-active state remains read-only pending, while complete becomes closed review. Never clear flags, resume, audit, or republish. `blocked` is reserved for the platform's independently satisfied repeated-blocker rule.

## Explicit new-task v8 rebind

A different task may continue an existing v8 run only through the special rebind gate: user-explicit revocation of the old binding plus new Goal/rebind authorization, freshly active new Goal, no unfinished commit, and unchanged Contract semantics/permissions. User revocation is sufficient; do not query the old task. The new Host stages one exact-schema `HOST_REBIND` with the old head in `prior_host_binding` and `{authority:"user-explicit-revocation",reason:<nonempty>}` in `retirement`, then performs the cooperative guarded project-head transition in one incremented generation; no separate `HOST_RETIRE` exists. The new raw objective need not equal the obsolete binding. Preserve Contract/problem bytes, counters, route history, failures, evidence, and cumulative consumption. A changed target, quantifier, permission, external effect, Contract, or run identity fails closed/read-only pending an implemented and authorized `RUN_SUCCESSOR`; confirmation alone is insufficient.

## Tickets and workers

Tickets are frozen, hash-bound collaboration records. They are not cryptographically signed, not capabilities, and not one-use process leases. Each ticket fixes one role, bounded question, inputs, tools, staging path, resource cap, stop rule, and expected output. The exact cycle policy carries a nonempty unique worker-tool allowlist and positive tool-call/output-byte caps; every ticket uses a unique subset, cannot invoke Goal/control/dispatcher/launcher/lease/`exec`/retired routes, and cannot exceed those caps. A verifier is derived only, has nonempty dependencies, and has one exact candidate-artifact pointer equal to one input artifact. A worker cannot broaden authority or publish project state. The host validates results before commit.

## Budget and audit boundary

- `ATTEMPT_START` consumes one attempt and one total round.
- A complete three-role `AUDIT_START` consumes one total round.
- Every new attempt, including one that does not hit the interval, must reserve a possible terminal audit: before `ATTEMPT_START`, the old counters satisfy `attempt_count + 1 <= attempt_budget` and `total_round_count + 2 <= total_round_budget`.
- When `audit_due=true`, no next attempt starts.
- Retries do not create replacement runs or reset counters.
- This release has no v8 rollover/new-Contract/new-run transition. Any such request is planning-only/read-only pending a separately implemented and authorized `RUN_SUCCESSOR`; never reset counters or invoke the head helper for it.

The campaign is not an unconditional promise to run forever: it stops with a verified proof/disproof or when its frozen inherited attempt/round/resource envelope is exhausted. It never silently extends that envelope.

## Legacy terminal circuit breaker

Startup v3 classifies legacy records before any recovery proposal. If a legacy record consistently contains `goal_continuity_failed`, `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`, or failed child Goal continuity with `persistence_verified=false`, return:

```text
goal_continuity_terminal -> stop_no_retry_preserve_run
```

Caller `GoalStatus=active`, a marker, a different Goal, compatibility reader success, or an old scheduler policy cannot override the fuse. Do not Resume, Tick, create a child Goal, rerun migration, rewrite the manifest, or reset counters. Preserve the whole archive.

Every legacy Goal binding is retired. The fuse/no-op remains final for the old run, but an explicitly user-created new active Goal may start an additive v8 successor in the same project only when the normalized effective predecessor envelope is equivalent under the mandatory retired-control-path contraction and has no permission/resource expansion. A same-project `/goal` request to continue until the fixed problem is proved or disproved is launch intent for that nonexpanded envelope; never ask the user to repeat confirmation, hashes, or commands. The current active Goal is authority; old HMACs, receipts, manifests, and caller status are evidence only. Any other difference or expansion remains planning-only/read-only pending `RUN_SUCCESSOR`; a newly confirmed Contract alone is not executable.

A legacy `rollover=false` or `rollover=never` clause forbids automatic or same-run rollover only. It does not forbid a user-explicit new Goal plus the prescribed additive Contract v8 successor within the normalized same-target/nonexpanded research envelope: that action neither modifies nor continues the old run, all predecessor consumption is inherited rather than reset, and retired legacy control authority is replaced only by the narrower v8 control path. Any other envelope difference is read-only pending `RUN_SUCCESSOR`, not made executable by confirmation.

After a fresh active-Goal check, successor preparation uses the production `scripts/build_math_research_legacy_successor_v8.ps1` staging helper with the exact raw current objective/hash and optional exposed stable ID. Require its exact result schema, `built=true`, expected-old/new agreement, and explicit no-HMAC/no-Goal-authority trust label. It snapshots exact old `project.json` bytes, inventories the predecessor problem, verified partial results, attempts, failures, evidence, routes, audits, handoff, all intermediate artifacts, cumulative counters, spent budgets, and remaining ceilings, deterministically derives the immutable effective-envelope and retired-control-mapping artifacts, and stages immutable lineage, new Contract/run/`RUN_GENESIS`/external host binding, and generation state/checkpoint. The Contract binds both new artifacts by path/hash and the first `LEGACY_SUCCESSOR` project event lists them as raw `referenced_artifacts`; lineage/state/checkpoint exact key sets remain unchanged. The builder never replaces `project.json`. A deterministic exact-schema build intent is staged under `state/build-intents/gNNNN.json`; atomic no-overwrite write-or-verify recovery may reuse matching staging or fill only missing bytes, returning `reused_staging_ready_for_goal_gated_commit`, while any mismatch fails closed. After a second fresh Goal gate only `scripts/commit_math_research_head_v8.ps1` may perform the cooperative guarded activation transition using the snapshot hash/generation as expected-old. Before it, the old head remains active and the successor is unreferenced. Later generations preserve the activated lineage pointer/activation generation and do not reuse the predecessor snapshot as their expected-old. Both helpers are Goal-agnostic and cannot expand authorization. No old manifest byte, counter, or evidence grade changes.

## Honest guarantees

The campaign archive provides ordinary hash-bound integrity, monotone accounting, and inspectable handoff. Its head transition is cooperative under the sole-writer/helper protocol and does not exclude arbitrary non-cooperating writers. It does not prove a prior model tool call, continuous Goal activity, runtime isolation, or delivery by an external scheduler. Those boundaries must never be advertised as implemented.
