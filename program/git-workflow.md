# Git workflow

## Stable identity and temporary work

```text
长期身份：Project ID + Project directory + content hashes
协调身份：work packet Issue + lease ID + actor/run/role
临时工作：single-owner short-lived branch / worktree
权威发布：merged Pull Request
```

每道题使用一个长期 Project 目录和一个 registry 文件，不使用常年不合并的问题分支：

```text
projects/P-0001--example-problem/
registry/projects/P-0001.json
```

Project 根严格只有 `project.json`、`README.md`、`研究地图/`、`.research/`。分支不是稳定身份，也不能替代 Project 状态机。

## Before branching

1. 读取 `GOVERNANCE.md`、适用协议、当前 Issue / dependencies、所有 active lease 和相关 open PR；
2. work packet 声明单一 deliverable、base SHA、read/write set、conflict domain、required role 和完成证据；
3. 发布有限期 `jin-math-lease:v1` claim，再次读取评论确认没有更早的不兼容 claim；
4. 从声明 base 创建 branch。一个 branch 只允许一个 `actor.id + run_id` 写入；其他 Agent 用独立 branch 和 handoff。

Issue lease 只协调写入意图。最终陈旧写入由 Git base、strict checks、Project CAS heads 和 PR scope policy 拒绝。

## Branch names

分支名全部使用小写，并在全局/基础设施任务中包含 Issue：

```text
source/p-0001/audit-2026-08-28
genesis/p-0001/objective-v1
research/p-0001/w-0001-close
attempt/p-0001/w-0001/a-01-spectral
verify/p-0001/w-0001/v-01
state/p-0001/park
terminal/p-0001/t-0001
infra/i-0004/project-genesis-v1
infra/i-0015/multi-agent-governance-v1
program/i-0009/candidate-selection-v1
shared/s-0001
```

Attempt branches/worktrees 是单写临时 staging。一个关闭窗口最终只通过 `research/p-XXXX/w-XXXX-close` 向 `main` 发布一个 window PR。Agent 之间通过 branch/head SHA 和 Issue handoff 交换冻结工件，不共同 push 同一 branch。

## PR types

| Type | Meaning |
|---|---|
| `[program]` | 全局政策，不推进数学 authority |
| `[infra]` | Schema、Skill、脚本、CI、模板，不推进 Project authority |
| `[P-XXXX][source]` | 来源或开放状态审计 |
| `[P-XXXX][genesis]` | 首次创建 Project 并冻结 objective |
| `[P-XXXX][state]` | Park、reopen、compute-wait 等运营状态变化 |
| `[P-XXXX][window]` | 发布一个完整关闭的三尝试窗口 |
| `[P-XXXX][verify]` | 对冻结候选增加独立验证 receipt |
| `[P-XXXX][terminal]` | 终局候选与三项审计 |
| `[shared][S-XXXX]` | 发布一个已独立验证的跨项目结果 |

每个 merge-intended PR 还必须绑定一个 work packet Issue，并在 body 中提供 `jin-math-agent-coordination/v1` manifest。

## Conflict domains

- `global-serial`：`PROGRAM_CHARTER.md`、`GOVERNANCE.md`、`program/`、`schemas/`、`scripts/`、`.github/`、Skills 与 lock manifest；必须独占写入。
- `project-authority:P-XXXX`：Project head、匹配 registry 和不可分割 window transition；同一 Project 串行。
- `attempt:P/W/A`：不同 attempt 可分片并行，各自单写且信息隔离。
- `verification:P/C/V`：candidate 只读，receipt 路径由独立 verifier 单写。
- `compute:P/W/J`：job ID、checkpoint 和 result 单写，恢复幂等。
- `generated:catalog`：不单独占用，由当前 merge-intended PR 在最新 base 重新生成。

不同 Project、不同 attempt、不同 verifier receipt 或不同 compute job 只有在写集和语义事务不重叠时才可并行。

## Isolation

Git branch/worktree 只提供版本与写入隔离，不自动提供信息隔离。需要独立性时：

- attempt 冻结前不向 sibling 暴露 staging；
- 不向 worker 挂载 sibling worktree/branch；
- verifier 使用新 `run_id`，只接收冻结 candidate、dependency hashes 和 ticket；
- verifier 不读取 solver 对话，也不修改候选；
- 受限 token、挂载或独立 clone 用于需要真实读取隔离的任务；
- GitHub username、不同模型名或不同 prompt 不能单独证明独立。

## Handoff

交接至少记录：lease ID、actor/run/role、branch/head/base SHA、完成范围、changed paths、测试命令和结果、冻结 artifact hashes、失败边界、blockers 和建议下一角色。接收者必须重新检查文件、hash 和 diff，不能把 handoff 摘要当作证据。

## Merge and cleanup

- `main` 只接受 PR；基础仓库初始化或 emergency 等明确授权的例外需在 Issue/PR 记录并立即恢复保护。
- 使用 squash merge，使一个 PR 对应 `main` 上一个权威状态转换。
- Required checks 使用 strict base；前序冲突域 PR 合并后，后续 PR 必须 rebase、更新 manifest base SHA、重新检查 lease 并重跑 CI。
- 合并后删除远端临时分支并清理本地 worktree；关闭未合并 PR 时发布 release/handoff。
- Catalog 从 registry 生成，不手工编辑；并行 PR 在合并前更新 base 并重新生成。
- PR ready 后 force-push 会使旧 review 与 handoff 失效；必须重新审查和运行检查。

## Mechanical policy

`scripts/pr_policy.py` 根据 PR title、branch 和 changed files 检查：

- PR 类型与 branch 前缀一致；
- 普通 Project PR 只触及一个且匹配的 Project；
- objective 只能在 `[genesis]` 中新增，不能修改；
- `[infra]`/`[program]` 不推进 Project authority；
- `[verify]` 不修改 receipt 绑定的 candidate；
- `[genesis]` 必须新增 registry、project head 和 objective；
- 数学 PR 不能夹带协议、Skill 或 CI 变更。

`scripts/coordination_policy.py` 根据 PR body、base 和 diff 检查：

- coordination manifest 恰好一个且为有效 JSON；
- actor/run/role、lease、expiry、base 和 independence 字段有效；
- write set 使用精确规范路径，无 glob 或路径穿越；
- 完整 diff 在声明写集中，且不存在未使用的过宽范围；
- global-serial 路径使用 `exclusive_write`；
- `[verify]` 声明新的 independent-verifier run、冻结 candidate 且无 solver context access。

PASS 仍只证明机械边界，不验证真实 lease winner、信息隔离实现或数学正确。
