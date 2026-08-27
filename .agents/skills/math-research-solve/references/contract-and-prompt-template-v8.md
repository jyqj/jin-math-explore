# Research Contract v8 与 direct Goal-host 模板

本文件只用于生成新的 **Math Research Goal-Host Contract v8**。当前 product Goal task 是唯一 Goal Host；collaboration child 只执行冻结票据，不触碰 Goal 控制。

方括号字段必须被替换、删除，或明确写为 `unknown` / `requires user decision`。若未知字段影响数学真值、完成标准、权限或资源上限，合同不得确认或启动。

Prompt v3-v7、Startup Router v2 和相关历史 bundle 只是 legacy labels；不能静默升级为 v8。档案规范见 [research-project-archive.md](research-project-archive.md)，Goal ownership 见 [goal-host-protocol-v8.md](goal-host-protocol-v8.md)。

## 1. 生成规则

1. 先固定对象域、量词顺序、依赖关系、边界/例外、允许假设和完成证书。
2. Immutable Contract 只写 `goal_binding_policy=direct-current-task/v8`、rebind/successor 规则与 `problem_statement_sha256`。实际 `host_goal.objective_raw_sha256` 和可选 `host_goal.thread_id` 只写外置 `RUN_GENESIS`/`HOST_BIND` chain 与 generation state/checkpoint；checkpoint 还绑定 immutable `host_binding_head`。不得因 rebind 改写 Contract bytes。
3. 对完整 ContractFile 先 CRLF→LF，再算 `contract_binding_sha256`。为避免自引用，该 hash 只写入项目/run/advisory state，不写回 ContractFile。
4. `cycle_policy_sha256` 与 `initial_tickets_sha256` 按本文的 exact-block 算法生成。
5. 模型、reasoning、approval mode、web policy、子代理上限、runtime、attempt/audit/round 预算都必须由本次用户授权或同范围活动信封明确给出；模板不提供静默默认。
6. 得到 launch intent 后，当前 active Goal task 完成 genesis、外置 `HOST_BIND`、generation-unique advisory/checkpoint 和 initial ticket 的落盘/回读，fresh gate 后用 `scripts/commit_math_research_head_v8.ps1` 按 sole-writer/helper 协议执行 cooperative guarded 单一 `project.json` head transition，再 fresh `get_goal` 后启动第一次 attempt。该 helper Goal-agnostic，不证明 Goal 或扩权，也不排除任意 non-cooperating writer。
7. 不创建 Goal-owning CLI child，不声明外部 dispatcher、synthetic heartbeat 或跨 `codex exec` Goal persistence。

`project_identity_sha256` 是 genesis 冻结并跨文件绑定的 opaque 64-hex project identity；本版本没有定义或验证“绝对路径 hash”算法，不得用它声称同名复制目录就是原项目。Canonical path containment 与 fresh Goal/authorization gate 仍需独立满足。

## 2. Research Contract vN 正文模板

```markdown
# Research Contract vN

## Project and exact target

- project_id: [stable project id]
- project directory: [canonical absolute path]
- canonical problem statement: [complete statement]
- domain and quantifier order: [exact]
- dependencies between variables/choices: [exact]
- boundary cases and exclusions: [exact]
- allowed assumptions: [explicit list]
- problem_statement_sha256: [64 lowercase hex]

## Truth and completion standard

- target kind: [proof | disproof | construction | classification | decision]
- global resolution means: [exact certificate]
- accepted evidence grades: [proved / verified computation / ...]
- computation-only settlement allowed: [yes/no and exact certificate]
- sources required for imported claims: [primary-source policy]
- what does not count as completion: [special family, bounded search, heuristic, consensus, missing bridge, ...]

## Current Goal ownership

- sole Goal Host: current product Goal task
- goal_binding_policy: direct-current-task/v8
- Goal identity storage: external RUN_GENESIS/HOST_BIND chain and generation state/checkpoint, with checkpoint also binding their immutable head; not Contract bytes
- child Goal operations: forbidden
- v8 new-task continuation: user explicitly revokes old binding and authorizes new Goal; new Host stages one exact-schema HOST_REBIND with prior_host_binding=old head and retirement={authority:user-explicit-revocation, nonempty reason}, no unfinished commit, control_generation increment; Contract/problem/run identity unchanged; no separate HOST_RETIRE; do not query old task
- legacy continuation: all old Goal/control bindings obsolete; explicit new Goal may create additive LEGACY_SUCCESSOR and a new v8 run only after normalized same-target/nonexpanded envelope verification and mandatory retired-control-path contraction
- cancelled or absent Goal: map to none and remain read-only

## Permissions and external effects

- approval_mode: [approve_for_me | never]
- filesystem scope: [exact]
- private-data scope: [exact]
- web/source policy: [allowed/denied plus limits]
- network destinations: [exact or none]
- external messages/deployments/purchases/deletion: [exactly allowed or forbidden]
- computation tools and versions: [exact]
- platform approvals remain mandatory: yes

## Resource envelope

- model: [explicit]
- reasoning_effort: [explicit]
- max concurrent collaboration subagents: [1..16]
- max_runtime_minutes per segment: [0 or positive integer]
- attempt_budget: [positive integer]
- audit_interval_attempts: [positive integer]
- total_round_budget: [positive integer]
- max preregistered repairs per attempt: 1
- cumulative campaign ceiling and rollover rule: [explicit]

## Cycle and audit policy

- ATTEMPT_START consumes one attempt and one total round.
- Complete three-role AUDIT_START consumes one total round.
- Before every ATTEMPT_START, including a non-interval attempt, require the old counters to satisfy `attempt_count + 1 <= attempt_budget` and `total_round_count + 2 <= total_round_budget`, reserving one mandatory terminal-audit round.
- The attempt that reaches the audit interval may finish; no next attempt starts before AUDIT_END.
- Every complete audit resets attempts_since_last_audit only; global counters never reset.
- Audit roles: skeptic_quantifiers, skeptic_strategy, theory_tool_scout.
- Audit performs no new proof search, computation, repair, or route invention.

## Collaboration-ticket policy

- ticket nature: immutable and hash-bound; not cryptographically signed; no Goal authority
- role scope: one exact bounded decision question
- required binding: project, contract, run, cycle, non-authoritative planned lifecycle slot, inputs/hashes, exact `{ticket_id,path,sha256}` dependencies, ledger/counters
- required limits: allowed tools, source/network policy, filesystem scope, unique writable staging directory, runtime/tool-call/output-size caps, stop rule
- required outputs: paths, schemas, returned hashes, evidence grade, dependencies, and fixed failure_return schema
- verifier: derived independent ticket with distinct ID/hash/role/path, nonempty completion dependencies, and exact `candidate_artifact` bound to one input hash
- worker output: proposed artifacts only; host validates before one authoritative head commit
- frozen wrapper/event: ticket file omits its own hash and `source_event`; state stores ticket path/hash plus nullable source-event pointer; initial ticket alone deep-equals a Contract member, while a derived ticket is one-way hash-bound by an exact ticket event and receives full schema/limit validation
- initial ticket ID: [ID]

## Pause, return, and completion

- fresh get_goal required before attempt, audit, publication, handoff, pause, closing, rebind, completion
- pause ordering: only `attempt_running` or `auditing` may pause; fresh gate then persist/activate/read back a PAUSE resume capsule/checkpoint/handoff and return; a paused head may next use only RESUME or exact capsule-preserving HOST_REBIND, while CHECKPOINT_COMMIT/other events fail closed; nonrunning pause fails closed, no update_goal, and blocked is not a pause surrogate
- audited completion ordering: a terminal cycle-audit summary is first verified; startup returns `goal_host_completion_ready_to_publish`, then only a fresh active Goal gate may publish `COMPLETION_READY` and durable flags, after which a further fresh gate may call update_goal(status=complete)
- completion checkpoint: flags only false/false or true/true; once true/true never clear, resume, audit, or publish; startup class is goal_host_completion_pending until Goal complete becomes closed review
- non-active observation: no project mutation; report last durable state read-only
- completion: same frozen candidate receives all three terminal-audit PASS reports
- non-complete return: strongest verified partial result, exact gaps, counters, evidence grades, reopen conditions

## Cycle 1 initial tickets

[For every ticket give ID, role, attempt kind, method family, falsifiable decision question, bounded inputs and hashes, search domain, success/stop signals, exact permissions, explicit resource caps, output files, evidence grade, exact `{ticket_id,path,sha256}` dependencies, and reopen condition. Keep this prose identical in meaning to the machine block. Initial source-event-null tickets must have role solver.]
```

## 3. 完整 ContractFile 骨架

以下 code block 是生成器骨架。替换全部 placeholder，并保证正文与两个 machine blocks 语义一致。

```markdown
# Math Research Goal-Host Contract v8
<!-- math-research-goal-host
schema: 8
goal_host_protocol: direct-current-task/v8
goal_binding_policy: direct-current-task/v8
goal_rebind_policy: external-host-bind-chain/v8
contract_version: vN
project_archive_schema: math-research-project/v8
project_id: [stable project id]
project_directory_name: [direct project directory leaf]
project_identity_sha256: [64 lowercase hex]
model: [model]
reasoning_effort: [minimal|low|medium|high|xhigh|max|ultra]
approval_mode: [approve_for_me|never]
web_search: [allowed|denied]
audit_interval_attempts: [positive integer chosen for this contract]
attempt_budget: [positive integer chosen for this contract]
total_round_budget: [positive integer chosen for this contract]
max_child_agents: [1..16]
max_total_agents: [max_child_agents + 1 host]
max_runtime_minutes: [0 or positive integer]
run_origin: [fresh|legacy_successor]
inherited_counter_budget_baseline_sha256: [null|64 lowercase hex]
problem_statement_sha256: [64 lowercase hex]
cycle_policy_sha256: [64 lowercase hex]
initial_tickets_sha256: [64 lowercase hex]
-->

<!-- math-research-cycle-policy
{
  "schema_version": 3,
  "protocol": "math-research-cycle-policy/v3",
  "total_round_budget": -1,
  "attempt_budget": -1,
  "audit_interval_attempts": -1,
  "max_route_family_attempts_per_cycle": 2,
  "max_repair_batches_per_attempt": 1,
  "allowed_worker_tools": [
    "apply_patch",
    "collaboration.spawn_agent",
    "collaboration.send_message",
    "collaboration.wait_agent",
    "shell_command",
    "web__run"
  ],
  "max_ticket_tool_calls": 32,
  "max_ticket_output_bytes": 8388608,
  "audit_roles": [
    "skeptic_quantifiers",
    "skeptic_strategy",
    "theory_tool_scout"
  ]
}
-->

<!-- math-research-initial-tickets
{
  "schema_version": 3,
  "cycle_id": "cycle-1",
  "tickets": [
    {
      "ticket_id": "C1-T1",
      "role": "solver",
      "planned_lifecycle_slot": "first_attempt",
      "route_id": "replace_with_stable_route_id",
      "route_fingerprint_sha256": "replace_with_controller_computed_lowercase_sha256",
      "attempt_kind": "route_execution",
      "route_family_id": "replace_with_route_family_id",
      "mechanism_id": "replace_with_mechanism_id",
      "bottleneck_id": "replace_with_bottleneck_id",
      "decision_question": "replace_with_falsifiable_question",
      "input_artifacts": [
        {"path": "replace_with_project_relative_path", "sha256": "64 lowercase hex"}
      ],
      "search_domain": "replace_with_bounded_search_domain",
      "success_signal": "replace_with_inspectable_success_signal",
      "stop_signal": "replace_with_exact_stop_signal",
      "allowed_tools": ["replace_with_exact_tool_name"],
      "source_network_policy": {
        "web": "replace_with_allowed_or_denied",
        "allowed_source_classes": ["replace_with_exact_source_class"],
        "network_destinations": []
      },
      "filesystem_scope": {
        "read_paths": ["replace_with_project_relative_path"],
        "writable_staging_path": "runs/[replace-with-run-id]/staging/C1-T1/solver-1"
      },
      "resource_caps": {
        "child_agents": -1,
        "tool_calls": -1,
        "runtime_minutes": -1,
        "max_output_bytes": -1
      },
      "dependencies": [],
      "evidence_grade_required": "replace_with_exact_grade",
      "required_outputs": [
        {"path": "solver-report.md", "schema": "math-research-solver-report/v1", "sha256_on_return": "required"}
      ],
      "failure_return": {
        "schema": "math-research-ticket-failure/v1",
        "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]
      },
      "reopen_condition": "replace_with_falsifiable_reopen_condition"
    }
  ]
}
-->

The machine-ticket `dependencies` array is empty or contains only exact objects `{"ticket_id":"dependency-id","path":"project-relative completion path","sha256":"64 lowercase hex"}`. A verifier has at least one dependency that resolves to an exact closed solver `math-research-ticket-completion/v8` record bound to the same Contract/run/candidate; it may not self-reference or use a dependency hash as the candidate. The frozen ticket wrapper has exact top-level keys `schema,project_id,control_generation,contract,run,cycle_id,contract_initial_tickets_sha256,counter_snapshot,ticket` with schema `math-research-frozen-ticket/v8`; it contains neither its own hash nor `source_event`.

Generation state `current_ticket.source_event` is `null` for an initial ticket and exact `{path,sha256}` for a derived ticket; this lifecycle/source-event distinction, rather than run status alone, controls classification. A derived ticket event has schema `math-research-ticket-event/v8` and exact top-level keys `schema,project_id,control_generation,event_id,ticket_id,ticket,role,contract,run,counters,input_artifacts,dependencies,updated_at_utc`: `ticket={path,sha256}`, Contract is the full three-key pointer, run is identity-only `{id,path}`, counters are the exact issuance snapshot, inputs are raw path/hash pointers, dependencies are exact ticket-ID/path/hash completion pointers, and time is UTC `Z`. `ticket_id`/role/inputs/dependencies deep-equal the inner ticket; `event_id` is the separate safe event identifier. This one-way event→ticket hash binding prevents self-reference. The global exact worker allowlist is `apply_patch`, `collaboration.spawn_agent`, `collaboration.send_message`, `collaboration.wait_agent`, and `shell_command`, plus `web__run` only if `web_search=allowed`; a denied Contract omits `web__run`. `allowed_tools` is a unique subset and cannot name Goal/control/dispatcher/launcher/lease/`exec` or retired routes, and ticket `tool_calls`/`max_output_bytes` cannot exceed policy. A verifier is derived only, has nonempty ticket-completion dependencies, and has exactly one additional `candidate_artifact={path,sha256}` equal to exactly one input artifact; it cannot self-reference or disguise a dependency as the candidate.

## Launch intent

The user's explicit Goal-mode request to launch this exact Contract authorizes the current active Goal task to record internal hashes, persist and verify v8 genesis/advisory state/checkpoint/initial ticket, and then begin Cycle 1 after a fresh get_goal check. Approval without launch intent does not authorize launch. Platform boundaries remain separate; a child ticket cannot broaden authority.

## Goal ownership and genesis gate

Call get_goal in this current task. Require the intended active Goal. Immutable Contract bytes contain only the binding policy and problem hash; record the required Goal objective hash and optional stable task/thread ID externally in RUN_GENESIS/HOST_BIND and generation state/checkpoint. Never create or recover a Goal in a CLI or collaboration child. While active, persist and verify RUN_GENESIS, HOST_BIND, generation candidates, and initial ticket; a fresh run starts at zero while a legacy successor starts at its inherited cumulative baseline. Invoke scripts/commit_math_research_head_v8.ps1 for the cooperative guarded single project.json head transition last; it is Goal-agnostic, grants no authority, and serializes only cooperating writers.

The advisory file and ticket hashes are ordinary integrity records. They are not cryptographic signatures, capabilities, leases, or proof of Goal activity.

## Immutable Research Contract vN

[Paste the complete resolved Research Contract vN from section 2. It is immutable after confirmation.]

## State, event, and budget gate

Maintain Goal, Contract, and Run states separately. Run states are not_started, preparing, attempt_running, audit_due, auditing, completion_candidate, awaiting_input, paused, goal_continuity_terminal, superseded, and closed.

Each immutable generation project event has exact keys `schema,project_id,control_generation,event_id,event_type,updated_at_utc,previous_event_sha256,contract,run,counters,referenced_artifacts`, schema `math-research-project-event/v8`, a UTC `Z` timestamp, the prior authoritative project-event hash (`null` only at first v8 activation), exact generation Contract/run/counters, and raw artifact path/hash pointers. `event_type` is one of `RUN_GENESIS|LEGACY_SUCCESSOR|CHECKPOINT_COMMIT|ATTEMPT_START|ATTEMPT_END|AUDIT_START|AUDIT_END|HOST_REBIND|PAUSE|RESUME|COMPLETION_READY`.

That closed enum belongs only to the generation/project-head transition layer. Run-ledger/domain records may use names such as `PUBLICATION`, `COMPLETION_CANDIDATE`, `SUPERSEDE`, or `CLOSE`, but they are ordinary referenced artifacts and MUST NOT be written as `project_event_head.event_type` or treated as head-transition authority.

Maintain monotone attempt_count, audit_count, total_round_count=attempt_count+audit_count, attempts_since_last_audit, and audit_due exactly as specified in the cycle protocol. Before every new attempt, require the old counters to satisfy `attempt_count + 1 <= attempt_budget` and `total_round_count + 2 <= total_round_budget`; this reserves the possible mandatory terminal audit even when the attempt does not hit the configured interval. Never reset counters through retry, pause, rebind, migration, or a replacement run.

## Research execution

Each attempt answers one frozen falsifiable question. A `source_event=null` initial solver ticket is only the `preparing` seed and is never dispatched. `ATTEMPT_START` replaces it with a new active derived solver ticket plus non-null ticket event, all bound to post-start counters; delegate that bounded collaboration ticket only after activation/read-back. Every `ATTEMPT_END.referenced_artifacts[0]` is one exact nine-key `math-research-attempt-outcome/v8`: `schema,project_id,contract,run,attempt_id,outcome,candidate,verifier_completion,completed_at_utc`; outcome is `candidate_found|no_candidate|inconclusive|failed|awaiting_input`. A claimed mathematical result requires an independently derived verifier ticket with a distinct ID/hash/role/output path bound to the exact final candidate hash. `candidate_found` closes that current verifier ticket and requires identical candidate, verifier ticket ID, Contract/run, plus an exact PASS verifier result/completion; verifier schemas have no attempt ID. Outcome `attempt_id` is checked only as a safe ID distinct from the current verifier ticket ID, while the Attempt-record↔outcome attempt-ID relation remains Host-maintained and unmechanized in this helper version. Noncandidate outcomes use null candidate/verifier completion. At most one preregistered directed repair is allowed; a repaired candidate requires fresh verification. New lemmas, bridges, or syntheses require new attempts.

A special family, bounded computation, numerical fit, one-way reduction, consensus, or theorem-strength missing lemma does not settle a global target without a proved coverage bridge.

## Audit

When due, freeze one Contract/candidate/evidence/ledger/counter snapshot. Delegate exactly skeptic_quantifiers, skeptic_strategy, and theory_tool_scout. They return PASS, FAIL, or INCONCLUSIVE and perform no new proof work. Every `AUDIT_START` publishes one immutable `math-research-cycle-audit-plan/v8` with exact keys `schema,project_id,contract,run,audit_kind,candidate,snapshot,active_ticket,tickets,started_at_utc`. Terminal `candidate` is non-null and exactly equals the locked `candidate_found` Attempt outcome; scheduled/early require null. Every `AUDIT_END` publishes exactly one immutable `math-research-cycle-audit-summary/v8` linked to that start event/plan and exactly three ordered reports; plan, summary, and reports share the same candidate/snapshot. If interval/final-attempt audit is due at candidate discovery, preserve the gate but give terminal audit priority and clear it once at terminal `AUDIT_END`. Pre-audit completion-candidate advances only via `AUDIT_START` or outcome-preserving `HOST_REBIND`. Completion requires terminal PASS reports with no new math; terminal non-PASS cannot publish `COMPLETION_READY` and yields no automatic completion mutation.

## Sources, computation, and evidence

Use only the frozen source/network/tool envelope. Record primary-source locators and as-of dates. Preserve computation code/input/tool/version/domain/precision/output/error checks, reproduction instructions, and evidence grade. Sandbox scope is not a universal confidentiality guarantee.

## Publication, pause, Resume, and return

Fresh get_goal is required immediately before every authoritative publication. Stage proposed files nonauthoritatively; after the fresh gate publish each file atomically and publish one authoritative event/head/project pointer last. Do not claim multi-file atomicity. For pause, publish/read back PAUSE + handoff and return without Goal mutation. For completion, persist/read back both completion flags true; this permanently freezes project/head mutation. Startup then returns goal_host_completion_pending; call get_goal again immediately before update_goal(status=complete), and call it only if active/matching with no project write. Other non-active states remain pending read-only; blocked is never a pause surrogate.

Same-task continuation resumes the unique durable lifecycle point without resetting counters. A different task on a v8 run uses the sole special rebind gate: user-explicit revocation of old binding plus new Goal authorization, fresh new Goal active, no unfinished commit, unchanged semantics/permissions, then one new-Host-authored exact-schema HOST_REBIND with the old head in prior_host_binding and explicit retirement authority/reason, followed by the cooperative guarded head-helper transition. User revocation is sufficient; never query the old task. The new raw hash need not equal the obsolete one. Contract/problem/run identity remains unchanged; any change is read-only pending an implemented RUN_SUCCESSOR. Legacy runs never rebind.

At valid completion, persist/activate/read back `completion_ready=true` and `pending_goal_update=true`, then make no further project/head mutation. Fresh get_goal immediately before update_goal(status=complete); only active/matching may call it. If non-active, keep the durable pending state. Never clear flags, resume, audit, or publish; Goal complete is closed review. Otherwise return the strongest verified partial result, exact gaps, spent counters, evidence grades, and falsifiable reopen conditions without marking complete.
```

## 4. v8 Attempt record

每次 `ATTEMPT_END` 保存一个固定键集合的 JSON。`route_portfolio` 不适用时为 `null`，`source_claims` 可为空数组：

```json
{
  "schema_version": 1,
  "attempt_id": "attempt-0001",
  "tickets": [
    {
      "ticket_id": "C1-T1",
      "role": "solver",
      "ticket_sha256": "64 lowercase hex",
      "input_artifacts": [{"path": "input-a", "sha256": "64 lowercase hex"}],
      "candidate_sha256": null,
      "outputs": [{"file": "solver.md", "sha256": "64 lowercase hex"}]
    },
    {
      "ticket_id": "C1-V1",
      "role": "verifier",
      "ticket_sha256": "64 lowercase hex",
      "input_artifacts": [{"path": "candidate.md", "sha256": "最终候选 hash"}],
      "candidate_sha256": "最终候选 hash",
      "outputs": [{"file": "verification.md", "sha256": "64 lowercase hex"}]
    }
  ],
  "attempt_kind": "route_execution",
  "decision_question": "与票据逐字一致的问题",
  "solver_reports": [
    {"file": "solver.md", "sha256": "64 lowercase hex"}
  ],
  "verification_reports": [
    {
      "candidate_sha256": "最终候选 hash",
      "verdict": "PASS",
      "artifact_file": "verification.md",
      "artifact_sha256": "64 lowercase hex",
      "new_math_performed": false
    }
  ],
  "repair_batches": 0,
  "result_artifact": {"file": "result.md", "sha256": "64 lowercase hex"},
  "result_evidence_grade": "proved",
  "counter_snapshot_before": {"attempt_count": 0, "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0, "audit_due": false},
  "counter_snapshot_after": {"attempt_count": 1, "audit_count": 0, "total_round_count": 1, "attempts_since_last_audit": 1, "audit_due": false},
  "failure_record": null,
  "route_portfolio": null,
  "source_claims": []
}
```

`candidate_found`、`proved_subclaim`、`route_refuted`、`bounded_negative` 必须绑定最终产物的 PASS verifier。使用一次 repair 时，同时保留修订前非 PASS 与修订后 PASS。路线发现结果只生成 route portfolio，经 audit 接受后才可成为后续 ticket 输入。

## 5. Machine-block hash algorithm

对生成后的 ContractFile：

1. 全文件 CRLF→LF，拒绝 isolated CR。
2. 要求恰好一个 cycle-policy block 和一个 initial-tickets block。
3. 删除注释开闭 delimiters 与 JSON body 两端各一个约定 LF。
4. 对剩余 exact UTF-8 JSON text 算 SHA-256；不 trim、不 Unicode normalize、不重排 key、不改缩进/数字拼写、不 canonicalize。
5. 把两个 lowercase hash 写入 top metadata。
6. 再对最终完整 ContractFile 算外置 `contract_binding_sha256`。

两段 JSON 在替换 placeholder 后必须是严格 JSON；禁止注释、尾逗号和重复键。Machine blocks 中 numeric `-1` 是整 token sentinel：生成器必须用用户选择的 JSON integer 整体替换，validator 必须拒绝任何残留负值或用字符串表示的预算/cap。Ticket hash 不写回 ticket 自身；Host 对冻结 ticket bytes 算 hash，并只记录在 generation state、单向 derived-ticket event、Attempt event 和 Attempt record 中，避免自引用。

## 6. 外部授权记录

Host 在项目 state/run 中自动记录：

```text
Research Contract package: vN
contract_binding_sha256: [whole ContractFile hash]
host_goal.thread_id_available: [true|false]
host_goal.thread_id: [stable current task/thread ID|null]
host_goal.objective_raw_sha256: [raw Goal objective hash]
problem_statement_sha256: [canonical problem hash]
launch_intent: Direct current active Goal task performs v8 genesis and Cycle 1.
approval_mode: [approve_for_me|never]
authorization_source: [explicit launch request | exact active same-scope envelope]
```

内部 hash 自动生成、记录、核验；不得要求用户 relay hash 或运行技术命令。`approve_for_me` 只表示 Host 可提交合同范围内的窄 `require_escalated` 请求给 `managed auto-review`，不绕过平台边界。

## 7. Legacy v3-v7 boundary

既有 Prompt v3-v7 只供原始档案解释，保留其 thread、contract、primary/backup manifest、checkpoint、handoff、预算和全部 counters。所有 legacy Goal bindings 一律 obsolete；它们不能通过新 v8 Host 恢复旧 child Goal。

startup v3 若发现 `goal_continuity_failed`、`MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`，或 failed child Goal 且 `persistence_verified=false`，对 **old run** 返回 `goal_continuity_terminal -> stop_no_retry_preserve_run`。禁止伪装 Resume、create Goal、重复 migration、manifest 改写或 counter reset；这不禁止下述 additive successor。

用户显式创建新 active Goal，且 hash-bound effective predecessor envelope 与新 v8 Contract 在 target/domain/quantifiers/dependencies/assumptions/completion、model/reasoning、privacy/external effects、全部 agent/runtime/attempt/audit/round/cumulative ceilings 等价，并且任何非控制权限/资源不扩张时，Host 才可在同项目生成新的 v8 successor Contract/run。Effective envelope 必须按 archive 定义，从 frozen predecessor Contract/base manifest 与 strict hash-cross-bound recorded amendments 的 order 确定，不能任取旧 prose 或 stale file；legacy HMAC 只做 self-consistency evidence，本协议不认证它。旧 child Goal/launcher/dispatcher/lease/migration/control-receipt authority 必须退休并映射为 direct-current-task/v8 + bounded collaboration + head helper；这是唯一允许的 safe contraction，不要求 legacy control bytes 与 v8 相等。相同项目 `/goal $math-research-solve …继续直到证明或证伪` 已构成该 normalized nonexpanded envelope 的 launch intent，不得要求用户重复 confirmation/hash/command；authority 来自 current active Goal，而非 legacy HMAC/receipt。任何其余差异、unresolved normalization gap、expansion 或后续 v8 Contract/run 替换都只能 planning/read-only；`RUN_SUCCESSOR` 未实现，新的合同 confirmation 本身不能 genesis 或提交 head。

Successor Contract metadata 使用 `run_origin=legacy_successor` 并绑定独立 predecessor-derived `inherited_counter_budget_baseline_sha256`；Contract 正文还必须绑定 effective-predecessor-envelope 与 retired-control-mapping 两个 immutable artifacts 的 project-relative path/hash。它不绑定 lineage hash，也不写 current Goal identity，避免 Contract↔lineage 自引用。首个 `LEGACY_SUCCESSOR` project event 的 `referenced_artifacts` 必须包含这两个 raw pointers。外置 immutable lineage 位于 `state/successors/gNNNN.json`，schema 为 `math-research-legacy-successor-lineage/v8`，并单向绑定 Contract；其 exact keys 仍为 `schema,project_id,control_generation,legacy_goal_bindings_obsolete,predecessor,inherited_artifact_index,inherited_counter_budget_baseline,successor`，不因新增工件改变。

Builder 生成的 Contract 正文必须逐字使用下列五行 binding 形状；前两行是本 gate 的机器校验成员，不得改成 metadata key 或省略：

```markdown
## Legacy-successor binding

- Deterministic build intent: `state/build-intents/gNNNN.json` (`64 lowercase hex`)
- Effective predecessor envelope: `runs/successor-gNNNN/evidence/effective-predecessor-envelope.json` (`64 lowercase hex`)
- Control migration map: `runs/successor-gNNNN/evidence/control-migration-map.json` (`64 lowercase hex`)
- Inherited artifact index: `runs/successor-gNNNN/evidence/inherited-artifacts.json` (`64 lowercase hex`)
- Predecessor Contract: `contracts/legacy-contract.md` (`64 lowercase hex`)
```

两个新 JSON 工件的 exact schemas、fixed `source_precedence`、mapping enums、canonical compact UTF-8/no-BOM/one-LF raw hash 算法见 [archive protocol](research-project-archive.md#effective-predecessor-envelope-and-control-migration)。Production builder 是它们的 dedicated schema/source validator；head helper/startup 只通过 project event 做 generic raw-pointer/hash validation，不含第二份 schema-specific parser。因此不得绕开 builder 手工拼 candidate。Contract 的 normalized binding hash 仍按本文 CRLF→LF 规则计算，和工件 raw-byte hashes 是两种明确不同的绑定。

- `project_id`、`control_generation`、`legacy_goal_bindings_obsolete=true`；
- exact predecessor-project snapshot path/hash（也是 cooperative guarded activation transition 的 expected-old），以及 predecessor run/contract/primary+backup manifest/checkpoint/handoff paths/hashes（缺失项显式 `null`）；
- complete inherited artifact index path/hash，使用 canonical categories，逐 entry 保存 category/path/hash/original evidence grade；
- independent inherited counter/budget baseline path/hash；
- successor Contract/run/`RUN_GENESIS`/immutable initial `HOST_BIND` hashes。

先 snapshot old `project.json` exact bytes，再 stage/验证 immutable lineage、new run 和 generation checkpoint/state；`preparing` counters 等于 inherited baseline，以后不得低于。`state/successors/gNNNN.json` 本身是 `LEGACY_SUCCESSOR`，只有 fresh gate 后由 `scripts/commit_math_research_head_v8.ps1` 以 snapshot hash/generation 为 expected-old 执行 cooperative guarded head transition 才生效。此前失败时 old active pointers 不变，新材料只是 unreferenced staging。这是新 run 延续同一研究档案，不是恢复旧 Goal。

## 8. 最终检查

- 数学目标写全对象域、量词、依赖、边界与证书。
- Immutable Contract 只含 Goal binding/rebind policy；Goal raw objective/task identity 仅在外置 HOST_BIND chain 与 generation state/checkpoint（checkpoint 还绑定其 immutable head），并与 canonical problem 分开绑定。
- Goal/Contract/Run 三层状态和完整 run enum 明确。
- 所有资源和权限字段都有当前明确值，无静默默认。
- initial ticket ID 在 genesis 后可用；attempt ID 只在 ATTEMPT_START 后产生。
- ticket tool_calls/runtime/agent/output caps 都是 JSON integer 且 `-1` sentinel 已全部替换；allowed tools、source/network policy、filesystem/staging、evidence grade、dependencies、failure schema 与 output hashes 完整。
- verifier 使用独立 ticket 并绑定 exact candidate hash；Attempt record 的 `tickets` 数组覆盖全部 solver/verifier tickets 和多输入 hashes。
- initial ticket deep-equal Contract member；derived ticket 不要求相等，但其 full schema/权限/caps/inputs/dependencies 全验，并由 state `source_event` 指向的 exact ticket event 单向绑定 ticket hash。
- tickets 是 frozen/hash-bound records，未被称为密码学签名或 lease。
- fresh get_goal 覆盖 attempt、audit、publication、handoff、pause、closing、rebind、completion。
- pause 在 active fresh gate 后落盘/回读并 return，不调用 update_goal；completion flags 只允许 false/false 或 true/true，true/true 激活后项目永久只读，startup 返回 goal_host_completion_pending；update_goal(status=complete) 紧前再 fresh get_goal，失活时保留 pending，永不清 flags/resume/audit/publish。
- counters 单调，audit gate 和总轮计数正确。
- completion 使用同一 frozen candidate 的三份 PASS。
- v8 rebind 只推进外置 HOST_BIND chain/control generation，不改 Contract；Prompt v3-v7 old run 永不自动重试，但显式新 Goal 可走完整 `LEGACY_SUCCESSOR` 新-run 出口。
