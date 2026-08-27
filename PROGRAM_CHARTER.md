# AI 数学研究计划章程

## 1. 目标

本计划批量研究长期、困难、可能开放的数学问题。系统优化目标不是制造答案数量，而是持续增加以下可审计资产：

1. 精确定义的问题；
2. 可复用的已验证结果；
3. 诚实的失败边界和负面知识；
4. 可复现计算；
5. 可恢复的研究地图和因果记忆；
6. 经独立审查的完成候选。

## 2. 权威层级

| 对象 | 权威范围 |
|---|---|
| GitHub Issue / Project | 运营队列和讨论，不构成数学证据 |
| `registry/projects/<ID>.json` | 全局运营投影和项目定位 |
| 项目 `objective-core.json` | 不可变数学目标 |
| 项目 research authority head | 已提升的项目数学认识 |
| 项目 execution state head | 窗口、尝试、队列和验证中的工作 |
| 合并到 `main` 的 PR | 已发布状态变化；数学等级仍由 claim/receipt 决定 |
| CI | 结构、绑定、哈希和有限复现；不证明数学语义 |
| 独立 verifier | 对冻结候选和明确范围给出数学审查 |

任何聊天、模型自评、Issue 标签、PR 合并或 CI PASS 都不能单独把 claim 提升为已证明。

## 3. 多项目隔离

- 一个 Project 对应一个不可变数学目标。
- 一个 Project 同时最多有一个权威活动窗口。
- 不同 Project 可以并行运行。
- Sibling attempts 不得读取彼此未验证的 staging。
- 跨项目结果必须先在来源项目获得独立验证，再由目标项目通过 import proposal 重新核查假设和定义。
- 全局 catalog 是生成视图，不是状态所有者。

## 4. 研究窗口

每个活动窗口冻结一个来源地图和恰好三个不同语义指纹：

```text
(proof_object, mechanism_family, quantifier_strategy)
```

三个尝试可串行或并行，但必须分别形成冻结 candidate、依赖、计算产物、证据边界和 verifier 结果。窗口只有在三个 reconciliation package 完整时才能关闭。

## 5. 证据纪律

至少区分：

- `conjecture`
- `heuristic`
- `numerical_evidence`
- `bounded_check`
- `exact_check`
- `proof_candidate`
- `independently_verified`
- `verified_refutation`
- `verified_impossibility_boundary`
- `withdrawn`

每个非平凡 claim 必须记录量词范围、假设、依赖、证据和 `cannot_imply`。有限范围结果不得升级为无限量词结论；CAS 成功求值不得自动升级为证明。

## 6. 完成

项目完成要求一个覆盖全部目标量词的冻结候选，并通过三个相互隔离的终局审计：

1. quantifier / coverage；
2. strategy / soundness；
3. tool / reproducibility。

完成发布后项目数学 head 永久关闭。对目标的语义修改必须建立新 Project 或显式 fork。

## 7. 研究计划控制层

`$math-research-program` 可以分配资源、选择下一个窗口、管理 verification debt 和计算队列，但不能：

- 产生或提升数学 claim；
- 用模型成功概率作为数学证据；
- 绕过 Project 内部状态机；
- 把一个 Project 的结论无审查复制到另一个 Project；
- 因运行时间较长而擅自降低用户要求的证据标准。

## 8. 变更原则

- 数学研究 PR 与协议/Skill/CI PR 分离。
- 先合并协议变更，再由后续 PR 使用新协议。
- 对同一 Project，推荐一个关闭窗口对应一个 PR。
- 失败尝试如果形成精确失败边界、反例或可复用工具，应当保留，而不是从历史中删除。
