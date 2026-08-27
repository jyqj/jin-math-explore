# Project lifecycle

## 两个正交状态轴

运营状态和数学状态必须分开。

### `operational_status`

```text
candidate
source_audit
objective_freeze
active
review_gate
compute_wait
parked
terminal_audit
closed
```

### `mathematical_status`

```text
unknown
open
partial
proof_candidate
refuted
complete
```

例如一个项目可以是 `operational_status=parked` 且 `mathematical_status=open`。停工不等于解决或反驳。

## 晋升为 Project

候选问题必须完成：

1. 精确 statement、domain、quantifier order 和 assumptions；
2. 原始来源与当前开放状态核查；
3. 已知结果和等价表述边界；
4. evidence/completion standard；
5. 至少一个可验证 frontier；
6. 唯一 Project ID。

## 活动窗口

每个 Project 同时最多一个权威活动窗口。窗口关闭 PR 合并后，调度层才可以从新 authority 选择下一窗口。

## Park / Reopen

Park 必须记录：

- 当前阻塞；
- 已排除的范围；
- 未排除的范围；
- reopen condition；
- 依赖或计算需求；
- 最近 source audit 日期。

Reopen 需要新证据或明确满足 reopen condition，不能只因模型换了说法。
