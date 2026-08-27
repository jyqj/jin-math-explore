# Cycle and audit protocol v10 with v8 compatibility

## v10 continuous-research override

v10 keeps the same fresh-Goal, counter, three-role audit, and strict completion gates described below, but changes attempt granularity:

- an attempt is one frozen-bottleneck campaign, so auxiliary lemmas, bridge work, and in-family synthesis may continue through `RESEARCH_CHECKPOINT` without a new attempt;
- a non-promoting negative attempt may close without a verifier;
- every candidate, verified partial result, or failure boundary still requires an exact independent verifier;
- the strategy auditor must read the continuity capsule and every complete artifact it names, not only result summaries;
- the strategy auditor returns one `math-research-strategy-action/v1` with `continue|synthesize|semantic_reset|quarantine|await_input`, bottleneck progress, surface-reset risk, missing full artifacts, synthesis map, ranked routes, required next inputs, and `new_math_performed=false`;
- a new mathematical lead found during audit remains quarantined until a later solver reconstructs it;
- semantic-reset triggers and route-portfolio validation follow `proof-search-continuity.md`.

The sections below retain the exact v8 historical schemas where named. Existing v8 projects continue to use them byte-for-byte; v10 projects use the corresponding v10 state and artifacts from `state-machine-v10.md` and `contract-and-prompt-template-v10.md`.

本协议适用于新的 **Math Research Contract v8**。当前 product Goal task 是唯一 Goal Host；数学求解、候选核验和审计只能委派给 collaboration subagents。Prompt v3-v7 均为冻结 legacy，不能注入 v8 Goal ownership、预算或状态。

## 1. 三层状态

| 层 | 合法状态 | 权威来源 |
|---|---|---|
| Goal | `none`, `active`, `paused`, `blocked`, `complete` | 当前任务 fresh `get_goal`；cancelled/absent 映射为 `none` |
| Contract | `draft`, `awaiting_confirmation`, `confirmed`, `superseded` | 已绑定 ContractFile 与项目索引 |
| Run | `not_started`, `preparing`, `attempt_running`, `audit_due`, `auditing`, `completion_candidate`, `awaiting_input`, `paused`, `goal_continuity_terminal`, `superseded`, `closed` | run ledger 与 `project.json` 指向的同一 `state/generations/gNNNN/{checkpoint.json,goal-host-v8.json}` 一致快照 |

项目文件不能证明 Goal 状态。project head 指向的 generation `goal-host-v8.json` 是普通 hash-bound advisory state，不是签名、授权、lease 或控制面证明。

## 2. Fresh Goal gate

Goal Host 必须在下列动作**紧邻之前**调用 `get_goal`：

- genesis 或显式 host rebind；
- 每个 `ATTEMPT_START` 和对应 worker dispatch；
- 每个 `AUDIT_START` 和三名 auditor dispatch；
- AttemptEnd、AuditEnd、completion candidate、handoff 等权威发布；
- pause、closing、supersede 或 completion。

只有当前任务 fresh `get_goal` 返回 `active` 且 raw-objective hash 与运行记录一致时，才允许权威写入或研究。若平台实际返回稳定 task/thread ID 且运行记录了该值，也必须一致；平台不暴露稳定 ID 时明确记为 unavailable，不因此阻塞合法 current Goal。child、脚本参数、Prompt、路径、marker、checkpoint、hash 或另一任务的 `get_goal` 均不能替代 fresh call。

一旦观察到 `none|paused|blocked|complete`，当前项目立即只读。不得补写 checkpoint、继续已排队 child、重建 Goal、重绑另一 Goal 或完成尚未提交的发布。

## 3. Genesis

在 active Goal 中，按一个受保护的模型/文件事务完成：

1. 冻结 Contract v8、问题 hash、`goal_binding_policy=direct-current-task/v8` 和资源信封；当前 Goal identity 不写入 immutable Contract；
2. 建立 run，追加 `RUN_GENESIS` 与外置 `HOST_BIND`（必需 objective hash、平台若有则 task/thread ID）；
3. 写入 generation-unique advisory/checkpoint candidates 和 initial ticket；fresh project 计数为零，legacy successor 使用已验证累计 baseline；
4. 回读并核对 project/contract/run/problem/Goal/counter/ticket 全部交叉绑定；
5. fresh Goal gate 后只调用 `scripts/commit_math_research_head_v8.ps1`，按 sole-writer/helper 协议执行 cooperative guarded 单一 `project.json` head transition，使候选 generation active；
6. fresh `get_goal` 后再进入第一次 `ATTEMPT_START`。

Genesis 不消耗 attempt 或 audit round。此时可报告 initial ticket ID，但 attempt ID 只有在 `ATTEMPT_START` 后才存在。

## 4. 预算与计数

维护：

```text
attempt_count
audit_count
total_round_count = attempt_count + audit_count
attempts_since_last_audit
audit_due
```

规则：

1. 权威 `ATTEMPT_START` generation 令 `attempt_count += 1`、`total_round_count += 1`、`attempts_since_last_audit += 1`。
2. 若该开始使 `attempts_since_last_audit == audit_interval_attempts`，立即置 `audit_due=true`。本尝试可以结束，但下一次 `ATTEMPT_START` 禁止发生。
3. 一个完整三角色 `AUDIT_START` generation 令 `audit_count += 1`、`total_round_count += 1`。
4. 完整 `AUDIT_END` 才令 `attempts_since_last_audit=0` 并清除适用 gate。
5. scheduled、early、terminal 与 closing audit 都占一个 total round。
6. startup、read-only verify、operational retry、artifact formatting、publication 本身不占 attempt；这些动作不得夹带数学搜索。
7. 全局计数在 pause、Resume、rebind、新 contract、migration 或失败后均不归零。

Host 必须在**每个**新 attempt 前（不只将在本轮命中 audit interval 的 attempt）为可能必需的 terminal audit 留出一个 total round。以开始前的旧 counters 机械要求 `attempt_count + 1 <= attempt_budget` 且 `total_round_count + 2 <= total_round_budget`；否则拒绝 `ATTEMPT_START`，停止并返回非完成结果。不得创建替代 run/window 绕过上限。

## 5. Ticket 冻结

每张 collaboration ticket 在 dispatch 前固定：

- ticket ID、非权威 planned lifecycle slot、project/contract/run/cycle binding；
- role 与逐字 decision question；
- 输入 artifact 路径/hash 与依赖；每个非空 dependency 都是 exact `{ticket_id,path,sha256}`，并指向 immutable ticket-completion record；
- method family、search domain、success signal、stop signal；
- allowed tools、source/network policy、filesystem scope、唯一 writable staging directory、tool/runtime/output-size caps；
- required output paths/schemas、返回 output hashes、evidence grade、dependencies 与固定 `failure_return` schema（status/failed step/reason/partial hashes/reopen condition）；
- ledger/counter snapshot；Host 对最终 ticket bytes 计算的 hash 只记录在 state pointer、外部 ticket event 和 Attempt record，不写入 ticket 自身。

Ticket 不可变且 hash-bound，但**不是 cryptographically signed**，不是 capability，也没有 Goal 权限。不存在本地 one-use lease。worker 只写其 staging 目录；Host 核验返回产物后才提交权威事件。

Frozen ticket wrapper 的 exact top-level keys 是 `schema,project_id,control_generation,contract,run,cycle_id,contract_initial_tickets_sha256,counter_snapshot,ticket`，schema 为 `math-research-frozen-ticket/v8`；ticket file 不含自身 hash，也不含 `source_event`。Generation state 的 `current_ticket` 同时保存 ticket `id/path/sha256/status`、Contract-block hash、三项 counter snapshot 与 nullable `source_event` pointer。其初始/派生性质由 lifecycle 与该 pointer 决定，不由 run status 推断：`null` 只对应 initial ticket，inner ticket 必须 deep-equal Contract initial member；non-null exact `{path,sha256}` 对应 derived ticket，执行完整 schema/权限/cap 检查但不要求等于 initial member；verifier 必须是后者。

Derived ticket event schema 为 `math-research-ticket-event/v8`，exact top-level keys 是 `schema,project_id,control_generation,event_id,ticket_id,ticket,role,contract,run,counters,input_artifacts,dependencies,updated_at_utc`。其中 `ticket={path,sha256}`，`contract={path,version,binding_sha256}`，`run={id,path}`，`counters` 是 exact issuance snapshot，`input_artifacts` 是 raw pointer array，`dependencies` 是 exact `{ticket_id,path,sha256}` ticket-completion array，时间是 UTC `Z`。Event 的 `ticket_id`/role/input/dependencies 必须与 inner ticket deep-equal；`event_id` 是独立 safe event identifier。State `source_event` 绑定 event hash；这是单向 event→ticket binding，不形成 hash cycle。

Cycle policy exact 增加 `allowed_worker_tools`（非空、唯一 closed allowlist）、`max_ticket_tool_calls`（正整数）和 `max_ticket_output_bytes`（正整数）。全局 allowlist 精确为 `apply_patch`、`collaboration.spawn_agent`、`collaboration.send_message`、`collaboration.wait_agent`、`shell_command`，且仅当 `web_search=allowed` 时可增加 `web__run`；`denied` 必须删除它。每 ticket 的 `allowed_tools` 是唯一子集，禁止 Goal/control、controller/dispatcher/launcher/lease、`exec` control 与 retired launcher 名；`tool_calls` 与 `max_output_bytes` 不得超过 policy。初始 source-event-null ticket 必须为 solver。初始 machine ticket 中 `resource_caps.tool_calls` 是必须由合同填写的 placeholder，不得固定为 `1` 或其他默认值。

## 6. AttemptStart

满足下列条件才可开始：

- Contract 已 confirmed 且 launch intent 覆盖本动作；
- fresh Goal gate 通过；
- run 不是 terminal/paused/closed/superseded；
- `audit_due=false`；
- attempt 与 total-round 预算充足且保留必需 audit；
- route fingerprint 未冻结重复，或已有预先登记的合格 reopen evidence；
- ticket 及其依赖已完整发布并 hash 一致。

Builder/genesis 的 `source_event=null` initial solver ticket 只是 `preparing` seed，绝不直接 dispatch。Host 在 non-authoritative staging 形成 `ATTEMPT_START`、不可复用 attempt ID、ticket-to-attempt binding、预算消费，以及一张新的 active derived solver ticket 与 non-null `math-research-ticket-event/v8`；state pointer、ticket envelope、ticket event 全部绑定 post-start counters。紧邻发布前 fresh gate，通过后逐文件发布并只用 `scripts/commit_math_research_head_v8.ps1` 切换单一 project head，回读成功后才 dispatch 这张 derived ticket。若 dispatch 失败，attempt 不退款；以 staged `aborted` AttemptEnd 候选开始后续 fresh-gated publication。是否另开新 attempt 由后续 active Host 决定。

候选需要核验时，Host 必须派生一张独立 verifier ticket：不同 ticket ID/hash/role/output path，non-null `source_event`、非空 dependencies，且唯一新增 `candidate_artifact={path,sha256}` 必须 exact 等于一个 `input_artifacts` 成员。不得让 solver ticket 自证、复用其输出路径、self-reference 或用 dependency hash 伪装 candidate。

## 7. 数学研究内循环

`attempt_kind` 只能是：

- `route_discovery`：产生可检验路线卡，不直接宣称数学结论；
- `route_execution`：执行一条冻结路线；
- `candidate_revision`：针对已知缺陷进行独立登记的修订；
- `candidate_synthesis`：使用已发布 claim/evidence hashes 进行组合。

一次 attempt 只回答一个可证伪问题。一个或多个 solver 可共同形成候选，但任何 `candidate_found`、`proved_subclaim`、`route_refuted` 或 `bounded_negative` 都必须由独立 verifier 对最终候选 hash 给出 PASS。solver 与 verifier 报告不得是同一文件或同一 hash。

同一次 attempt 最多一次预登记定向 repair。修订前非 PASS 报告和修订后新 PASS 报告都要保存。若需要新引理、覆盖桥梁或跨路线综合，结束当前 attempt，再登记新 attempt。

有限搜索、特殊子族、局部同余、数值拟合、单向归约或缺失 theorem-strength lemma 都不能自动提升为全局解决。

## 8. AttemptEnd

Host 收齐 worker 返回后：

1. 验证所有路径、hash、ticket binding 和角色分离；
2. 验证 candidate 的最终 verifier verdict；
3. 对负面/不确定/aborted 结果在非权威 staging 写完整 failure record；
4. 在非权威 staging 写 Attempt record 与最终 artifact；Attempt record 的 `tickets` 数组列出每张 solver/verifier ticket 的 id、role、ticket hash、candidate/input hashes 与 output hashes；
5. fresh `get_goal`；
6. 若仍 active，逐文件原子发布验证后的最终 artifacts，写入下一代 immutable checkpoint/advisory state，最后调用 `scripts/commit_math_research_head_v8.ps1`，以 cooperative guarded 单一 `project.json` head transition 选择 authoritative event/head 并发布 `ATTEMPT_END`；再发布人类可读视图。

每个 `ATTEMPT_END.referenced_artifacts[0]` 必须是 exact `math-research-attempt-outcome/v8`，且只有九个 keys：`schema,project_id,contract,run,attempt_id,outcome,candidate,verifier_completion,completed_at_utc`。`outcome` closed set 为 `candidate_found|no_candidate|inconclusive|failed|awaiting_input`。非候选 outcome 的 `candidate` 与 `verifier_completion` 都为 null。`candidate_found` 必须关闭当前 derived verifier ticket，并让 outcome candidate、ticket `candidate_artifact`、PASS verifier result/completion 的 candidate、ticket ID、Contract/run 三方完全一致；outcome `attempt_id` 只机械验证为 safe ID 且必须不同于当前 verifier ticket ID，verifier schema 不含 attempt ID。Attempt record 与 outcome attempt ID 的对应由 Host 维护，本 helper 版本未机械交叉验证；所有 pointers 都是 immutable non-staging raw pointers。

Failure record 至少记录失败步骤、失败类型、排除范围、不能推出的结论、evidence hashes、retry fingerprint 与可证伪 reopen conditions。若第 5 步观察到非 active，禁止发布；staging 仍非权威，只报告最后已经耐久提交的 head。以上流程不声称多文件原子性。

## 9. AuditStart

触发条件：

- `attempts_since_last_audit == audit_interval_attempts`；
- 早期重大风险；
- completion candidate；
- 非完成 closing review；
- 用户/合同明确要求。

Host 先冻结同一份 Contract binding、问题 hash、ledger/counters、candidate/evidence 列表、route cards 和 trigger labels，stage `AUDIT_START` 及预算消费；紧邻发布前 fresh Goal gate，通过后逐文件发布并只用 head-commit helper 激活单一 project head，回读成功后才 dispatch。`math-research-cycle-audit-plan/v8` 的 exact keys 为 `schema,project_id,contract,run,audit_kind,candidate,snapshot,active_ticket,tickets,started_at_utc`：terminal 时 `candidate` 必须 non-null 且等于 locked `candidate_found` Attempt outcome；scheduled/early 时必须 null。其余 dispatch 为：

- `skeptic_quantifiers`：检查对象域、量词、覆盖、边界与反例；
- `skeptic_strategy`：检查证明链、循环依赖、失败路线和替代解释；
- `theory_tool_scout`：检查已用定理/工具的条件与已有材料是否遗漏。

三者各自输出 PASS、FAIL 或 INCONCLUSIVE。审计不能补证明、运行新搜索/计算、提高界、改 artifact 或现场发明路线。新线索只能进入 `quarantined_leads`，待 AuditEnd 后另开 attempt。

## 10. AuditEnd

Host 验证三份报告绑定同一 snapshot/candidate 且角色/hash 分离，先写非权威 staging，然后 fresh `get_goal`。仍 active 时逐文件发布 artifacts/new generation，最后只调用 `scripts/commit_math_research_head_v8.ps1`，以 cooperative guarded 单一 `project.json` head transition 选择 authoritative event/head 并发布 `AUDIT_END`、counter/gate/checkpoint；人类视图随后更新。不得声称多文件原子。每个 `AUDIT_END.referenced_artifacts[0]` 都必须是唯一 immutable `math-research-cycle-audit-summary/v8`：exact keys 为 `schema,project_id,contract,run,audit_kind,audit_start_event,plan,candidate,snapshot,reports,completed_at_utc`，并按 `skeptic_quantifiers,skeptic_strategy,theory_tool_scout` 顺序指向恰好三份 distinct reports。每份 `math-research-cycle-audit-report/v8` exact keys 为 `schema,project_id,contract,run,role,candidate,snapshot,verdict,new_math_performed,checked_at_utc`。Plan、summary、reports 必须回链同一 `AUDIT_START` history 且 candidate 完全一致；terminal 仅三份 `PASS` 与 `new_math_performed=false` 才能进入 completion-ready。

任一 FAIL、INCONCLUSIVE、缺失报告或 hash mismatch 都禁止 completion。普通周期审计可以据 verdict 决定继续、冻结路线、等待输入或非完成关闭，但不能把审计意见当作新证明。

## 11. Completion candidate

只有当候选满足合同全部终止证书时，才可进入 `completion_candidate`。冻结：

- exact theorem/construction/classification statement；
- proof 或证书 artifact hashes；
- verification reports；
- source/computation certificates；
- ledger/counter snapshot；
- Contract/problem/Goal bindings。

完成必须对这同一 snapshot/candidate 运行 terminal audit，且三角色全 PASS。候选恰在 interval/final attempt 产生时，保留 `audit_due=true`，但 terminal audit 优先；它的单次 `AUDIT_END` 同时清除 audit gate，禁止再重复 scheduled audit。Pre-audit `completion_candidate` 只能转入 `AUDIT_START`，或由 `HOST_REBIND` 原样保留同一 Attempt outcome pointer。该 audited state 的 startup class 是 `goal_host_completion_ready_to_publish`；只有 fresh active Goal gate 才能随后发布 `COMPLETION_READY`。跨后续 `HOST_REBIND` 必须保留同一 terminal summary pointer 与完整 audit history。任一 terminal FAIL/INCONCLUSIVE 都必须回到非完成状态，绝不能发布 `COMPLETION_READY`。部分结果、预算耗尽、路线失败或“问题可能开放”都不是完成。

## 12. Pause、closing 与 Goal update 顺序

主动 pause/暂时返回只改变项目档案，不改变 product Goal：它只能暂停 `attempt_running` 或 `auditing`，必须以一份 immutable `math-research-resume-capsule/v8` 保存 prior status、exact ticket/lifecycle/counters；任何 nonrunning `PAUSE` fail closed。Paused head 唯一合法下一事件是 `RESUME`，或 exact capsule-preserving `HOST_REBIND`；`CHECKPOINT_COMMIT` 与其他事件全部拒绝。fresh `get_goal` 后仍 active 时只用 `scripts/commit_math_research_head_v8.ps1` 发布单一 project head 并回读 `PAUSE`、resume capsule、checkpoint、counters、gates、artifact hashes 和 handoff；随后 return。不得为 pause 调用 `update_goal`，也不得把 `blocked` 当 pause surrogate。

Completion 单独处理：两个 flags 只允许 false/false 或 true/true。Terminal audit 三份 PASS 后，按 publication gate 写入/激活/回读 closing state 并令两者都为 true；从这一 head 起项目永久只读，禁止清 flag、resume、audit、publication 或再次改 closing。startup 返回 `goal_host_completion_pending`；在 `update_goal(status=complete)` **紧前**再次 fresh `get_goal`，仅在仍 active/matching 时调用且不写项目。Goal complete 映射只读 `goal_host_closed_review`；其他失活状态保留 durable pending 只读状态。

如果一开始就观察到 `none|paused|blocked|complete`，项目只读，不得补写 PAUSE/closing。cancelled 按 `none` 处理。`blocked` 仅在平台独立的 repeated-blocker 规则实际满足时使用，绝非临时停止手段。

## 13. Resume 与新任务 rebind

同一 current Goal task 的后续轮次先跑 startup v3 只读分类，再 fresh `get_goal`，然后从 checkpoint 中唯一 lifecycle point 继续；不依赖旧聊天文本。

不同 task 只有在用户显式撤销旧 binding 并授权新的 continuation Goal/rebind 后才能处理。已有 v8 run 使用唯一 special rebind gate：fresh new Goal active、无 unfinished commit、Contract semantics/permissions 不变；用户撤销已足够，禁止查询旧 task。new Host 在同一 generation staging 写一个 exact-schema `HOST_REBIND`：`prior_host_binding` 等于 old head，`retirement={authority:"user-explicit-revocation",reason:<nonempty>}`，Contract/run identity 不变并绑定 new `host_goal`；不存在单独 `HOST_RETIRE`。随后 `control_generation += 1`，最后只用 head-commit helper 做 cooperative guarded head transition。new raw hash 不要求等于 obsolete binding。提交后普通 gate 才匹配 new binding；全部 counters/failures/routes/evidence/cumulative envelope 保持。目标、量词、权限、external effect、Contract 或 run identity 改变均 fail closed/read-only；`RUN_SUCCESSOR` 未实现，confirmation alone 不可执行。

所有 legacy Goal/control bindings 一律退休，legacy run 不能 rebind/Resume。用户显式新 active Goal 只有在 effective predecessor envelope 经 frozen Contract/base manifest + strict hash-cross-bound recorded amendments 的 order 确定后，与新 v8 Contract 在 target/domain/quantifiers/dependencies/assumptions/completion、model/reasoning、privacy/external effects、全部 agent/runtime/attempt/audit/round/cumulative ceilings 等价，且任何非控制权限/资源不扩张时，才可创建新 v8 successor；legacy HMAC 只做 self-consistency evidence，本协议不认证它。旧 child Goal/launcher/dispatcher/lease/migration/control-receipt authority 必须映射为 current Goal Host + bounded collaboration + head helper；这是唯一允许的 safe contraction，不是差异放宽。相同项目 `/goal …继续直到证明或证伪` 已提供该 nonexpanded envelope 的 launch intent，不得要求用户重复确认/hash/command；authority 来自 current active Goal 而非 old HMAC/receipt。Fresh active gate 后用 production builder 传入 exact raw objective/hash 与 optional stable ID，要求 exact result + `built=true` + expected-old/new agreement；builder Goal-agnostic 且永不改 `project.json`。它继承 problem、verified partial results、attempts、failures、evidence、routes、audits、handoff、intermediate artifacts 与累计 counters/budgets，snapshot old head，生成 Contract-bound effective-envelope/control-mapping artifacts，并 stage non-authoritative lineage/new `RUN_GENESIS`/`HOST_BIND`/generation files；首个 `LEGACY_SUCCESSOR` project event 的 `referenced_artifacts` 必须列出两工件，lineage/state/checkpoint exact keys 不变。再次 fresh gate 后，只有 head-commit helper 的 cooperative guarded 最终 `project.json` transition 才激活 `state/successors/gNNNN.json`。此前失败旧 pointers 不变。这是新 run，不是恢复旧 Goal。任何其余差异、unresolved normalization gap 或 expansion 都仅能 planning/read-only，等待另行实现并授权 `RUN_SUCCESSOR`；新合同 confirmation 本身不提供执行路径。

## 14. Legacy terminal circuit breaker

Prompt v3-v7 的原始文件、manifest、thread、合同和计数全部冻结。startup v3 若在 self-consistent primary/backup state 中发现以下任一项：

- `goal_continuity_failed`；
- `MATH_RESEARCH_GOAL_MISSING_OR_MISMATCHED`；
- failed child Goal 且 `persistence_verified=false`；

则对 old run 返回 `goal_continuity_terminal -> stop_no_retry_preserve_run`。禁止把新动作伪装成 old-run Resume、Tick、create Goal、重复 compatibility migration、改写 manifest、重置计数，或使用 caller `GoalStatus=active` 覆盖；本条不禁止 §13 的显式新-Goal additive successor。

## 15. Event invariants

Generation project-event exact top-level keys 是 `schema,project_id,control_generation,event_id,event_type,updated_at_utc,previous_event_sha256,contract,run,counters,referenced_artifacts`，schema 为 `math-research-project-event/v8`。`event_type` closed set 为 `RUN_GENESIS|LEGACY_SUCCESSOR|CHECKPOINT_COMMIT|ATTEMPT_START|ATTEMPT_END|AUDIT_START|AUDIT_END|HOST_REBIND|PAUSE|RESUME|COMPLETION_READY`；首个 v8 activation 的 previous hash 为 `null`，以后必须等于 old `project_event_head.sha256`。Contract/run/counters 与 generation 完全一致，artifact entries 都是 exact `{path,sha256}` raw pointers，事件文件自身 hash 只存于 project head/checkpoint。

该 closed set 只属于 generation/project-head transition layer。Run ledger/domain event 可记录 `PUBLICATION`、`COMPLETION_CANDIDATE`、`SUPERSEDE`、`CLOSE` 等业务标签，但它们只能作为 canonical project event 引用的普通 artifacts，绝不能成为 `project_event_head.event_type` 或独立 mutation authority。

每次权威提交必须满足：

- `control_generation`/generation path 单调，event ID 非空且为 safe ID；`previous_event_sha256` 连续提供权威顺序，不声称 event ID 自身单调；
- project/contract/run/problem binding 不漂移；effective Goal binding 仅可由合规 `HOST_REBIND` 或 `LEGACY_SUCCESSOR` 推进 control generation，旧 binding 必须保留在 immutable chain；
- counter 只按本协议变化；
- artifact 在 event 前已经写入并验证；
- child staging file 不直接成为权威记录；
- proposed files 先留在 non-authoritative staging，fresh gate 后逐文件原子发布，最后只用 `scripts/commit_math_research_head_v8.ps1` 发布单一 authoritative project head；这是 sole-writer/helper 协议下的 cooperative guarded CAS，不排除任意 non-cooperating writer；helper 不证明 Goal、不扩权；不声称多文件原子；
- machine state 先提交，人类视图后发布；
- publication 前 fresh Goal gate；
- 本地 hash 只被描述为普通完整性，不被称为控制面或密码学证明。
