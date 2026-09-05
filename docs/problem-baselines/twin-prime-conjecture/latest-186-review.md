# 186 新结果：证据分层与待复核接口

**不是完整证明审查报告。** 本轮确认了论文的目标陈述和代码仓库公开的输入合同；尚未逐行审计分析证明，也未编译 Lean 或执行数值证书。

## 固定对象

论文：[OpenAI2026]，*Improved short gaps between primes*，稿内日期 2026-08-30，39 页；第 1 页 Thm. 1.1 / Cor. 1.2，及第 2 页 (1.5)。稿内日期不当作已经核实的首次公开时间。

配套仓库：[PrimeGaps1862026]，`openai/PrimeGaps186`，观察到的 commit：

```text
61340d0b74163003b32756bb16e91d9209a5e330
```

本轮已读 README 和此 commit 的 `comparator/main.json`。未把全体 Lean 源码、辅助 PDF、Python 运行输出和 FLINT 构建转写成本仓库已审计工件。PDF 字节 SHA-256 尚未取得，见来源债务。

## 三层结论

**论文层。** 论文陈述 $\mathrm{DHL}[40,2]$，并使用一个直径 186 的可容许 40 元组得到 $H_1\le186$。路线将分布估计、补余因子分解与扩大筛权支持域结合。这里记录作者给出的无条件数学结果声称，不另加 EH/GEH 假设。[OpenAI2026]

**形式化层。** Comparator 明确允许三个非基础输入：

```text
PrimeGap186.kloosterman3_bound
PrimeGap186.kloosterman2_correlation_bound
PrimeGap186.physical_integral_bounds
```

另允许 `propext`、`Quot.sound`、`Classical.choice` 三个基础项。后者与本项目特定的分析/数值输入分开计数；不能简单说“只有三个公理”而不说明口径。[PrimeGaps1862026, comparator/main.json]

**仓库验证层。** 本运行尚未复现任何 Lean 或 Python 证明链，因此记录 `independent_verification=not_performed`。上游 README 报告的通过状态只属于上游，不能借用为本运行的测试结果。

## 输入核对表

| 输入 | 上游给出的来源或内容 | 下一次应核对什么 |
|---|---|---|
| `kloosterman3_bound` | Deligne 型估计；README 指向 Katz, Thm. 4.1.1，归一化后绝对值不超过 3 | 素数及非零参数量词、除以 $p$ 的归一化、所有小特征 |
| `kloosterman2_correlation_bound` | README 指向 Fouvry–Kowalski–Michel, *The Friedlander–Iwaniec character sum*, Prop. 2 | 极点排除、$A=B$ 情形、标准化与 $8p\sqrt p$ 常数 |
| `physical_integral_bounds` | 104 个外层、45 个内层积分上界及 3 个 cap bounds | 每个目标与区间输出的一一对应、舍入方向、严格正余量及源码完整性 |

这些是上游陈述的接口；本轮未独立重读 Katz/FKM 的整个证明。形式化中尚未证明的输入，不必然是数学上未解决的猜想；但在完成接口核验前，也不能仅凭引用名称宣布它们已经被正确实例化。

## 复现障碍不得隐藏

README 的测试环境包括定制 FLINT 3.6.0 构建，修复 signed polynomial convolution，且该构建未随仓库捆绑。直接安装同版本号的普通环境不应宣称等价复现。数值程序的通过也不会自动消去 Lean axiom。[PrimeGaps1862026]

本次既未准备该环境，也未运行证书；不能承诺一个未经验证的运行时长。下一任务先锁定构建补丁与依赖，再决定是独立实现区间算法还是复现原程序。

## 最小审查任务，而非直接继续降数字

先冻结 `A-TP-186-INPUT-0001` 的任务定义：三个输入各一份“来源定理 → 数学归一化 → Lean statement → 实际调用”的矩阵；并把数值输入展开为逐条证书覆盖表。验收结论只能在明确范围内给出 PASS / FAIL / INCONCLUSIVE。

随后才检查分析层所有 $o(1)$ 是否在固定试验参数下统一小于严格余量。输入层 PASS 不等于全文 PASS；全文 PASS 不等于孪生素数猜想已解决。进一步将 $k=40$ 改小属于新的 solver attempt，不在此基线内虚构进展。
