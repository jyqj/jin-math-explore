# 来源审计

**冻结日期：** 2026-08-31  
**审计类型：** pre-genesis source/version audit  
**数学验证：** 未执行全篇独立 proof verification

## 1. 当前版本锁

| Key | 冻结版本 | 版本事实 | 本仓库状态 |
|---|---|---|---|
| `LiLiu2026` | `arXiv:2606.05224v2` | 2026-08-08 修订；摘要声称无条件 `(1+1.9)` 与条件 `(1+1.4)` | `preprint claim` |
| `BhowmikGrimmelt2026` | `arXiv:2607.27282v2` | 2026-08-13 修订；修正排印错误，注明拟刊 Analysis Mathematica | `source map / survey`, 不自动验证其引述 |
| `BordignonJohnstonStarichkova` | `arXiv:2207.09452v6` | 2025-06-25 修订；摘要给出显式 Chen 阈值 | `established-source candidate` |
| `Helfgott2014` | `arXiv:1312.7748v2` | 2014-01-17 修订；证明三元哥德巴赫 | `established` |
| `Zhao2026` | `arXiv:2511.05631v2` | 2026-01-23 修订；摘要声称 \(E(X)=O(X^{7/10})\) | `preprint claim` |
| `AlsetriShao2024` | `arXiv:2405.18576v2` | 2024-09-19 修订；局部密度阈值 \(1/2\) | `paper/to appear` |
| `Cantarini2026` | `arXiv:2607.09110v1` | 条件于 GRH、弱 Gonek–Hejhal 及函数空间权重的平均结果 | `conditional preprint` |
| `GrimmeltTeravainen2026` | `arXiv:2508.16400v2` | 2026-07-29 修订；两个 Chen primes 的 power-saving exceptional set | `adjacent-route preprint` |

## 2. 对 v0.3 来源状态的修正

v0.3 把 Bhowmik–Grimmelt 锁在 `v1`。本次来源刷新发现当前版本为 `v2`；后续引用 theorem number、页码或措辞必须以 v2 为准。

Li–Liu 当前仍为 `v2`，与旧账本使用的版本一致。

## 3. 来源与数学权威分离

- arXiv 页面只证明版本、作者、摘要和提交历史；
- “to appear” 不替代对本项目实际使用命题的适用性检查；
- 作者在摘要中写“we prove”仍先作为来源报告，不能自动成为仓库独立验证结果；
- 综述中的历史 best bound 需要在影响 frontier 时继续追溯原始论文；
- 条件结果必须保存全部附加假设，不能只摘取结论指数。

## 4. 近期来源的精确边界

### Li–Liu

来源定义

\[
N=p+rq,\qquad r\le q^{a-1},
\]

并在摘要中声称无条件 `(1+1.9)`。v0.3 已验证部分数值和有限组合层，但 Lemma 3.5 逐 block 调用、`G_7` 边界层和共同误差仍开放，所以仓库不升级该主张。

### Zhao exceptional set

摘要声称

\[
E(X)=O(X^{7/10}),
\]

隐含常数无效。本基线保留为 `P`，因为旧项目没有完成全篇独立审计；即使成立，也仍允许无限多个异常偶数。

### Möbius-twisted Elliott–Halberstam

Cantarini 的结果带有 GRH、弱 Gonek–Hejhal 和指定 Sobolev/Hölder–Zygmund 权重条件，研究的是加权平均/对角版本。它可用于设计局部奇偶敏感假设，不能直接作为无条件二元哥德巴赫输入。

## 5. 未完成的 source debt

1. 为 `1+1.9` 冻结 v2 PDF/TeX 的原始字节 SHA-256；
2. 给 Lemma 2.5、3.5 和每次调用保存精确页码、公式和变量映射；
3. 比较 Bhowmik–Grimmelt v1→v2 对历史界和定理编号的变化；
4. 对 Zhao v2 的 \(7/10\) 证明做独立 source/proof audit；
5. 追溯 v0.3 中 \(0.72\) 基线到 Pintz 原始结果，而不永久依赖综述；
6. 对计算到 \(4\times10^{18}\) 的算法、代码和审计链建立独立 bounded-check receipt。

## 6. Primary locators

- https://arxiv.org/abs/2606.05224
- https://arxiv.org/abs/2607.27282
- https://arxiv.org/abs/2207.09452
- https://arxiv.org/abs/1312.7748
- https://arxiv.org/abs/2511.05631
- https://arxiv.org/abs/2405.18576
- https://arxiv.org/abs/2607.09110
- https://arxiv.org/abs/2508.16400
