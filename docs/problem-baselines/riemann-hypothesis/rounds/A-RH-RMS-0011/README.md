# 黎曼猜想研究档案：第 11 轮 RMS 传递

Attempt: `A-RH-RMS-0011`。日期：2026-09-06。工作 Issue：[#69](https://github.com/jyqj/jin-math-explore/issues/69)。
数学状态：**proof_candidate，未经独立验证**；发布性质：reference-only research archive。

## 本轮实际增量

沿用第 10 轮的周期盒指数模型，而非重新开始文献整理。将逐 Fourier 系数
估计改为归一化 Hilbert–Schmidt / 均方位移估计，消去一次不必要的
`sqrt(Q)` 损失。在有界深度、正简单点比例和既定单胞模型下，二尺度排除
所需的充分条件从 **`Q^2 delta -> 0` 放宽为 `Q delta -> 0`**。
其中 `Q` 是周期，`delta` 是归一化长尺度缺陷；这不是 ζ 零点的无条件结论。

同时给出同一模型内的循环缓慢应变族：简单点比例保持 `2/3`，长缺陷为
`O(1/Q)`，到任何共同整数陪集的最佳均方距离却恒为 `1/128`。
因此，全局相位中间估计里的周期因子不能全部删去。该反例不满足短尺度
预算，不能据此否定周期无关的二尺度路线。

另一项具体修补是证明最近陪集舍入后，每个格点的聚合质量至多为 4：
允许质量碰撞，不假装标号始终单射。这使矩阵传递常数不再随维数增长。

## 文件与证据

[完整候选证明](proof.md) 给出模型、归一化、显式常数、父级输入重推导、
充分条件、反例与审查范围；[历史恢复图](history.md) 记录 10 轮主链及来源。
[逐项结论](claims.json) 保留假设、量词、依赖和不能推出的事项。
[来源边界](source-scope.md) 区分原论文、父级候选与本轮推导。

实际执行了 120 个固定种子配置、4 个边界配置、370 次相位比较，
以及 10,080 个有理权重不等式、480 个精确舍入配置和周期六常数计算。
全部程序断言通过；浮点量含明确容差，不是区间证书或形式化证明。
最大有限矩阵重构残差约为 `9.64e-15`。完整输出在 [validation.json](validation.json)。

新常数不是对所有小周期都更优：`A=log(2), Q=6` 时旧阈值更强；
`Q=48,96,384` 时新阈值分别约为旧值的 `1.58,3.15,12.58` 倍。
保留旧估计，使用二者中较强者，不把渐近改进写成处处改进。

## 复现

需要 Python、NumPy、mpmath；本轮版本为 3.13.5 / 2.3.5 / 1.3.0。
在本目录运行：

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_rms_transfer.py --samples 120 --output /tmp/rh-rms-validation.json
python check_rms_transfer.py --check-package
```

重算输出写到临时文件，避免不同平台浮点末位改写冻结输出。
[计算记录](computation-record.json)、[计算交接](computation-handoff.json) 与
[九文件哈希清单](checkpoint.json) 区分数值检查、精确有限检查与候选证明。
哈希清单不循环包含自身；其 Git blob 和最终 commit 在 PR 中记录。

## 未完成的桥梁

本轮未证明周期无关的二尺度分离，未从真实 ζ 零点抽取单胞/周期表示，
未闭合来源权重、局部化、异常算子能量或算术矩预算，未提升任何无条件
零点比例，也未证明 RH。下一项明确任务是 `A-RH-LOC-0012`：用局部相位
而非共同全局相位处理应变与无锚点区域；其精确目标见 proof.md 第 8 节。

当前 PR 从 main 单独新增本档案，不修改冻结 staging、Project heads、知识
catalog、策略或验证 receipt。PR/CI 通过不等于数学独立验证。完整仓库本地
测试、上游 Lean 构建和隔离 verifier 均未执行；远端 CI 观察另在 PR 留存。
