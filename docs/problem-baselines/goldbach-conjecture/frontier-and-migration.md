# Frontier 与迁移计划

## 1. 本次实际迁移

本 baseline PR 完成：

- 绑定 v0.3 的主要原文件、机器对象和证书哈希；
- 保存 100-entry legacy claim set 的内容承诺；
- 继承关键 `GB-*` ID、证明问题和依赖状态；
- 刷新主要 2024–2026 来源的 arXiv 版本；
- 把下一窗口固定为三个可证伪 attempt；
- 明确不能创建手工 v13 Project head。

尚未完成：

- 精确 100-entry JSON 原始字节的 GitHub 内嵌；
- 原计算脚本、日志、区间证书和 DAG 原始文件的仓库归档；
- source-audited candidate admission；
- 受控 Project genesis。

## 2. 基础设施阻塞

正式 `projects/P-XXXX--.../` 仍受以下 Issue 控制：

- `#4`：production v13 Project genesis adapter；
- `#20`：pregenesis admission/runtime 等五层契约；
- `#23`：知识节点与生成 catalog 的原子 PR family。

在这些门完成前，不手工拼装 `objective-core.json`、research/execution heads 或 registry authority。

## 3. Stage 4：解析接口闭合

### `A-GB-L35-0001` — Lemma 3.5 调用编译器

对 `G_9,G_11,G_12` 的每一个 dyadic block 冻结：

```text
block_id
paper_location
M, N, nu
alpha_m, beta_n
support
divisor bound
condition (3.2)
small-prime exclusion
nu range
well-factorable weight
uniformity/constants
verdict
earliest failure
```

输出 verdict 只能是：

```text
PASS / REPAIRABLE / FAIL / INCONCLUSIVE
```

### `A-GB-G7-0001` — `G_7` 边界层

精确比较：

- 印刷域；
- Lemma 2.5 合法域；
- 宽度 \(\eta=B\log\log N/\log N\) 的移动边界层；
- 数值证书实际积分域。

目标是证明或否定：

\[
\operatorname{Loss}_{G_7}(N,\varepsilon)
=o\!\left(\frac{C(N)N}{\log^2N}\right).
\]

### `A-GB-ERR-0001` — 统一误差与共同 \(N_0\)

建立带符号误差账本：

```text
source equation
main-term direction
error expression
constant dependencies
uniformity scope
downstream coefficient
worst harmful sign
absorption condition
effectivity
```

先选 \(\varepsilon_0\)，再固定 \(\varepsilon\)，最后选共同 \(N_0(\varepsilon)\)。区分：

- 非有效渐近存在；
- 半显式阈值；
- 完全显式阈值。

## 4. Reconciliation

- 三项 PASS：只形成 `1+1.9` 全篇独立审计候选；
- 某项 REPAIRABLE：冻结失败版本，另开 repair attempt；
- 某项 FAIL：保存最小失败点及所有仍有效上游结果；
- 共同 \(N_0\) INCONCLUSIVE：区分未显式常数、量词循环和同阶误差；
- 任何结果都不能在没有新 verifier 的情况下升级为 independently verified。

## 5. 后续窗口

### Stage 5：模板能力边界

先自动复现 \(a=1.9\)，再测试 `1.51 / 1.50 / 1.49`，量化组合相变、负质量和分布要求。成功结果可以是更优参数，也可以是当前模板的 verified impossibility boundary。

### Stage 6：局部奇偶敏感桥梁

从实际筛权支持反推最小 Möbius 去相关命题，并证明带显式参数的条件蕴含；同时用有限模型排除过弱平均条件。

### Stage 7：异常集结构化

不只继续压低 \(E(X)\) 指数，而是寻找异常数必须满足的多尺度、剩余类、奇异级数或例外零约束，以及这些约束之间的冲突或传播机制。

## 6. 留存纪律

每次尝试必须留下：

- 冻结输入和 source hash；
- 精确 statement、量词和假设；
- candidate、代码、命令和输出 hash；
- verdict 与最早失败点；
- `cannot_imply`；
- 旧 `GB-*` 到新 claim 的关系；
- DAG delta；
- 负面知识与 reopen condition。

“没有证明终局命题”不能成为删除失败尝试的理由。
