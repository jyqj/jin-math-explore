# 186 输入审查：本轮可闭合与不可闭合部分

协调 Issue #38；冻结源 commit `61340d0b74163003b32756bb16e91d9209a5e330`。本轮是 solver 自查，不是上下文隔离的 independent verifier。

## 审查结论表

| 项 | 本轮结果 | 精确边界 |
|---|---|---|
| K3 来源 → 可读规格 | 归一化推导成立的 proof candidate | 以 Katz 定理为外部输入；不是重新证明 Deligne，也未消去 Lean axiom |
| K2 相关和来源 → 可读规格 | 变量代换与系数推导成立的 proof candidate | 以 FKM Proposition 2 为外部输入；A=B 无需额外排除 |
| 规格 → 实际 Lean 证明模块 | INCONCLUSIVE | 10 MB `PrimeGaps186.lean` 未能读出；不能只信 Challenge 的复制声明 |
| 数值 axiom 的结构 | 104 + 45 + 3 个标量不等式已列清 | 是结构提取，不是验证这些积分 |
| 表格 → 带符号预算 | exact_check PASS | 97 行、原预算、改进预算和余量都有精确计算 |
| 原 Python → 每条积分不等式 | 未执行 | 未取得定制 FLINT 构建，也未运行原程序 |
| 完整 186 定理 | INCONCLUSIVE / 未独立验证 | 来源、数值、分析一致性及形式化链仍有缺口 |

## S1：rank-three Kloosterman 输入

可读的 `Challenge.lean` 定义

\[
K_3(c;p)=p^{-1}\sum_{u,v,w\in\mathbb F_p\atop uvw=c}e_p(u+v+w),
\qquad c\ne0.
\]

因为乘积非零，所有参与变量都非零，故与 Katz 的非零变量求和域相同。Katz *Gauss Sums, Kloosterman Sums, and Monodromy Groups*, Theorem 4.1.1(1)–(2)，书页48–49，PDF第29页（两页合扫），取

\[
q=p,\quad n=3,\quad b_1=b_2=b_3=1,\quad\chi_1=\chi_2=\chi_3=1
\]

及标准非平凡加性特征。秩为3，权为2；迹是原始求和（符号为 $(-1)^{3-1}=1$）。三个 Frobenius 特征值的复绝对值为 $p$，所以原始和的绝对值至多 $3p$，除以 $p$ 得 $|K_3(c;p)|\le3$。

这里不要求 $p\nmid3$：定理关于 $b_i$ 的去除 p 幂约定在 $b_i=1$ 时没有变化。不能自行删除小素数。作为定义层边界，$p=2,c=1$ 时唯一非零三元组是 $(1,1,1)$，得到 $K_3=-1/2$；同样满足所需界。

这是外部定理到数学规格的推导，不是完整 Lean elaboration 或内核检查。

来源：https://web.math.princeton.edu/~nmk/Katz-GKM.pdf ，本轮已看 PDF 第29页图像。

## S2：二阶相关和输入

令

\[
K(c;p)=\sum_{u\ne0}e_p(u+c/u),\qquad
\operatorname{Kl}_2(c)=p^{-1/2}\sum_{x\ne0}e_p(cx+x^{-1}).
\]

映射 $u=x^{-1}$ 是 $\mathbb F_p^\times$ 的双射，所以

\[
K(c;p)=\sqrt p\operatorname{Kl}_2(c).
\]

FKM 的 Proposition 2 对每个素数和任意 $A,B\ne0$ 给出

\[
\left|\sum_{t\in\mathbb F_p^\times\setminus\{-1\}}
\operatorname{Kl}_2(A/t)\operatorname{Kl}_2(B/(t+1))\right|\le8\sqrt p.
\]

因此所需未归一化相关和的界是 $p\cdot8\sqrt p=8p\sqrt p$。两个极点与规格完全对应。源定理没有 $A\ne B$ 的条件，不应为对角情形另造障碍。$p=2$ 时求和域为空，界显然成立。这里的乘积没有需要偷偷补上的复共轭。

来源：Fouvry–Kowalski–Michel, *The Friedlander–Iwaniec character sum*, 2013-06-14, p.1, Proposition 2；本轮已看该页图像。https://people.math.ethz.ch/~kowalski/friedlander-iwaniec-sum.pdf

## S3：数值规格的真实大小

`physical_integral_bounds` 是一个合取，不是“一次积分通过”：

| 类 | 行数 | 每行积分界数 | 标量界数 |
|---|---:|---:|---:|
| outer order 2 | 17 | root + face | 34 |
| outer order 5/2 | 35 | root + face | 70 |
| inner base order 2 | 7 | mass | 7 |
| inner base order 5/2 | 10 | mass | 10 |
| inner enlarged order 2 | 11 | mass | 11 |
| inner enlarged order 5/2 | 17 | mass | 17 |
| caps | 3 | I下界、I上界、J下界 | 3 |
| 合计 | 97 个分量行 + caps | | 152 |

外层 root/face 的定义不依赖 Young 参数 $c_j$；参数只用于组合已独立给界的两个分量。因此本轮改变 $c_j$ 不会改变待假设的物理积分本身。

固定参考量是 $I_0=23685317816/10^{24}$，不是可以随意更换的实际积分 $I$。所有149个分量上界先除以此 $I_0$，再按 $10^{-18}$ 单位编码。52个旧 Young 参数按 $10^{-6}$ 编码，旧组合预算按 $10^{-12}$ 编码。三个 cap 界也按 $10^{-24}$ 编码。

可读规格使用固定 step trial、同一物理测度与同一 normalizer。该一致性是后续代码复现必须逐条匹配的目标，不因本轮列出定义就自动得到保障。

## 访问失败与保留事项

本轮 `git clone` 失败（容器 DNS 不可用）；PDF 下载失败，未得到源文件原始字节哈希。GitHub 的 `PrimeGaps186.lean` 文件读取返回空内容，raw读取也被拒绝。GitHub 树仍可给出其 blob SHA 和10,312,565字节的大小，但这些元数据不能替代正文审查。数值 companion PDF 的 web读取也失败。

实际已读的是 `Challenge.lean` 第1–470、590–770、770至结尾的相关片段，以及主论文和两份引用的一手 PDF。Challenge 的三个 `sorry` 是规格占位，不能据此认定解决模块有洞；同样不能据此认定解决模块已无洞。

下一独立审查先核对转录和上述数学推导；数值复现则需取得原始代码、定制库构建和所有输入目标。不得把“表格能相加”当成“152个积分命题均为真”。
