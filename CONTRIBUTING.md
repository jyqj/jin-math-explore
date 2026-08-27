# Contributing

所有贡献者——人类、Agent 或 automation——先阅读 [`GOVERNANCE.md`](GOVERNANCE.md)、[`PROGRAM_CHARTER.md`](PROGRAM_CHARTER.md) 和 [`program/multi-agent-governance.md`](program/multi-agent-governance.md)。

## Work packet 与 lease

每个 merge-intended PR 必须绑定一个开放 Issue。Issue 应定义单一 deliverable、依赖、required role、authority boundary、observed base、read/write set、conflict domain、完成证据和 handoff。

写入前在 Issue 发布 `jin-math-lease:v1` claim，并二次读取评论确认没有更早的不兼容 claim。一个 branch 只由一个 `actor.id + run_id` 写入；其他执行者使用独立 branch 和显式 handoff。lease 是运营协调，不是数学权威。

## 变更类型

PR 标题使用以下前缀之一：

- `[program]`：全局政策或调度机制；
- `[infra]`：schema、脚本、CI、模板或 Skill；
- `[P-XXXX][window]`：关闭一个研究窗口；
- `[P-XXXX][source]`：来源或开放状态更新；
- `[P-XXXX][genesis]`：首次创建 Project 并冻结 objective；
- `[P-XXXX][state]`：纯运营状态变化；
- `[P-XXXX][verify]`：独立验证；
- `[shared][S-XXXX]`：发布跨项目共享结果；
- `[P-XXXX][terminal]`：终局候选与审计。

## PR coordination manifest

PR body 必须包含恰好一个 `jin-math-agent-coordination/v1` JSON block，声明：

- coordination Issue；
- actor kind/id、run ID 和 role；
- lease ID、mode、base SHA、expiry、read/write set；
- independence 状态；
- handoff status 与摘要。

`scripts/coordination_policy.py` 要求当前 PR base 与 manifest 一致，并验证完整 diff 被精确写集覆盖。它不验证 Issue 中谁赢得 lease，也不验证数学真理。

## 研究 PR 约束

1. 绑定 Problem ID、objective SHA-256 和 base commit。
2. 列出所有新增或变化的 claim / attempt / verification ID。
3. 明确证据等级和 `cannot_imply`。
4. 计算产物必须有复现命令、版本、哈希和范围说明。
5. 独立 verifier 使用新 run/context，不读取 solver 对话且不得修改被审查候选。
6. 一个 PR 不得同时改变研究协议并依赖该新协议发布数学结论。
7. 一个 Project authority PR 只能触及匹配 Project、registry entry 和生成 catalog；attempt staging 由最终 window integrator 统一发布。

分支名、冲突域和类型边界见 [`program/git-workflow.md`](program/git-workflow.md)。

## Handoff

Agent 中断、任务转交或 PR ready 时记录：lease、actor/run/role、branch/head/base SHA、完成范围、changed paths、命令与测试结果、冻结 artifacts/hashes、失败边界、blockers 和建议下一角色。接收者必须重新读取和验证，不能只相信摘要。

## 本地检查

```bash
make check
```

PR 环境还会运行 title/branch/path policy 和 coordination manifest/write-set policy。格式、lease、CI PASS 和 GitHub approval 都只证明运营或机械条件，不代表数学结论正确。
