# 黎曼猜想研究档案：第15轮，周期无关的洞区稳定性

Attempt: `A-RH-HSTAB-0015`。Issue: [#93](https://github.com/jyqj/jin-math-explore/issues/93)。
日期：2026-09-07。状态：**proof_candidate，尚未独立验证**。
本目录是 reference-only 研究档案，不推进 Project authority。

## 本轮增量

接续第14轮的精确问题 (28)，不再尝试恢复共同相位，而是证明一个中心行能量
恒等式，再结合“到两倍正交投影的距离”缺陷分解。得到无简单点周期模型的
候选稳定性定理：

```text
E_(3/4) >= (16/9) rho + (4/9) rho^2 - (16 sqrt(2)/9) sqrt(delta).
```

误差常数不依赖周期，也不依赖深度上界；rho 和能量均按单胞归一化。
精确等号分类不再是这一推导的必要输入。定理仅适用于 marks 0/2 的洞区，
不能直接套用到含简单点的整体模型。

本轮进一步补齐有限块周期化、带符号边界误差和缺陷平均步骤，将洞区定理
接回第12轮的好块估计。在**既定均值一单胞模型、有统一有限深度上界**的
前提下，给出不再要求 H、Omega 或 Q*delta 条件的混合模型候选结论：

```text
s_n -> 2/3, delta_n -> 0  =>  liminf E_(3/4,n) >= 44/27.
```

因此该受限模型中，与短预算 19/12 的差距仍为 5/108。显式有限误差见
[proof.md](proof.md) (20)-(21)，误差随缺陷趋零。A<=log(2) 时还给出完全
有理比较支持的保守容差：L=2^24、delta<=10^-24 时总误差小于 13/500。
这是标量不等式中的分块尺度，不是实际模拟了 2^24 阶矩阵。

## 实际检查与文件

[check_hole_stability.py](check_hole_stability.py) 的最终完整运行通过：
125 个洞区模型（含5个边界）、120个混合模型、120个抽象投影模型，
750次洞区短尺度检查、1,080次混合模型/尺度/分块检查、153,272项整数
系数恒等式及8项有理比较。12次独立公式的连续积分检查也通过。
完整计数、残差和容差边界在 [validation.json](validation.json)。

高深度案例的未归一化行恒等式最大残差约 2.04e-10；这些浮点计算不是
区间证明。保守混合下界在小型随机样本上是空泛的；非空泛的有限结论依赖
正文解析估计和有理证书，不能将随机样本包装成普遍证明。

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_hole_stability.py --samples 120 --output /tmp/rh15-validation.json
python check_hole_stability.py --check-package
```

环境为 Python 3.13.5、NumPy 2.3.5、mpmath 1.3.0。
[claims.json](claims.json) 给出8项逐条审查范围；
[source-scope.md](source-scope.md) 记录来源和历史恢复；计算记录、交接及
[checkpoint.json](checkpoint.json) 保留实际执行与8份文件哈希。

## 未完成部分

这是受限模型问题的候选推进，**不是黎曼猜想证明，也不是实际零点比例改进**。
真实 zeta 零点的单胞表示、multiplicity 降阶、深度尾部、权重与局部化误差、
以及两个匹配归一化的矩预算均未建立。下一拟议任务 A-RH-SOURCE-0016
专门审查这一来源接口。洞区估计本身不依赖深度上界，不代表混合分块边界
也能无视深度增长。独立 verifier 尚未执行；完整仓库本地测试和上游 Lean
构建未执行，远端 CI 结果单独记入 PR，不预写为通过。
