# 第20轮：非对角检验、宏观高度与可分离性边界

Attempt：`A-RH-OFFDIAG-0020`。工作 Issue：[#128](https://github.com/jyqj/jin-math-explore/issues/128)。
日期：2026-09-08。状态：**proof_candidate；未经独立验证**。
本轮接续第19轮冻结档案，不修改旧候选，不替代 #124 的隔离审查。

## 本轮增量

构造并求值一类真正非对角的正半定矩阵：对固定带宽 Toeplitz 矩阵，左右
乘以非恒定剖面的平方根。完整复数展开明确保留了零点对的高度相位，不能
直接把它冒充只依赖差值的配对关联公式。

由已有固定检验的配对关联定理和带误差项的经典零点计数公式，候选推导
给出宏观高度加权矩。关键步骤是统一控制分割高度处的**带符号交叉误差**，
随后对不必单调的前缀能量作 Stieltjes 积分。由此得到这类非对角检验的
来源主项，而无需删除拥挤零点、截断增长深度或假定新的扭曲关联定理。

简单零点部分则显式留下同一个高度分布测度 `nu`，没有把它偷换成总比例。
进一步证明：在固定带宽、可分离矩阵、`9/10<=theta<=1` 和
`sup r<=3/2` 的范围内，已知 Montgomery–Taylor 比例与均匀简单高度测度
组成一个**同时满足全部当前标量必要不等式**的见证。精确系数是
`281/72<4`。它覆盖经典最优剖面，不产生更高比例。

这是特定不等式族的边界，不是实际极值零点构造，更不是对所有非对角
矩阵的否定。联合误差约束、不可分离矩阵和随高度增长的带宽仍未被排除。

## 冻结内容

[proof.md](proof.md) 包含有限恒等式、来源桥梁、极限次序、标量一致性
证明和反例。[claims.json](claims.json) 分开八项结论及各自不能推出的事项。
[来源与恢复范围](source-scope.md) 记录精确父级 commit/blob 和外部输入。

[offdiag_tools.py](offdiag_tools.py) 与 [check_offdiag.py](check_offdiag.py)
实际测试了124个有限模型、521组非对角配对／一次迹公式、480项一致性
不等式、12个另一表达式的连续积分，以及14,805项整数／有理检查。
最大非对角配对公式残差约 `4.44e-15`；连续积分残差约 `3.55e-15`。
完整结果在 [validation.json](validation.json)，微小负浮点余量原样保留。
测试不涉及真实零点枚举，不验证来源渐近式或未知 PC 余项。

## 复现

需要 Python、NumPy、mpmath；实际版本为3.13.5、2.3.5、1.3.0。
在本目录运行，避免覆盖冻结的跨平台浮点输出：

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_offdiag.py --samples 120 --output /tmp/rh20-validation.json
python check_offdiag.py --check-package
```

[计算记录](computation-record.json)、[交接](computation-handoff.json) 和
[九文件哈希清单](checkpoint.json) 分开候选证明、精确有限检查与数值证据。
本地没有运行完整仓库套件、bundled inventory、Lean 或独立 verifier；远端
CI 的实际观察单独写入 PR，不预写到冻结证据。

下一项 `A-RH-JOINT-0021` 聚焦联合算子缺陷：保留多个检验共享的误差结构，
寻找可由来源公式求值的耦合约束，或构造真正联合的一致性见证。
**本轮没有改进已知零点比例，也未证明黎曼猜想。**
