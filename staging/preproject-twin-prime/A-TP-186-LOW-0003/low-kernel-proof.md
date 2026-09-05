# G0:R00：真实 root 积分的控制关系与数值上界候选

身份 `A-TP-186-LOW-0003`，solver proof candidate，2026-09-05。
本文件不是 independent-verifier receipt，也不是 Lean 内核证明。

## 0. 要认证的具体对象

固定 `openai/PrimeGaps186@61340d0b74163003b32756bb16e91d9209a5e330`。
采用 `Challenge.lean` 中 `physicalSourceOuterRoot 0 0` 的定义，记其值为 K_root。
它已经除以 `trialPhysicalNormalizer`，不能再漏除或重复除该因子。
设

\[
 I_{ref}=23685317816/10^{24}.
\]

固定输入的第一项是

\[
 K_{root}/I_{ref}\le 11/10^{18}.
\]

本候选用一个独立的正更新方程包络和精确整数卷积，得到

\[
 \boxed{K_{root}/I_{ref}\le10.42897229\cdot10^{-18}<11\cdot10^{-18}}. \tag{R}
\]

这里的 I_ref 仅是正有理数常数；本推导**没有假设**尚待验证的 `I_ref <= trialIH`。
另一个 `physicalSourceOuterFace 0 0` 的目标 10 本轮没有认证。

## 1. 精确参数与冻结定义

网格宽度、标记区间和指数参数为

\[
 h=2742997/258046918656,\quad
 \ell=29068686916144971709156469/1172752030899844388101008936,
 \quad u=3\ell/2,\quad\theta=189.
\]

置 L=2331、H=3498、C=49152，令 \(\ell_0=Lh\le\ell\)、\(u_0=Hh\ge u\)、\(z=Ch\)。
分组阈值为

\[
 T=7200342320019/6890569875110.
\]

由冻结源几何，第一行的径向格点和 r 只可能在 94919..95638。
确切裁剪值为

\[
 q=288763833465798194485431089923/286076767019837125756522770000,
\]

故 `floor(q/h)-40+1=94919`。分组上端为

\[
 U_G=16430591763736936545249922448197799591/
       16161921199408696007503616565983946000,
\]

且 `floor(U_G/h)=95638`。两段实际 fragment cap 分别是 49152h、46580h，均不超过 z。
本推导放宽成统一 z；这是上界，不是假定两段 cap 相同。

77 个有理系数、11 个角向签名和全部输入在 `inputs.json` 中；文件 SHA-256 被程序固定。
上游读取范围和未取得的完整源码字节见 `source-lock.json`。

令 \(t_i=\text{mass}(X_i)\)、\(j_i=\lfloor t_i/h\rfloor\)、\(\widehat t_i=(j_i+1/2)h\)、\(r=\sum j_i\)。
则 \(s=\sum\widehat t_i=(r+20)h\)，且

\[
 rh\le\sum t_i<(r+40)h=s+20h.
\]

令 \(g(t)=(21/200)/(1+t/100)+(179/200)/(1+(907/5)t)\)。
试验函数是 mask 乘以 \(\prod_i g(\widehat t_i)Q(\widehat t)\)，其中

\[
 Q(t)=\sum_\sigma p_\sigma\bigl(\sum_i t_i-9/10\bigr)
        \prod_{e\in\sigma}\sum_i t_i^e.
\]

固定归一化是 \(Z^{40}\)，\(Z=h\sum_{j=0}^{98263}g((j+1/2)h)^2>0\)。
这里空角向签名的乘积是 1，重复指数按重数保留。

## 2. Poisson 测度：无额外 cap 比例

记 \(\nu_z=e^\gamma z\,\mathcal L(\Pi_z)\)，\(\Pi_z\) 的强度是 \(dv/v\) 于 (0,z]。
采用主论文 (3.24)–(3.25) 及 Last–Penrose 的 Laplace/Mecke 恒等式：
限制没有大于 z 的 fragment 后，\(\nu_\zeta\) 变为 \(\nu_z\)，没有额外 z/ζ 因子。
这也直接来自大 fragment 的空集概率 z/ζ 与前面的 e^γζ 相乘。

与 Lean 的 weighted finite-measure 表示的对应如下：每个 fragment v 贡献 \(v\delta_v\)；
其总质量是 fragment 总和，除以 v 的 count measure 恢复点计数。
所有 dyadic bands 上的总质量期望为 z，因此质量有限几乎处处；`finiteFragments` 的零回退分支是零测集。
以独立 band 构造的过程与上述 Poisson 过程同分布。

所有后续积分都非负，或是有界支撑上有限的多项式组合。计数区间下端严格正，
故使用 Tonelli/Mecke 时不会引入不明的 `infinity - infinity`。

## 3. 连续 low 核的恒等式

定义小片段总质量 \(S_{\ell_0}(X)=\sum_{v\in X,v\le\ell_0}v\)。
令 \(M(dt)\) 是 \(e^{-\theta S_{\ell_0}}d\nu_z\) 经总质量映射的像测度。
分解小片段与大于 ℓ0 的片段，得到

\[
 M=D_{\ell_0,\theta}*\sum_{n\ge0}K_{\ell_0,z}^{*n}/n!,\quad
 D_{\ell_0,\theta}(dt)=e^{-\theta t}\rho(t/\ell_0)dt,
 \quad K_{a,b}(dv)=1_{(a,b]}dv/v. \tag{1}
\]

此处 ρ 是 Dickman 函数，不是密度参数。由 Mecke，带一个计数标记的像测度是

\[
 D(dt):=\int N_{(\ell_0,u_0]}(X)e^{-\theta S_{\ell_0}(X)}
                    1_{\{\text{mass}(X)\in dt\}}d\nu_z(X)
       =M*K_{\ell_0,u_0}(dt). \tag{2}
\]

标记的片段大于 ℓ0，因此它不额外贡献一个 `exp(-theta*v)`；漏掉这一点会改变核。
对 40 个坐标，总计数给出 40 个乘积测度之和：每项恰有一个 D，其余为 M。

原覆盖函数中的计数区间是 (ℓ,u]。放宽到 (ℓ0,u0] 增大计数；
小片段区间缩小使负指数权增大；u 换为 u0 也增大指数。因此这是逐点的非负上界。

## 4. 独立于 FLINT 的正更新方程

(1) 的密度记为 m。由 Laplace 变换求导，或对总质量使用一次 Mecke，

\[
 t m(t)=\int_0^t w(t-v)m(v)\,dv,\qquad
 w(a)=\begin{cases}e^{-\theta a}&0<a\le\ell_0,\\
                   1&\ell_0<a\le z,\\0&a>z.\end{cases} \tag{3}
\]

对 \(0<t<\ell_0\)，有 \(m(t)=e^{-\theta t}\)。此外 \(0\le m(t)\le1\) 几乎处处：
倾斜权不超过 1，而 νz 的总质量密度是 \(\rho(t/z)\le1\)。

设 a_j 是 m 在格子 \([jh,(j+1)h)\) 上本质上确界的一个上界。
在 j<L 时可取 \(a_j=e^{-\theta jh}\)。在 j≥L 时，从 (3) 得到合法递推

\[
 a_j=\min\left\{1,
 \frac{\sum_{k=1}^{L-1}e^{-\theta(k-1)h}a_{j-k}
       +\sum_{k=L}^{C}a_{j-k}}{j-1}\right\}, \tag{4}
\]

负下标作零。证明：若 t 在格子 j、v 在过去格子 j-k，则 t-v 落在
\([(k-1)h,(k+1)h]\)。k≤L-1 时 w 被第一项系数控制；L≤k≤C 时被 1 控制；
k>C 时仅可能有零测端点贡献。当前格子的贡献至多 h 倍当前本质上确界。
把它从 `j*a_j` 右侧移走产生 **j-1**，不能误写 j。
已知 m≤1 使取 min(1,...) 合法；它不是数值截小真实正量。

程序对 (4) 的两个窗口做 O(N) 更新。高窗口是精确整数和；低窗口的乘、减都向外取整，
同时保留下、上端点，不能只在带减法的递推中保留“上界”。所有 a_j 是固定的二进有理数。
指数通过有理 Taylor 和严格几何尾界，再以平方/倒数向外传递。

## 5. 从密度上界到真实格子质量

a_j 定义了同一个分段常数上测度 \(\widehat M\)，其格子质量是 h*a_j。
标记强度在格子 k 上被常密度 \(1/(kh)\) 控制，格子质量 \(b_k=1/k\)，L≤k<H。
两独立均匀分数部分的 carry 分别为 0、1，概率都是 1/2。因此

\[
 M_j\le h a_j,\qquad
 D_j\le \frac h2\left[(a*b)_j+(a*b)_{j-1}\right]. \tag{5}
\]

(5) 是连续测度不等式的结果，不是经验采样。左闭右开格子端点不影响这些绝对连续像测度。
所有后续计算保持这一对共同的非负上测度。

### 对原 Eulerian 实现的额外语义检查

r 个高片段加一个低片段有 r+1 个分数部分，其 carry 概率多项式为 E_{r+1}(x)；
再加一个指定标记则为 E_{r+2}(x)。它们系数非负、和为 1。
对系数非负且 A(0)=0 的 A，粗 carry 包络满足形式幂级数恒等式

\[
 \sum_{r\ge0}\frac{A(x)^r}{r!}(1+x+\cdots+x^{r+a})
 =\frac{e^{A(x)}-x^{a+1}e^{xA(x)}}{1-x},\quad a=0,1. \tag{6}
\]

减去前 33 项后的余项逐系数非负。原代码采用的这一尾项形式因而有明确的数学来源。
第一行高片段最小格子为 2331；在原 98304 格范围内 r 至多 42，指定标记还占一个正格子。
只保留到 32 而丢掉余项并不合法。本次数值计算使用 (3)–(5)，无需依赖原代码的尾项计算。

## 6. 带符号试验平方为什么仍可使用上测度

若 μ≤ν 是测度序且 f 是实函数，则 \(\int f^2d\mu\le\int f^2d\nu\)。
不要求 f 的多项式系数为正。但是必须先确定一个共同上测度，再在它上面计算完整平方。

仅给每个矩分别换成上界不具有这一性质。例如 δ_{1/2} 上，
`m0=1,m1=1/2,m2=1/4` 给 \(\int(1-t)^2=1/4\)；把 m1 单独提高到 1，代入变成 -3/4，
即使截成零也低于真实值。本程序对共同上测度的每个正矩运算保存区间，
最后按平方展开系数的符号选端点，而不把所有矩的上端点直接代入带符号和。

## 7. 降维至精确多项式卷积

为改善整数数值尺度，仅计算上使用 β=-6 和 q0=1/360；没有改变原 θ=189 或原试验。
置 \(t_j=(j+1/2)h\)，定义非负多项式系数

\[
 A_e[j]=q_0^{-1}h a_j g(t_j)^2e^{\beta t_j}t_j^e,
\quad B_e[j]=q_0^{-1}\widehat D_jg(t_j)^2e^{\beta t_j}t_j^e. \tag{7}
\]

这里只需 e≤12。对角向签名 σ 的各个有标签出现位置，枚举分配到指定标记坐标的子集 S，
再对其补集取集合划分 π。其余块分配到 39 个互不相同的坐标。因此总标记矩的生成式是

\[
 40\sum_{S\subseteq\sigma}\sum_{\pi\vdash\sigma\setminus S}
 (39)_{|\pi|}\ B_{\sum S} A_0^{39-|\pi|}
       \prod_{B\in\pi}A_{\sum B}. \tag{8}
\]

签名是多重集，但枚举先按出现位置进行，合并相同指数和后保留精确重数。
这是展开乘积和按相同坐标分组的有限恒等式。空集和为零、空乘积为一。
11 个试验签名平方后产生 53 个不同签名，(8) 合并后有 216 个不同正卷积单项。

所有乘积都是**线性**卷积，且每次只保留下标 <95639 的系数。由于指数非负，
更高下标不可能回流到所需系数，截断合法。不能不加论证地替换成循环卷积。

## 8. 最终积分上界公式

记 E_r 为在 (7) 的共同上测度上，完整 Q 平方乘以总计数的第 r 个格子系数。
原 face 权不超过 1；把 40 个 face 求和放大为因子 40。由第 1 节的总质量上界，

\[
 K_{root}\le40\left(\frac{q_0}{Z}\right)^{40}
 \sum_{r=94919}^{95638}
 e^{\theta(u_0-T+20h)+(\theta-\beta)(r+20)h}E_r. \tag{9}
\]

外面的 40 来自 face 求和；(8) 的 40 来自哪个坐标携带计数标记，两者含义不同，均需保留。
积分中的 mask 已经以非负上界放宽；并没有假定对所有配置 mask=1。

程序用 160-bit 二进固定点保存所有有限系数区间。正卷积通过 GMP 的 mpz 精确乘法作
Kronecker 编码；每槽位的编码基数严格大于 `min(lengths)*max(coeff_a)*max(coeff_b)`，
因此不会发生系数间进位串扰。乘积后除以固定点尺度，分别向下/向上舍入。
最后 Q 平方的有理系数由原 77 个系数与精确 r 值计算，按符号合并区间。

Z 的下界由各个正有理项向下取整相加得到。使用它放大 (q0/Z)^40，方向正确。
`results.json` 保存 (9) 的总和整数上端点和 Z 下端点，可仅用有理数重算最终界。
完整密度数组的逐行整数流 SHA-256 也保存；完整运行可从冻结输入重建它，没有读取旧积分报告。

## 9. 实际结果与范围

完整精确运行的最后向上取整值是 1042897229/10^8 个 `10^-18` 单位，给出 (R)。
这是**真实目标积分的上界候选**，其意义依赖本文件各个分析控制步骤正确；
有限程序通过本身不替代独立数学审查。

本轮不使用 `physical_integral_bounds` 作为前提，不执行原 FLINT 引擎，不构建原 Lean 文件。
未认证 face、另外 147 个源积分界、三个整体 cap 界、有限域输入或全部解析恢复步骤。
即使 (R) 经独立审查通过，也不会产生新的素数间隔纪录，更不会证明孪生素数猜想。

## 10. 后续明确任务

下一目标仍在同一行：`physicalSourceOuterFace 0 0 / I_ref <= 10e-18`。
该项含一个平方边缘积分，擦除坐标中的标记与保留坐标中的标记必须分别计入。
它不能简单从 root <=11 推出；需要对边缘函数的共同上测度或区间展开独立建立控制。
原第1、2轮的独立审查队列也没有在本轮被冒充完成。

## Sources

- PrimeGaps186 固定 commit 的 `Challenge.lean`：trialCore、trialPhysicalNormalizer、physicalSourceCover、physicalSourceOuterRoot 及 outerOrderTwoBounds。
- 同 commit 的 `prime_gap_186_certificate.py`：source_low_measures、_low_eulerian_envelopes、SourceJets、source_component_raw。这里读取了相关文本，不声称完整源码/证明模块审计。
- *Improved short gaps between primes*，§3.3 的 (3.24)–(3.25)，及 §4.5–4.6。
  https://cdn.openai.com/pdf/51126fac-1b68-4128-9666-c908bcc16033/short_gaps.pdf
- Last–Penrose, *Lectures on the Poisson Process*，Theorems 3.9、4.1（Laplace functional 与 Mecke），作者发布稿。
  https://stoch.math.kit.edu/img/Last/lastpenrose2017.pdf

本文件的正更新包络及特定第一行的整数证书是本轮重建；不声称相关更新方程、集合划分恒等式或 Kronecker 编码在文献中首次出现。
