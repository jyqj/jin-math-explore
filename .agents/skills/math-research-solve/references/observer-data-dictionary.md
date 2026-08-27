# math-research-solve Observer 阶段字典

目录版本为 `math-research-solve/v1`，指标契约为 `timing/v1`。Current production script phases 包括 v13 startup/transition prepare、独立 CAS commit、v12→v13 migration、bounded cognition 与 map validation；旧版 Startup、migration、ticket、topology 和 transition labels 仅用于冻结兼容或历史遥测。v13 state/prepare 不写权威，commit 只在 Host fresh Goal 门禁之后执行 expected-head CAS，migration 只保存和重绑冻结材料，cognition/map validators 不授予数学真值。所有 phase 都不证明 Goal、不扩权，也不排除任意 non-cooperating writer；retired labels 的 registration is not execution authority，MUST NOT invoke。

## 工作流阶段

| 阶段 | 含义 |
|---|---|
| `workflow.startup` | 实际进入 Skill startup 时的墙钟区间。 |
| `retrieve` | 只读检索。 |
| `verify_live` | 当前状态/文件验证。 |
| `plan_change` | 变更规划。 |
| `mutate` | 已获授权的实际写入。 |
| `validate` | 变更后验证。 |
| `version_control` | 版本控制步骤。 |
| `final_response` | 最终业务工具调用到答复前。 |

## Script phase authority

| Phase | Authority |
|---|---|
| `math-research-solve.script.math_research_state_v13` | **Current production, pure startup/transition prepare validator only.** 检查双 head、窗口、closing、verification、reconciliation、maintenance 与 terminal audit 候选；不写权威。 |
| `math-research-solve.script.math_research_commit_v13` | **Current production, journaled expected-head CAS helper only.** 仅在 Host fresh Goal 门禁后执行同卷 staging、命名锁、不可变对象优先与 `project.json` 最后替换/readback；本地 Goal 参数不替代 Host。 |
| `math-research-solve.script.finalize_attempt_package_v13` | **Current production, non-authoritative attempt-package finalizer only.** 在 fresh same-volume staging 中规范化 JSON、回填 package-local 指针并生成 manifest/receipt；不冻结权威、不消耗 repair，也不证明数学。 |
| `math-research-solve.script.validate_attempt_package_v13` | **Current production, read-only package-closure checker only.** 重算 inventory、manifest、candidate/dependencies/artifact refs 与 Markdown SHA；PASS 不是 verifier verdict 或 evidence grade。 |
| `math-research-solve.script.math_research_migrate_v12_to_v13` | **Current production adapter boundary only.** 校验项目本地迁移适配器的绝对路径与精确哈希并转发受控动作；具体准备、独立审查绑定、同卷交换、条件回滚和恢复语义由外置适配器负责，Skill 不嵌入项目答案。 |
| `math-research-solve.script.project_core_cognition_v13` | **Current production, bounded cognition generator only.** 只消费绑定后的 objective/map/attempt-local 输入并生成压缩工作认知；不是权威 head 或证明。 |
| `math-research-solve.script.validate_research_map` | **Current production, structural map/result-export validator only.** 检查绑定、链接、资产和导出门禁；独立数学语义复核仍须另行完成。 |
| `math-research-solve.script.map_semantic_review_v1` | **Current production, deterministic map-review closure validator only.** 准备最小化 packet/ticket，验证 fresh-subagent 结果与三轮 lineage，并重算最终 closure；不派发 reviewer、不修改研究地图、不证明数学，也不自行授予发布权威。 |
| `math-research-solve.script.window_authoring_preflight_v13` | **Current production, non-authoritative authoring preflight only.** 区分 review document/raw digest，拒绝 project 内 worker 输出，检查 authoring tree 的 artifact-class byte budgets，并验证 `WINDOW_CLOSE` planning/commit manifests 分离；不生成数学、不开启 window、不写项目或授予发布权威。 |
| `math-research-solve.script.invoke_math_research_startup_v3` | **Current production, read-only classifier only.** 可严格读取 `project.json` 及其 generation pointers、执行 legacy terminal no-op 分类；不得 New/Resume/Goal mutation。 |
| `math-research-solve.script.build_math_research_legacy_successor_v8` | **Current production, non-authoritative staging helper only.** 在模型确认 current Goal/normalized nonexpanded envelope 后，严格读取 legacy archive，生成 hash-bound effective envelope、control map、lineage、Contract/run 与 generation candidates；Goal-agnostic，永不替换 `project.json`，不授权 successor。 |
| `math-research-solve.script.commit_math_research_head_v8` | **Current production, cooperative guarded mutation helper only.** 在模型 fresh Goal gate 之后验证 expected-old hash/generation 与 candidate pointers，使用 named mutex 和 same-directory flushed atomic replace 提交最终 `project.json` head；仅序列化 cooperating writers，不排除任意 non-cooperating writer；Goal-agnostic，不授权业务动作。 |
| `math-research-solve.script.invoke_math_research_migrate_v8_to_v10` | **Current production, Goal-agnostic migration harness only.** `inspect/prepare` 冻结输入与计划；`freeze` 只 create-new 写入 v8 迁移标记并读回；`verify` 重哈希 predecessor/successor。它不证明 Goal、不做数学、不消耗 attempt/audit/round。 |
| `math-research-solve.script.invoke_math_research_startup_v4` | **Current production, read-only classifier only.** 通过共享引擎执行 v9 Auto/Full audit；v3-v8 原样委托 Startup v3；不得写项目或证明 Goal。 |
| `math-research-solve.script.invoke_math_research_ticket_preflight_v8` | **Current production, read-only preflight only.** 检查 v8 source requirements、input/read closure 与可选 access log，输出 `fork_turns=none` capsule；不派发 worker。 |
| `math-research-solve.script.prepare_math_research_successor_v9` | **Current production, non-authoritative staging only.** 检查 unchanged envelope、remaining budgets 与 predecessor head，在项目外生成 v9 successor plan；不写 predecessor/successor head。 |
| `math-research-solve.script.prepare_math_research_transition_v9` | **Current production, non-authoritative staging only.** 只调用共享状态引擎生成规范 state/event/manifest/head candidates；不证明 Goal、不切 head。 |
| `math-research-solve.script.commit_math_research_transition_v9` | **Current production, cooperative guarded mutation helper only.** 在 Host fresh Goal gate 之后验证 plan、expected-old head 与 immutable bytes，create-new 发布并最后替换/read-back `project.json`；Goal-agnostic，非通用 writer isolation。 |
| `math-research-solve.script.invoke_math_research_startup_v5` | **Current production, read-only classifier only.** 通过 v10 共享状态引擎分类；必要时委托冻结的 v3-v9 startup；不得写项目、证明 Goal 或启动研究。 |
| `math-research-solve.script.invoke_math_research_worker_dispatch_preflight` | **Current production, read-free topology preflight only.** 检查 project/ticket/Host workspace/execution workspace 的路径关系，拒绝外部项目直接 collaboration dispatch 与 staging-only workspace；不读取票据、不请求授权、不派发 worker。 |
| `math-research-solve.script.invoke_math_research_execution_topology` | **Current production, Goal-agnostic topology and consumer probe only.** 在实际 worker topology 读取/哈希输入并写 staging probe，由 ingest/publisher 独立重开并写根继承 probe，再由长期桌面/应用 consumer principal 递归重开；也用于发布后 consumer readback。输出短时 receipt 或只读结果，不证明 Goal、不授予权限、不启动数学工作。 |
| `math-research-solve.script.invoke_math_research_ticket_preflight_v10` | **Current production, read-only preflight only.** 检查 v10 ticket、full-context closure、scope 与 worker access log；不派发 worker，不授权研究。 |
| `math-research-solve.script.prepare_math_research_successor_v10` | **Current production, non-authoritative staging only.** 检查 unchanged envelope、remaining budgets 与 predecessor head，在独立 successor root 生成 v10 successor plan；不写 predecessor/successor head。 |
| `math-research-solve.script.prepare_math_research_transition_v10` | **Current production, non-authoritative staging only.** 通过 v10 共享状态引擎生成 state/event/manifest/head candidates；不证明 Goal、不切 head。 |
| `math-research-solve.script.commit_math_research_transition_v10` | **Current production, cooperative guarded mutation helper only.** 在 Host fresh Goal gate 之后验证 plan、expected-old head 与 immutable bytes，create-new 发布并最后替换/read-back `project.json`；Goal-agnostic，非通用 writer isolation。 |
| `math-research-solve.script.run` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.launch_math_research` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.stop_math_research` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_cycle` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_project` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_startup_v1` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_startup_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.launch_math_research_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.stop_math_research_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_cycle_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_project_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_canary_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_legacy_v1_compat_migration` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume/migration authority. |
| `math-research-solve.script.launch_math_research_legacy_v1_compat` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_cycle_legacy_v1_compat` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_legacy_v1_compat_canary_host` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_legacy_v1_control_path_amendment_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume/amendment authority. |
| `math-research-solve.script.launch_math_research_legacy_v1_compat_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |
| `math-research-solve.script.invoke_math_research_legacy_v1_compat_canary_host_v2` | Retired historical telemetry/parse label only; MUST NOT invoke; no New/Resume authority. |

旧 phase 名称可以出现在历史 telemetry 或固定 regression fixture 中；这不允许当前 v8 workflow 包装、调用或恢复相应脚本。v8 successor 由当前模型 Goal Host 授权，使用 current production builder 做 non-authoritative staging、head helper 做最终 guarded activation；不借用任何 retired script phase。

## 允许字段

| 字段 | 类型 | 边界 |
|---|---|---|
| `mode` | `name` | 不含业务内容的分类。 |
| `operation` | `name` | 不含业务内容的分类。 |
| `write` | `boolean` | 是否写入。 |
| `file_count` | `nonnegative_integer` | 非负计数。 |
| `candidate_count` | `nonnegative_integer` | 非负计数。 |
| `byte_count` | `nonnegative_integer` | 非负计数。 |
| `harness_call_count` | `nonnegative_integer` | 非负计数。 |
| `result_count` | `nonnegative_integer` | 非负计数。 |
| `change_count` | `nonnegative_integer` | 非负计数。 |
| `warning_count` | `nonnegative_integer` | 非负计数。 |
| `error_count` | `nonnegative_integer` | 非负计数。 |

禁止记录 `path`、`title`、`note_title`、`query`、`body`、`excerpt`、`heading`、`diff`、`command`、`exception_text`、`resource_id`、`raw_file_hash` 和 `tool_output`。Observer 失败或超时不得改变业务命令的输出、退出码或文件行为。
