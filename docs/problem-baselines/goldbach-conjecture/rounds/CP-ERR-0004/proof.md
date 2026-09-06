# G6：双素数原生下界与单变量数值证书

**CP-ERR-0004；solver proof candidate；未独立验证。**
本文重建 Li–Liu `arXiv:2606.05224v2` 的一个局部输入，不证明其整篇定理或二元哥德巴赫猜想。
原文定位：[S1] Lemma 2.2、Lemma 2.5、(1.3)、(5.2)–(5.3)、§5.2、(5.28)–(5.30)、(5.51)。
来源版本、实际阅读范围与未获取的 PDF 字节哈希见 `source-lock.json`。
此前 CP-ERR-0003 只提供任务交接；下列推导不把未审查的旧候选当成定理。

## 1. 对象、截断及源端假设

本笔记的 `a,b` 是筛指数，不是原文 Proposition (1+a) 的 a。设
\[
a=4/53,\quad b=4/33,\quad z=N^a,\quad Y=(1-\epsilon_0)N,
\quad 0<\epsilon_0\le1/2,
\]
其中 N 为偶数，N≥16 且 z≥2。固定
\[
\mathscr A=\{N-p:p<Y,\ p\text{ 为素数}\},\quad
\mathscr A_m=\{n\in\mathscr A:m\mid n\}.
\]
令 \(P_N(z)=\prod_{p<z,p\nmid N}p\)，S 为没有 P_N(z) 素因子的计数。
本轮对象始终是
\[
G_6=\sum_{z\le p_1\le p_2\le N^b\atop(p_1p_2,N)=1}
 S(\mathscr A_{p_1p_2};\mathscr P(N),z).\tag{1}
\]
两端素数区间闭合、原始 p<Y 严格截断，不能把 Y 换为 N 再声称原集合的下界。

采用 \(\operatorname{Li}(x)=\int_2^xdt/\log t\)。写
\[
\mathcal S_N=C(N)N/\log^2N,\quad
V_N(z)=\prod_{p<z,p\nmid N}\left(1-\frac1{p-1}\right),
\quad \psi(s)=f(s)/(2e^{\gamma_E}).
\]
C(N) 正好是 [S1](1.3) 的乘积。因其额外因子≥1，且
\(\prod_{n=2}^{M}(1-n^{-2})=(M+1)/(2M)\)，素数 p−1 对应全整数乘积的子集，故 C(N)≥1/2。
没有使用孪生素数常数的小数近似。

以下源端输入被**明确作为假设**采用；本轮的算术检查不证明这些来源假设。

**U-LS。** 对上述维数一筛数据存在固定 K>1 及 C_s=C_s(K)≥1。
C_s 与 eta、epsilon0、N、p1、p2 无关。对 0<eta<1/8、L=exp(8 eta^-3)、合法水平 Q_m，
存在至多 floor(L) 组系数，绝对值≤1、支撑 d<Q_m、d|P_N(z)，满足
\[
S(\mathscr A_m;\mathscr P(N),z)
\ge2e^{\gamma_E}\frac{\operatorname{Li}(Y)}{\varphi(m)}V_N(z)
 [\psi(s_m)-e_*]
+\sum_l\sum_{d\mid P_N(z)}\lambda_{m,l}^-(d)r_m(d).\tag{2}
\]
这里 e_* 在第2节给出，是 [S1](2.13) 除以 2e^gamma 后的一个保守上界。
原文 (2.13) 使用隐含常数；本轮**没有**完成原始线性筛文献中这一常数的量词审查。
`uniform_Cs=assumption_not_discharged` 是尚待审查的前提，不是已得到 uniformity 的证据。

**U-BV。** 对每个固定 A0>2 存在固定 B0,C_BV 和起点，使
\[
\sum_{d<D}\max_{2\le y\le N}\max_{(c,d)=1}
\left|\pi_{<}(y;d,c)-\frac{\operatorname{Li}(y)}{\varphi(d)}\right|
\le C_{BV}\frac{N}{\log^{A0}N},\quad D=N^{1/2}/\log^{B0}N.\tag{3}
\]
这是所需的经典最大端点素数计数形式，参见 [S1](1.11)、(5.10)。从 psi/theta 或 pi 主项形式转来时须增加对数节省并做分部求和，不可原样搬用常数。
严格端点可对非严格计数取 y 的左极限，Li 连续；无需给每个模数另加一个端点 1。
这里导入 (3)，没有重证经典 BV，也没有使用 L35 或更高分布水平。

**U-PNT。** 使用通常的素数倒数 Mertens 估计、Mertens 乘积估计及 Li 渐近式。
第4节定义精确缺陷 r_N、q_N，并说明其在偶数 N 上统一趋零的约化。
不设定未经给出的数值常数或有效数值起点。

## 2. 合法水平与不会隐藏的核漂移

只在严格支路 p1<p2 上应用 (2)。令 m=p1p2、u=log(p1)/log N、v=log(p2)/log N，并设
\[
Q_m=D/m,\quad h=B0\frac{\log\log N}{\log N},\quad
s_m=\frac{1/2-u-v-h}{a}.
\]
不含漂移时，整个三角域满足
\[
901/264\le s_0\le37/8.
\]
几何合法条件 s_m≥2 的余量为 373/3498；本轮采取更强但简便的
\[
0\le h\le109/3498,\qquad 3\le s_m\le37/8,\quad
\log Q_m\ge3a\log N.\tag{4}
\]
因此没有需要截除的非法边界条带，但仍必须支付 h 引起的核变化。
采用统一
\[
e_*=C_s\left[\eta+\eta^{-8}e^K(3a\log N)^{-1/3}\right].\tag{5}
\]
本轮选用 fixed/log 模式，不借用 CP3 固定水平模式的“零漂移”好处。

从 [S1] Lemma 2.2 换序得
\[
\psi(s)=\frac{\log(s-1)+T(s-4)}s,\qquad
T(w)=\int_0^w\frac{\log(1+x)}{2+x}\log\frac{3+w}{3+x}\,dx\ (w\ge0),\tag{6}
\]
而 s≤4 时把 T 项定义为0。对 0≤w≤5/8，log(1+x)≤x 及
log((3+w)/(3+x))≤(w−x)/3 给出
\[
0\le T\le w^3/36,\quad 0\le T'\le w^2/12,
\quad |T''|\le w/6+w^2/36.
\]
令 F0=log(s−1)+T，则在 [3,37/8] 上 0≤F0≤3、|F0'|≤1、|F0''|≤1。
T、T'、T'' 在 w=0 都为零，故拼接为 C2。直接微分 F0/s 得
\[
0\le\psi\le1,\quad |\psi'|\le2/3<1,\quad
|\psi''|\le7/9<1.\tag{7}
\]
后文仅用更松的三个常数1。

## 3. 两种“对角项”不能混为一谈；BV 不再带未知重数

(1) 中 p1=p2 的真实计数非负。因此先删去它，可得合法下界，**不需要支付真实计数的减项**。
这样 m 平方自由，且对 d|P_N(z)，(m,d)=1，恒等式为
\[
r_m(d)=\pi_{<}(Y;md,N)-\frac{\operatorname{Li}(Y)}{\varphi(md)}.\tag{8}
\]
映射 (p1,p2,d)↦p1p2d 在 p1<p2、p1,p2≥z、d 的所有素因子<z 时单射：
两个大素因子及其顺序唯一，剩余部分唯一。
于是所有 m 的所有误差之和，绝对值最多是 (3) 的 L 倍。归一化后
\[
R_{BV}/\mathcal S_N\le2LC_{BV}\log^{2-A0}N.\tag{9}
\]
各 m 的 lambda 可以不同；单射、绝对值≤1 及至多 L 组足以控制，不要求不同 m 的 lambda 相同。

若保留 p1=p2，则 p1^2d 不是平方自由，不能用带 mu^2 的求和把该误差直接删掉。
经典全模数 BV 或许可以另行覆盖，但那是不同论证。本轮不据此指控原文定理错误。

另一方面，把**严格双素数主项**转为连续积分时，必须扣除乘积测度的离散对角。
真实计数的“免费删除”不意味着下面 (12) 的对角修正可以不计。

## 4. 截断、归一化及双素数测度的明确误差

令 theta=1−Li(Y)/Li(N)。对 N≥16，Li(N)≥(N−2)/log N≥7N/(8log N)，
而 Li(N)−Li(Y)≤epsilon0 N/log(N/2)≤4epsilon0 N/(3log N)，故
\[
0\le\theta\le(32/21)\epsilon_0.\tag{10}
\]
定义精确的正归一化因子及误差
\[
R_N=\frac{2e^{\gamma_E}\operatorname{Li}(N)V_N(z)}{53\mathcal S_N},
\qquad q_N=|R_N-1|.
\]
R_N 是 [Li(N)log N/N] 与 [e^gamma log z V_N(z)/(2C(N))] 的乘积。
对 z>2 的有限乘积恒等式给出
\[
\frac{V_N(z)}{2C(N)\prod_{p<z}(1-1/p)}
=\prod_{p\ge z,p>2}\left(1-\frac1{(p-1)^2}\right)^{-1}
 \prod_{p\ge z,p\mid N}\frac{p-2}{p-1}.
\]
尾积误差为 O(1/z)，大素因子 p|N 的个数≤log N/log z=1/a，其修正为 O_a(1/z)。
因此通常的 Mertens 乘积及 Li 估计给 q_N=O_a(1/log N+1/z)，一致于偶数 N。
维数一筛所需的乘积上界 K 也可先对不删去 N 的所有奇素数取定，再由删除素因子只减小上界得到 N-uniformity；不由此推断 C_s 对 eta 的统一性。

在 [a,b] 上定义包含两个端点的测度
\[
\mu_N=\sum_{z\le p\le N^b}\frac1p\delta_{\log p/\log N},\quad
\lambda(dt)=dt/t,\quad \ell=\log(b/a),
\quad r_N=\sup_{a\le t\le b}|\mu_N([a,t])-\log(t/a)|.
\]
素数倒数 Mertens 估计给 r_N=O_a(1/log N+1/z)；下端点为素数时的原子已计入定义，不能再用无原子的起点公式。
有 ell<1/2，因为 exp(1/2)>1+1/2+1/8=13/8>53/33。
写 M=ell+r_N，故 mu_N([a,b])≤M。

对绝对值≤1、Lipschitz 常数≤1/a 的连续 g，含端点的 Stieltjes 分部积分给
\[
\left|\int g\,d(\mu_N-\lambda)\right|
\le r_N\left(1+\frac{b-a}{a}\right)=\frac ba r_N.\tag{11}
\]
令 K0(u,v)=psi((1/2−u−v)/a)。依次在两个变量上应用 (11)，得到完整正方形测度误差
≤(b/a)r_N(2ell+r_N)。记
\[
I=\int_a^b\frac{du}{u}\int_u^b\psi((1/2-u-v)/a)\frac{dv}{v},
\qquad g_6=53I.
\]
删去 p|N 的坏素数测度，总质量≤1/(az)。完整乘积测度的损失≤2M/(az)；
转为严格无序对后损失≤M/(az)。离散对角总质量≤sum 1/p^2≤M/z，须另减 M/(2z)。
因此对于好素数的严格和，及实际 h 核，
\[
\sum_{p_1<p_2\atop(p_1p_2,N)=1}\frac{\psi(s_m)}{p_1p_2}\ge I-\Delta_N,\tag{12}
\]
\[
\Delta_N=\frac{b}{2a}r_N(2\ell+r_N)+\frac{M}{az}+\frac{M}{2z}
 +\frac{hM^2}{2a}.\tag{13}
\]
最后一项来自 (7) 的 Lipschitz 漂移与严格对质量≤M²/2。
(13) 是不重复计费的四项：PNT、去公因子、离散对角、水平漂移。

因为 psi(s_m)≥0，正主项中 1/phi(p1p2)≥1/(p1p2) 是有利方向，**不用** CP2 上界中的倒数修正。
但误差项必须用相反方向的上界
\[
\sum_{p_1<p_2}\frac1{\varphi(p_1p_2)}
\le\frac{M^2}{2(1-1/z)^2}.\tag{14}
\]
不能在 psi−e_* 可能为负时对整个括号一起替换分母。

## 5. 原生有符号契约与局部存在性结论

假设 q_N≤1、r_N≤1/2，于是 M≤1。正主项与负罚项分开处理。
因实际正主项非负，由 (12) 可得
\[
R_N(1-\theta)\sum\frac{\psi(s_m)}{\varphi(p_1p_2)}
\ge I-\Delta_N-(q_N+\theta)I.
\]
即便 I−Delta_N<0 也成立：先用非负主项乘 (1−q_N)(1−theta)，然后展开且保留 Delta_N 的正确符号。
由 (14)、z≥2、R_N≤2，罚项最多为 212e_*。
第7节数值证书还给 g6<2（**不是** G6 计数的上界）。合并得到
\[
\boxed{\frac{G_6}{\mathcal S_N}\ge g_6-
\left[\frac{64}{21}\epsilon_0+2q_N+\frac{2809}{44}r_N+
\frac{2915}{4z}+\frac{2809}{8}h+212e_*+
2LC_{BV}\log^{2-A0}N\right].}\tag{15}
\]
这里用 2ell+r_N≤3/2 将 (13) 线性化。所有系数在程序中使用 Fraction 运算检查。
G6 在 [S1](5.2)/(5.51) 中的系数为 **+1**，因此这些亏损在十二项组合中仍带负号；最后才除以4。

在 U-LS 的统一 C_s 已固定的**条件下**，对任意 delta>0，可取
\[
\eta=\epsilon_0=\min\{1/16,\ \delta/[4(64/21+212C_s)]\}.
\]
固定损失≤delta/4。然后固定 A0>2、B0、C_BV，最后增大 N，使剩余五个衰减机制
(q_N,r_N,z^-1,h，以及含筛尾项和 BV 的合计) 小于 3delta/4，并满足所有源端起点及 (4)。
故最终 G6/S_N≥1.6335733−delta。特别是 delta=3×10^-6 时，局部目标 1.63357 有正余量。
这只是条件性的起点存在结论：未给出数值 C_s、有效数值 N0，未验证其余十一项或组合引理。
若 C_s=C_s(eta)，此选择失效；eta*C_s(eta) 不必趋零。

## 6. 将固定系数化为单变量积分

令 t=u+v，固定 t 时 u 从 l(t)=max(a,t−b) 到 t/2。因此
\[
W(t)=\int_{l(t)}^{t/2}\frac{du}{u(t-u)}
=\begin{cases}
 t^{-1}\log((t-a)/a),&2a\le t\le a+b,\\
 t^{-1}\log(b/(t-b)),&a+b\le t\le2b.
\end{cases}
\]
变量变换的 Jacobian 为1，而不是2；无序三角形的二分之一不能丢失。
\[
g_6=53\int_{2a}^{2b}W(t)\psi((1/2-t)/a)\,dt.\tag{16}
\]
在 t=21/106 时 s=4，T 项开始/结束。实际分段端点为
8/53、344/1749、21/106、8/33。两个内部端点不同，不能合并。

为避免嵌套多维求积，对 |x|<1 展开
\[
\frac{\log(1+x)}{2+x}=\sum_{n\ge1}(-1)^{n+1}c_nx^n,
\quad c_n=\sum_{k=1}^n\frac1{k2^{n-k+1}}<1.
\]
由 T'(w)=(3+w)^-1 integral_0^w log(1+x)/(2+x) dx，逐项积分得
\[
T(w)=\sum_{k\ge3}(-1)^{k-1}A_kw^k,\quad
A_k=\frac1k\sum_{n=1}^{k-2}\frac{c_n}{(n+1)3^{k-n-1}},
\quad 0<A_k<\frac1{4k}.\tag{17}
\]
绝对收敛支持乘法与积分。A3=1/36，A4=1/48。截到 K=48 时，对 0≤w≤5/8，
\[
|T(w)-P_K(w)|\le\varepsilon_T
=\frac{(5/8)^{K+1}}{4(K+1)(1-5/8)}.
\tag{18}
\]
不依赖未证明的“交错项单调”猜测。
因为 integral W=ell²/2<1/2 且 s≥3，(16) 的总 Taylor 误差≤53 epsilon_T/6。

## 7. 有向计算、截断失败对照及证据等级

每个光滑段上，写 W=L(t)/t，其中 0≤L≤1、|L'|≤1/a、|L''|≤1/a²、t≥2a。
于是 W≤1/(2a)、|W'|≤3/(4a²)、|W''|≤5/(4a³)。由 (7)，真实被积函数
H(t)=53W(t)psi((1/2−t)/a) 满足
\[
|H''|\le\frac{53\cdot13}{4a^3}=\frac{102576253}{256}=:M_2.\tag{19}
\]
每段 n=4096 个中点，真实积分的求积误差合计
\[
E_Q=\sum_{[c,d]}\frac{M_2(d-c)^3}{24n^2}
=\frac{168374375}{926089438298112}<1.819\times10^{-7}.\tag{20}
\]
仅含 log 项的被积函数同样满足这个上界。

实际执行：mpmath.iv 1.3.0，50 位有向区间运算，12288 个中点，48阶有理系数 Horner 求值。
所有二进制区间端点精确转 Fraction，再向外舍入至18位小数；最终同时加上 (18)、(20)，不是把 mp.quad 的误差估计冒充证书。

```text
g6 in [1.633573342946618456, 1.633573706594987299]
log-only in [1.633080252089732671, 1.633080615714169010]
safe lower coefficient = 1.6335733
printed comparator = 1.63357
conditional coefficient gain = 0.0000033
```

**必要的失败对照：** 只保留 log(s−1)/s 时，连该比较积分的上端点都达不到 1.63357。
不能丢掉正 T 修正后声称保住原系数；这不是完整 g6 目标失败，更不是原论文或哥德巴赫的反例。
初步 25 位 mp.quad 仅用于设计，正式结论仅依赖上述有向计算和解析误差。

486 个有限符号测试、122 个模数单射实例、46 个有理系数界、端点序列化测试以及负面控制，
是回归检查而非普遍命题的替代证明。独立审查仍需重导 (2) 的源端量词及 (6)–(20) 全部推导。

## 8. 合并边界与下一步

本轮增加的是“原生误差契约 + 可复算固定系数”候选。0.0000033 没有写入权威全局账本。
旧显示小数的 0.00172 总差值与保留 4×0.0004 后的 0.00012 预算仍不同。
新 floor 的敏感性增益只有在局部源输入、其余条目与统一 N0 全部协调后才能使用。
本档案进入 docs 的 PR 仅保存研究记录，不改变 Project、registry、catalog 或任何独立验证状态。

下一 solver 小任务：G8 原生上界，明确其两个提取素数/变化筛界的余数聚合与系数2；
先做模数重数分析，再决定是否能直接使用经典 BV，不能机械复制本轮固定筛界的单射。
另一个隔离角色应审查 U-LS 的 C_s 量词；没有启动该 verifier，也不代写其结论。

[S1] Jiamin Li, Jianya Liu, *Theorem (1+1.9) on the Goldbach Conjecture*,
`arXiv:2606.05224v2`, https://arxiv.org/html/2606.05224v2 ;
PDF https://arxiv.org/pdf/2606.05224v2 。引用其定义/公式不等于接纳其整篇声称。
