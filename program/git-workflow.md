# Git workflow

## Stable identity and temporary work

```text
长期身份：Project ID + Project directory + content hashes
临时工作：short-lived branch / worktree
权威发布：merged Pull Request
```

每道题使用一个长期 Project 目录和一个 registry 文件，不使用常年不合并的问题分支：

```text
projects/P-0001--example-problem/
registry/projects/P-0001.json
```

Project 根严格只有 `project.json`、`README.md`、`研究地图/`、`.research/`。分支不是稳定身份，也不能替代 Project 状态机。

## Branch names

分支名全部使用小写：

```text
source/p-0001/audit-2026-08-28
genesis/p-0001/objective-v1
research/p-0001/w-0001-close
attempt/p-0001/w-0001/a-01-spectral
verify/p-0001/w-0001/v-01
state/p-0001/park
terminal/p-0001/t-0001
infra/project-genesis-v1
program/scheduler-v1
shared/s-0001
```

Attempt branches/worktrees are temporary staging. 一个关闭窗口最终只通过 `research/p-XXXX/w-XXXX-close` 向 `main` 发布一个 window PR。

## PR types

| Type | Meaning |
|---|---|
| `[program]` | 全局政策，不推进数学 authority |
| `[infra]` | Schema、Skill、脚本、CI，不推进 Project authority |
| `[P-XXXX][source]` | 来源或开放状态审计 |
| `[P-XXXX][genesis]` | 首次创建 Project 并冻结 objective |
| `[P-XXXX][state]` | Park、reopen、compute-wait 等运营状态变化 |
| `[P-XXXX][window]` | 发布一个完整关闭的三尝试窗口 |
| `[P-XXXX][verify]` | 对冻结候选增加独立验证 receipt |
| `[P-XXXX][terminal]` | 终局候选与三项审计 |
| `[shared][S-XXXX]` | 发布一个已独立验证的跨项目结果 |

## Isolation

Git branch/worktree 只提供版本与写入隔离，不自动提供信息隔离。需要独立性时：

- attempt 冻结前不推送远端 staging；
- 不向 worker 暴露 sibling worktree/branch；
- verifier 只接收冻结 candidate、dependency hashes 和 ticket；
- verifier 不读取 solver 对话，也不修改候选；
- 受限 token、挂载或独立 clone 用于需要真实读取隔离的任务。

## Merge and cleanup

- `main` 只接受 PR；基础仓库初始化等明确授权的例外需立即恢复保护。
- 使用 squash merge，使一个 PR 对应 `main` 上一个权威状态转换。
- 合并后删除远端临时分支并清理本地 worktree。
- Catalog 从 registry 生成，不手工编辑；并行 PR 在合并前更新 base 并重新生成。

## Mechanical policy

`scripts/pr_policy.py` 根据 PR title、branch 和 changed files 检查：

- PR 类型与 branch 前缀一致；
- 普通 Project PR 只触及一个且匹配的 Project；
- objective 只能在 `[genesis]` 中新增，不能修改；
- `[infra]`/`[program]` 不推进 Project authority；
- `[verify]` 不修改 receipt 绑定的 candidate；
- `[genesis]` 必须新增 registry、project head 和 objective；
- 数学 PR 不能夹带协议、Skill 或 CI 变更。

PASS 仍只证明变更范围和绑定规则，不证明数学正确。
