# Contributing

## 变更类型

PR 标题使用以下前缀之一：

- `[program]`：全局政策或调度机制；
- `[infra]`：schema、脚本、CI 或 Skill；
- `[P-XXXX][window]`：关闭一个研究窗口；
- `[P-XXXX][source]`：来源或开放状态更新；
- `[P-XXXX][verify]`：独立验证；
- `[shared][S-XXXX]`：发布跨项目共享结果；
- `[P-XXXX][terminal]`：终局候选与审计。

## 研究 PR 约束

1. 绑定 Problem ID、objective SHA-256 和 base commit。
2. 列出所有新增或变化的 claim / attempt / verification ID。
3. 明确证据等级和 `cannot_imply`。
4. 计算产物必须有复现命令、版本、哈希和范围说明。
5. 独立 verifier 不得修改被审查候选。
6. 一个 PR 不得同时改变研究协议并依赖该新协议发布数学结论。

## 本地检查

```bash
make check
```

格式和 CI PASS 只证明机械契约通过，不代表数学结论正确。
