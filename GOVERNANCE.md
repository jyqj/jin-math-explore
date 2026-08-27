# 仓库治理规范

版本：`jin-math-governance/v1`

本文件规定 `jin-math-explore` 的治理宪章；数学权威的具体边界仍由 [`PROGRAM_CHARTER.md`](PROGRAM_CHARTER.md)、Project 状态和证据 receipt 决定。详细并发协议见 [`program/multi-agent-governance.md`](program/multi-agent-governance.md)。

## 1. 治理目标

GitHub 被用作可审计的多 Agent 协作底座，而不是模型共识系统。治理优化以下性质：

- 多个 Agent 可以在不重叠的冲突域中并行工作；
- 同一目标、同一写集或同一数学 authority 不发生静默双写；
- 每次权威变化都绑定精确 base、diff、证据、执行身份和审查边界；
- Agent 中断、过期、上下文丢失或工具失败后，工作可由仓库状态恢复；
- 任何协调便利都不能降低数学证据、独立验证或可复现性标准。

## 2. 五个平面

| 平面 | GitHub / 仓库对象 | 权威边界 |
|---|---|---|
| 协调平面 | Issue、sub-issue、dependency、Project view、lease comment | 谁在做什么、阻塞关系和短期写入意图；不是数学证据 |
| 执行平面 | branch、worktree、commit、checkpoint、handoff | 临时工作和可恢复中间状态；未合并内容不拥有发布权威 |
| 发布平面 | 受保护 `main`、squash-merged PR | 已发布的仓库状态变化；数学等级仍由 Project claim/receipt 决定 |
| 数学平面 | objective、Project CAS heads、冻结 candidate、verification receipt | 数学目标、认识和证据的唯一权威 |
| 自动化平面 | schema、validator、CI、ruleset | 机械契约和变更边界；不能证明数学语义 |

不得用 Issue 标签、PR approval、CI PASS、模型数量或聊天结论替代数学平面。

## 3. 不可破坏的治理不变量

1. **一项工作一个协调 Issue。** 每个 merge-intended PR 必须绑定一个开放的 work packet。
2. **一个 branch 一个写入 owner。** 其他 Agent 通过独立 branch 和显式 handoff 协作，不共同推送同一 branch。
3. **先声明写集，再产生写入。** PR 的机器可读 coordination manifest 必须覆盖完整 diff，且不得用通配符占用仓库。
4. **冲突域内单写。** 全局协议、同一 Project authority、同一 candidate 或同一 computation job 的不兼容写入必须串行化。
5. **乐观并发必须绑定 base。** lease 和 PR 都记录完整 40 位 base SHA；base 变化后重新读取、rebase、续租并重跑检查。
6. **Agent 身份按执行上下文记录。** GitHub username 不是 Agent 身份，也不能证明 verifier 独立；使用 `actor.id + actor.run_id + role`。
7. **求解与验证按上下文隔离。** verifier 只读取冻结 candidate、依赖和 ticket，不继承 solver 对话或修改候选。
8. **协调状态不成为第二 authority。** lease、Project board 和调度器不能推进数学 head。
9. **失败必须可见。** 过期 lease、Agent 中断、冲突、撤回、部分 handoff 和未解决风险不得从历史中删除。
10. **主分支只经 PR。** `main` 保持受保护、strict required checks、resolved threads 和 squash merge；例外必须公开记录并立即恢复保护。

## 4. 决策权

- 仓库所有者对资源、权限、治理版本和紧急处置拥有最终运营决策权，但不能凭此提升数学 claim。
- Program steward 负责拆分 work packet、声明依赖、授予或撤销运营 lease、安排 integrator；不能产生数学结论。
- Solver、source auditor、compute runner、independent verifier、reconciler 和 protocol maintainer 只在各自 ticket 与写集中行动。
- Integrator 可以整合已交付工件和解决机械冲突，不能把未验证输出升级为更高证据等级。
- 自动化可以拒绝不满足契约的变更，不能批准数学语义。

## 5. 变更进入 `main` 的最小门槛

所有 PR：

- 绑定 work packet Issue 与有效 lease；
- branch、title 和 changed-file scope 满足 `scripts/pr_policy.py`；
- PR body 含 `jin-math-agent-coordination/v1` manifest；
- manifest 的 `base_sha` 等于当前 PR base，声明写集覆盖且只覆盖实际 diff；
- 明确 actor/run/role、independence、handoff 和未解决 blocker；
- required checks 通过，review thread 已解决，分支与最新 `main` 一致；
- squash merge 后删除临时 branch。

数学 PR 还必须满足 `PROGRAM_CHARTER.md`、`program/evidence-policy.md` 和 Project 状态机规定的全部冻结、绑定、验证与 `cannot_imply` 要求。

## 6. 治理修改与紧急例外

治理采用版本化变更：改变 authority、独立性或冲突模型为 major；兼容地新增角色、字段或检查为 minor；澄清文字为 patch。治理文档使用 `[program]` PR；脚本、schema、模板、CI 或 Skill 使用 `[infra]` PR。不得在同一 PR 中修改治理协议并发布依赖新协议的数学结果。

紧急例外必须由仓库所有者在 Issue 和 PR 中写明：触发原因、临时绕过、影响范围、恢复步骤和事后审计。无记录的“先合并再解释”无效。
