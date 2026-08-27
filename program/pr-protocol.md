# Pull Request protocol

## 一个 Issue、一个 owner、一个发布事务

每个 merge-intended PR 绑定一个 work packet Issue、一个获胜 lease 和一个 branch owner (`actor.id + run_id`)。多个 Agent 不共同 push 同一 branch；通过独立 branch、commit SHA 和 handoff 协作。

研究 PR 推荐以完整关闭的 window 为单位。Attempt staging 可以位于独立 worktree/branch，但不分别推进 `main` 上的项目 authority。

## Coordination manifest

PR body 必须包含一个 `jin-math-agent-coordination/v1` JSON block，字段和示例见 [`multi-agent-governance.md`](multi-agent-governance.md)。至少绑定：

- coordination Issue；
- actor kind/id、run ID 和 role；
- lease ID、mode、expiry、observed base SHA；
- read/write set；
- independence 声明；
- handoff status 和摘要。

PR diff 必须完全位于声明写集中；每个写集条目必须覆盖实际 changed file。base branch 前进、lease 续期、actor/run 更换或写集变化后，更新 manifest 并重新运行 CI。

## 数学 PR 必须绑定

- Project ID；
- objective commitment SHA-256；
- base commit；
- expected project/research/execution heads；
- window ID；
- 三个 attempt package；
- verifier receipts；
- reconciliation result；
- map/memory/route-review 变化；
- computation handoffs；
- evidence grades 和 `cannot_imply`。

## 分离原则

- `[infra]` PR 可以改变协议、schema、Skill、模板或 CI，但不得同时发布依赖新规则的数学结论。
- `[program]` PR 只改变治理/调度文档，不推进 Project authority。
- `[window]` PR 使用 `main` 上已存在的协议。
- `[terminal]` PR 不得夹带协议修改或额外研究。
- `[verify]` PR 的 actor role 必须为 `independent_verifier`，使用新 run/context，candidate 只读。
- Integrator 可以解决机械冲突和组装冻结工件，不能修改 evidence grade 来覆盖 receipt。

## Genesis and state

- `[P-XXXX][genesis]` 是唯一可以新增 `objective-core.json` 的 PR 类型；目标 Project 目录和 registry entry 必须同时首次新增。
- `[P-XXXX][state]` 只处理 park、reopen、compute-wait 等运营状态，不得修改 objective 或借机提升数学 claim。
- 目录、分支、lease 和 changed-files 边界见 [`git-workflow.md`](git-workflow.md)。

## Ready-to-merge gate

- work packet 契约未被未记录地改变；
- Issue 中没有更早的不兼容 active lease，当前 lease 未过期；
- manifest base SHA 等于当前 PR base，strict checks 已在最新 base 通过；
- PR title/branch/path、coordination manifest/write set、repository、catalog 和 Skill lock 检查通过；
- handoff 完整，blocker 和 review thread 已解决；
- 数学 PR 的 frozen hashes、receipts、reproduction 和 `cannot_imply` 完整；
- 使用 squash merge，合并后 release lease 并删除 branch。

CI、approval、lease 或 merge 本身都不改变数学证据等级。
