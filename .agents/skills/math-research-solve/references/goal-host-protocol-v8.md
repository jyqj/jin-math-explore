# Direct-current-Goal-task protocol v8

This protocol is normative for every new `math-research-solve` run. The **current product Goal task is the only Goal Host**. It owns contract binding, counters, lifecycle decisions, publication, pause, and completion. Collaboration subagents are bounded workers; they never create, inspect, resume, pause, replace, or complete a Goal.

This design deliberately makes no promise that Goal state persists across isolated `codex exec` processes or tasks. New v8 research uses no Goal-owning CLI child, external dispatcher, synthetic heartbeat, or local substitute for the Goal control plane.

## 1. Goal identity and problem identity are separate

Keep both, but at different layers:

- immutable Contract bytes contain only `goal_binding_policy=direct-current-task/v8`, the rebind/successor rules, and `problem_statement_sha256`;
- the external `RUN_GENESIS`/`HOST_BIND` chain and generation-unique Goal-host/checkpoint files named by `project.json` contain the required Goal-objective hash derived from the Goal visible in the current task; the checkpoint also binds its immutable `host_binding_head`;
- those external records use `host_goal.thread_id_available`, `host_goal.thread_id`, and `host_goal.objective_raw_sha256`; when no stable task/thread ID is exposed they store `false`, `null`, and the required objective hash respectively.

A path-based raw Goal objective need not equal the mathematical statement. Goal rebind changes the external host-binding chain and increments `control_generation`; it does not rewrite an immutable Contract. Equality of project paths, prompts, markers, or hashes never proves that a different task owns the same Goal.

## 2. Fresh control-plane gate

The host calls `get_goal` immediately before each of these boundaries:

- run genesis or task rebind;
- `ATTEMPT_START` and dispatch of its collaboration tickets;
- `AUDIT_START` and dispatch of its three audit roles;
- authoritative publication, handoff, pause, closing, supersede, or completion.

Research or authoritative mutation requires `status=active` from a fresh call in this current task and the same raw-objective hash recorded for the run. If the platform returns a stable task/thread ID and the run recorded one, it must also match. Lack of an exposed stable ID does not block the legitimate current Goal. A tool parameter, project file, caller assertion, or child report is never a replacement for the fresh call.

`HOST_REBIND` is the sole exception to matching the old effective binding: its purpose is to replace that binding. It follows the special gate in section 8; after the cooperative guarded head transition, ordinary mutations must match the new effective binding.

Map a cancelled or absent Goal to `none`. After observing `none`, `paused`, `blocked`, or `complete`, the project is read-only. Do not create or recover a Goal automatically and do not finish a pending write after the non-active observation.

## 3. Genesis ordering

While the current Goal is active, perform one serialized preparation and activation sequence before any mathematical worker starts:

1. freeze and hash Contract v8;
2. create the run archive, append `RUN_GENESIS`, and append the initial external `HOST_BIND` with the current Goal objective hash and optional task/thread ID;
3. write an immutable candidate `state/generations/gNNNN/{checkpoint.json,goal-host-v8.json}` directory (checkpoint schema `math-research-checkpoint/v8`; numeric generation equals `control_generation`) and initial collaboration ticket with matching project, contract, run, Goal, counter, and problem bindings; use zero counters only for a fresh project and a verified inherited baseline for a legacy successor;
4. read the files back and verify their exact hashes and cross-file identities;
5. after a fresh Goal gate, invoke `scripts/commit_math_research_head_v8.ps1` for the cooperative guarded replacement of the single authoritative `project.json` head last so its `goal_host_state` and `active_checkpoint` path/hash/generation fields make those candidate files active;
6. call `get_goal` again immediately before `ATTEMPT_START`.

The immutable run-genesis file has schema `math-research-run-genesis/v8` and this exact seven-key shape:

```json
{
  "schema": "math-research-run-genesis/v8",
  "project_id": "stable-project-id",
  "control_generation": 1,
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001", "status": "not_started"},
  "host_binding": {"path": "runs/run-0001/host-bindings/host-bind-g0001.json", "sha256": "64 lowercase hex"},
  "host_goal": {"thread_id_available": false, "thread_id": null, "objective_raw_sha256": "64 lowercase hex"}
}
```

`RUN_GENESIS` consumes no attempt and no audit round. A partially written genesis is recovery-only and cannot be inferred to be executable from a human note.

## 4. Advisory host generation state

The immutable generation file named by `project.json.goal_host_state` (for example `state/generations/g0001/goal-host-v8.json`) is an ordinary, hash-bound advisory state file. It has the following exact top-level shape:

```json
{
  "schema": "math-research-goal-host-state/v8",
  "project_id": "stable-project-id",
  "control_generation": 1,
  "contract": {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": "64 lowercase hex"},
  "run": {"id": "run-0001", "path": "runs/run-0001", "status": "preparing"},
  "host_goal": {"thread_id_available": false, "thread_id": null, "objective_raw_sha256": "64 lowercase hex"},
  "problem_statement_sha256": "64 lowercase hex",
  "successor": null,
  "counters": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0, "audit_due": false},
  "current_ticket": {
    "id": "C1-T1",
    "path": "runs/run-0001/tickets/C1-T1.json",
    "sha256": "64 lowercase hex",
    "status": "frozen",
    "contract_initial_tickets_sha256": "64 lowercase hex",
    "counter_snapshot": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0},
    "source_event": null
  },
  "updated_at_utc": "RFC 3339 UTC timestamp"
}
```

For a fresh project, `successor` is exactly `null` and the counters are zero. For a legacy successor it is exactly:

```json
{
  "lineage": {"path": "state/successors/g0002.json", "sha256": "64 lowercase hex"},
  "inherited_artifact_index": {"path": "runs/run-0002/evidence/inherited-artifacts.json", "sha256": "64 lowercase hex"},
  "counter_budget_baseline": {"path": "state/successor-baselines/g0002.json", "sha256": "64 lowercase hex"}
}
```

The counters equal the independent inherited baseline rather than zero and can never fall below it. The activated `project.json.legacy_successor` pointer and all three summary pointers must agree exactly. On later generations, preserve the original lineage pointer byte-for-byte: its `control_generation` remains the successor activation generation, and only the ordinary current-head pointers advance.

`current_ticket` classification is determined by its lifecycle and `source_event`, not merely by run status. `source_event=null` means an initial ticket and requires exact deep equality to one Contract initial-ticket member, including role, inputs, policies, caps, outputs, dependencies, failure schema, Contract block hash, and counter snapshot. A non-null exact `{path,sha256}` source event means a derived solver/verifier/auditor ticket: it receives the same full schema/limit checks and is hash-bound by the exact ticket event below, but need not equal an initial Contract member. A verifier is always derived. `current_ticket` may be `null` only for closed/terminal state with no pending lifecycle object. The ticket file never contains its own hash or a `source_event` pointer.

The file is not a signature, capability, lease, authorization token, proof of a prior `get_goal` call, or proof of continuous Goal activity. Its hashes detect ordinary mismatch and bind records to one another. The model host must still perform the fresh control-plane gate.

The local startup script may parse the generation files strictly through `project.json` and return a read-only classification. A legacy project without v8 pointer fields is read only from its fixed historical paths. Startup must not execute a ticket, mutate counters, attest Goal activity, or turn any file into research authority.

## 5. Collaboration tickets

Before dispatch, freeze one ticket record containing:

- ticket, project, contract, run, cycle, and a non-authoritative planned lifecycle slot;
- role and exact decision question;
- bounded inputs and their hashes;
- allowed tools, source/network policy, filesystem scope, writable staging directory, tool/runtime/output-size caps, and stop rule;
- required artifact paths/schemas, required returned output hashes, evidence grade, and parent-ticket dependencies;
- a fixed `failure_return` schema covering status, failed step, reason, partial artifact hashes, and retry/reopen condition;
- the ledger/counter snapshot it was derived from; the Host stores the hash of the final ticket bytes only in generation state, the one-way derived-ticket event when applicable, and the later Attempt record.

The frozen ticket file has exact top-level keys `schema`, `project_id`, `control_generation`, `contract`, `run`, `cycle_id`, `contract_initial_tickets_sha256`, `counter_snapshot`, and `ticket`. Its schema is `math-research-frozen-ticket/v8`; `contract` is the full `{path,version,binding_sha256}` pointer, `run` is the full `{id,path,status}` pointer at issuance, `counter_snapshot` is the exact five-field issuance snapshot, and `ticket` is one complete machine-ticket object using the Contract v8 ticket schema. It contains no `source_event` member, preventing a ticket↔event hash cycle.

The exact cycle-policy keys additionally include nonempty unique `allowed_worker_tools`, positive `max_ticket_tool_calls`, and positive `max_ticket_output_bytes`. The global allowlist is exactly `apply_patch`, `collaboration.spawn_agent`, `collaboration.send_message`, `collaboration.wait_agent`, and `shell_command`, with `web__run` added only when `web_search=allowed` (and absent when denied). Each ticket's `allowed_tools` is a unique subset of that allowlist; it must not name Goal controls, controller/dispatcher/launcher/lease paths, `exec` controls, or a retired launcher route. Each ticket's tool-call and output-byte caps are no greater than the policy caps. A verifier ticket has exactly one extra `candidate_artifact={path,sha256}` member: it must equal exactly one `input_artifacts` member, have a nonempty list of exact `{ticket_id,path,sha256}` closed solver ticket-completion dependencies, and cannot self-reference or use a dependency hash as a candidate disguise. An initial source-event-null ticket is solver-only.

Every derived ticket has one immutable source event with this exact top-level schema:

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

The event's ticket ID, role, input-artifact pointers, and dependencies must deep-equal the referenced ticket's inner object; its Contract/run/counters must equal the issuance state. `current_ticket.source_event` binds the exact event path/hash. Initial tickets use `source_event=null`, are solver-only, and alone are deep-compared to a Contract initial-ticket member. Dependency pointers are immutable raw pointers to `math-research-ticket-completion/v8`, never tickets or staging output.

Tickets are immutable and hash-bound, **not cryptographically signed**. They grant no Goal authority and cannot broaden the Contract. A worker writes only its ticket staging area and returns proposed artifacts. The host validates every artifact and hash before one authoritative ledger commit. A retry requires a newly recorded ticket decision; no local one-use lease or dispatcher is implied.

The Host assigns the authoritative `attempt_id` only at `ATTEMPT_START` and then records the ticket-to-attempt binding. Genesis and the initial ticket must not preclaim an attempt ID. In particular, the builder's `source_event=null` initial solver ticket is a `preparing` seed only and is never a worker-dispatch ticket.

A solver result that needs mathematical verification produces a separate derived verifier ticket. That verifier ticket has a different ID/hash/role/output path, a non-null source event, and one exact `candidate_artifact` bound to exactly one input artifact; it cannot reuse or self-verify the solver ticket.

## 6. Attempt, audit, and publication lifecycle

Every generation publishes one exact `math-research-project-event/v8` with keys `schema,project_id,control_generation,event_id,event_type,updated_at_utc,previous_event_sha256,contract,run,counters,referenced_artifacts`; its previous hash chains from the old project-event head (`null` only for first v8 activation), and its file hash is selected by the new project head/checkpoint. The event-type closed set and nested shapes are fixed by the archive protocol.

This project-event closed set is distinct from run-ledger/domain event labels. `PUBLICATION`, `COMPLETION_CANDIDATE`, `SUPERSEDE`, and `CLOSE` may occur only as ordinary run-ledger artifacts referenced by the applicable canonical project event; none is a legal `project_event_head.event_type` or independent mutation authority.

Before every `ATTEMPT_START`, including a non-interval attempt, the old counters must satisfy `attempt_count + 1 <= attempt_budget` and `total_round_count + 2 <= total_round_budget`, reserving one round for a mandatory terminal audit if the attempt finds a candidate. In the candidate generation, the active host registers a fresh attempt ID, consumes the attempt round, and replaces the preparing seed with a newly frozen active solver ticket and non-null `math-research-ticket-event/v8`; the state pointer, ticket envelope, and event all bind the post-start counters. Only after a fresh Goal gate, head activation, and read-back does it dispatch that derived solver ticket. Any claimed result is checked through a separate verifier ticket/artifact. At every `ATTEMPT_END`, `referenced_artifacts[0]` is one immutable `math-research-attempt-outcome/v8` with exact keys `schema,project_id,contract,run,attempt_id,outcome,candidate,verifier_completion,completed_at_utc`; `outcome` is exactly `candidate_found|no_candidate|inconclusive|failed|awaiting_input`. Noncandidate outcomes have null candidate/verifier completion. `candidate_found` requires the current derived verifier ticket, the same immutable candidate pointer, and an exact PASS verifier result or closed verifier completion whose ticket ID, Contract/run, and candidate all agree. Verifier schemas have no attempt ID: the outcome value is only safe-ID checked and must differ from the current verifier ticket ID, while Attempt-record↔outcome attempt binding remains a Host-maintained, unmechanized residual. The host first writes proposed records to non-authoritative staging, then performs a fresh Goal gate, atomically publishes each final file, and invokes `scripts/commit_math_research_head_v8.ps1` for exactly one authoritative `project.json` head transition last. There is no claim of multi-file atomicity.

When an audit is due, no next attempt may start. The host performs a fresh Goal check, freezes one evidence snapshot, and dispatches `skeptic_quantifiers`, `skeptic_strategy`, and `theory_tool_scout` as separate collaboration subagents. The exact cycle-audit plan keys are `schema,project_id,contract,run,audit_kind,candidate,snapshot,active_ticket,tickets,started_at_utc`: terminal requires the immutable candidate from the locked `candidate_found` Attempt outcome, while scheduled/early require null. Plan, summary, and all three reports bind that same value. If a candidate is found on an interval or final attempt, preserve `audit_due=true` but run the terminal audit first; its single `AUDIT_END` consumes/clears the gate rather than scheduling a second audit. Auditors inspect only frozen evidence and cannot add proof work.

Publication is authoritative mutation. Therefore the host performs a fresh Goal check immediately before each publication, including AttemptEnd, AuditEnd, handoff, pause, closing, and completion-candidate publication.

## 7. Pause, completion, and closing order

An intentional project pause is **not** a product Goal mutation. Only `attempt_running` or `auditing` may pause. While the Goal is active: stop new dispatch, stage any abort intent non-authoritatively, perform a fresh Goal gate, publish and read back `PAUSE` plus exact resume capsule/checkpoint/counters/gates/handoff through the cooperative guarded project-head transition, then return and stop dispatching. A paused head may next publish only `RESUME` or an exact capsule-preserving `HOST_REBIND`; `CHECKPOINT_COMMIT` and every other event fail closed. Do not call `update_goal` for pause and never use `blocked` as a pause surrogate.

Completion is separate:

1. require one exact terminal `math-research-cycle-audit-summary/v8`, linked to its immutable `AUDIT_START` plan/history and locked Attempt outcome, and exactly three ordered reports for `skeptic_quantifiers`, `skeptic_strategy`, and `theory_tool_scout`; plan, summary, and every `math-research-cycle-audit-report/v8` bind the same candidate/snapshot and every report is exactly `PASS` with `new_math_performed=false`;
2. terminal `AUDIT_END` publishes that summary as its sole `referenced_artifacts[0]`; startup exposes the audited state as `goal_host_completion_ready_to_publish`;
3. only after the fresh active Goal publication gate may the Host persist/activate/read back `COMPLETION_READY` plus `completion_ready=true` and `pending_goal_update=true`; terminal FAIL/INCONCLUSIVE is never completion-ready, and a `HOST_REBIND` before or after audit must retain the exact Attempt outcome or terminal summary pointer/history respectively;
4. call `get_goal` again immediately before `update_goal(status=complete)`;
5. call it only if the final check is still active and matching.

The two checkpoint flags are valid only as both false or both true. Once both are true, the project/head is permanently read-only: do not clear either flag, resume, audit, publish, or rewrite closing state. Startup returns `goal_host_completion_pending`; after a fresh active/matching Goal check the only allowed control action is `update_goal(status=complete)`, with no project write. A complete Goal becomes `goal_host_closed_review`; any other non-active Goal retains the pending state read-only. Budget exhaustion, a partial theorem, or an unresolved open problem is not completion.

If the host first observes `none`, `paused`, `blocked`, or `complete`, it performs no project mutation. `blocked` may be set only when the platform's independent repeated-blocker rule is actually satisfied; it is never a convenience stop state.

## 8. Explicit v8 rebind only

A new task may take ownership of an existing **v8** run only through this special gate:

1. the user explicitly revokes the old binding, starts a new Goal, and authorizes rebind/continuation for the exact project;
2. the new Goal is freshly observed active in the current task; its raw objective need not equal the obsolete binding;
3. the authoritative head shows no unfinished commit; user revocation is sufficient retirement authority, so do not query the old task;
4. immutable Contract target/quantifiers/assumptions/permissions/external effects remain unchanged; otherwise fail closed/read-only pending a separately implemented and authorized `RUN_SUCCESSOR` protocol—confirmation alone is not an executable transition;
5. in one new generation, stage one exact-schema `math-research-host-binding/v8` record with `event_type=HOST_REBIND`, `prior_host_binding` equal to the old head, `retirement={authority:"user-explicit-revocation",reason:<nonempty>}`, the unchanged Contract/run identity, and the new `host_goal`, plus generation checkpoint/state and `control_generation += 1`;
6. verify them and, after the special fresh Goal gate, invoke `scripts/commit_math_research_head_v8.ps1` for the cooperative guarded project-head transition last.

The cancelled/absent old host is neither queried nor required to prewrite retirement. The new Host records retirement inside the single `HOST_REBIND` object under the user's explicit revocation authority; there is no separate `HOST_RETIRE` event. After the head transition, ordinary mutations must match the new effective binding. Rebind never resets attempts, audits, rounds, failures, or route history. Legacy runs never use `HOST_REBIND`.

## 9. Legacy terminal fuse and binding retirement

Prompt v3-v7 and their historical control bundles remain frozen legacy material. **All legacy Goal bindings are retired**, regardless of whether the old state appears terminal. Startup v3 classifies them read-only before any route choice. If a legacy primary or backup state consistently records `goal_continuity_failed`, the exact marker `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`, or a failed child Goal with `persistence_verified=false`, classify the old run as `goal_continuity_terminal` and return only `stop_no_retry_preserve_run`.

Do not Tick, Resume, recreate a Goal, delete or rewrite the manifest, reset counters, repeat compatibility migration, substitute caller `GoalStatus=active`, or silently convert the run to v8. The no-op applies to the old run and is never overridden.

## 10. Additive legacy successor

The user may explicitly create a **new active Goal** to continue the same research project. This creates a new v8 run; it does not recover, rebind, or resume any legacy Goal.

The current Host may perform the successor transaction only when the explicit new Goal preserves a normalized effective predecessor envelope: target/domain/quantifiers/dependencies/assumptions/completion, model/reasoning, privacy/external effects, and all agent/runtime/attempt/audit/round/cumulative ceilings remain equivalent, and no non-control permission or resource expands. The effective values come from the frozen predecessor Contract/base manifest plus every strict hash-cross-bound recorded amendment in order, not from whichever prose or stale file is convenient. Legacy HMAC fields are only self-consistency evidence; this protocol does not authenticate them. Legacy child-Goal/launcher/dispatcher/lease/migration/control-receipt authority must be retired and mapped to direct-current-task/v8 + bounded collaboration + the guarded head helper; that prescribed control-path replacement is the sole permitted safe contraction and is not an envelope mismatch. A same-project `/goal $math-research-solve … continue until proved or disproved` supplies launch intent for this nonexpanded transition; never request repeated confirmation, hashes, or commands. The fresh current Goal, not an old HMAC or receipt, supplies authority. The one prescribed legacy-to-v8 Contract/run is part of this `LEGACY_SUCCESSOR`; any other envelope difference or any additional Contract/run transition beyond it is planning-only/read-only pending a separately implemented and authorized `RUN_SUCCESSOR`. Confirmation alone does not permit such an additional genesis or head transition.

While the new Goal is active:

1. keep startup's old-run result unchanged (`goal_continuity_terminal -> stop_no_retry_preserve_run` or `legacy_execution_unsupported -> fail_closed_read_only_diagnosis`);
2. copy the exact predecessor `project.json` bytes to an immutable successor snapshot whose hash becomes the activation transition's expected-old hash, then inventory the immutable predecessor and freeze a complete inherited-index manifest covering the problem statement, verified partial results, all attempts, failures, evidence, routes, audits, handoff, source/computation artifacts, cumulative counters, spent budgets, and remaining ceilings;
3. preserve every artifact and evidence grade; unverified material remains explicitly unverified and is not promoted;
4. the model Host—not a script—first determines that the natural-language current Goal is a same-target/nonexpanded continuation. After a fresh active-Goal check, invoke the production `scripts/build_math_research_legacy_successor_v8.ps1` with the exact raw Goal objective/raw UTF-8 hash and optional exposed stable ID; the builder uses that raw text only for external host binding. Require its exact JSON result, `built=true`, expected-old/new agreement, and no-HMAC/no-Goal-authority trust label. It derives/freezes the hash-bound effective predecessor envelope and retired-control-path mapping, mechanically preserves the predecessor semantic-section hashes/current effective configuration, freezes Contract v8 with `run_origin=legacy_successor`, the independent predecessor-derived counter/budget-baseline hash, direct-current-task binding policy, and path/hash bindings to those two artifacts; the lineage—not the Contract—binds predecessor/index/successor hashes, and the actual new Goal identity appears only in external genesis/host-binding records and generation state;
5. create and verify the new run `RUN_GENESIS`, successor state, checkpoint, and immutable `state/successors/gNNNN.json` lineage entirely as non-authoritative staged/unreferenced material; its counters start at the inherited baseline;
6. require every legacy host/control binding obsolete, verify the normalized envelope, the mandatory safe contraction, and no unfinished authoritative commit outside the lineage; publish the verified successor files without changing the active project head, include the effective-envelope and mapping pointers in the first `LEGACY_SUCCESSOR` project event's `referenced_artifacts`, and finalize the immutable `state/successors/gNNNN.json` lineage binding the predecessor-head snapshot, predecessor run/manifest hashes, new Contract/run/genesis/host-bind hashes, complete inherited index, independent baseline, and next generation; the lineage/state/checkpoint exact key sets do not grow;
7. activate only by `scripts/commit_math_research_head_v8.ps1`, using the predecessor snapshot hash/generation as expected-old and making the lineage plus already-verified successor files reachable; use a valid nonnegative legacy `control_generation + 1`, exactly generation 1 only when the key is absent, and fail closed when a present key is malformed; publish `CURRENT.md` and other human views afterward;
8. fresh `get_goal` again before the first new `ATTEMPT_START`.

The builder is Goal-agnostic, does not authenticate legacy HMACs, and never replaces `project.json`. The old run, manifests, and snapshotted old project head are byte-read-only. The staged lineage is non-authoritative; after another fresh active-Goal check, `LEGACY_SUCCESSOR` becomes activated only through the final cooperative guarded head transition. It supersedes the predecessor only in the new project index; it never edits old status or pretends old Goal continuity succeeded. If any step fails before that transition, live old active pointers remain unchanged and all successor material is staged/unreferenced recovery-only. Activation cannot reset IDs, counters, budgets, failures, evidence, or route history.

The head helper is Goal-agnostic and grants no authority. The model Host must complete the applicable fresh Goal/special rebind/successor gate first. It provides a **cooperative guarded CAS under the sole-writer/helper protocol**: a named mutex, expected-old hash/generation check, strict candidate/pointer validation, and same-directory flushed atomic replacement serialize cooperating writers, not arbitrary non-cooperating processes; only the final head-file replacement is atomic.

## 11. Honest boundary

Local hashes, ledgers, checkpoints, and startup output provide ordinary file integrity and recoverable bookkeeping. They do not cryptographically attest model behavior or Goal control-plane history. Product Goal state is known only from a fresh call in the current task; everything else is advisory evidence.
