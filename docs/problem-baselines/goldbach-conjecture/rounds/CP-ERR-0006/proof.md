# G8 的有界权分布桥：从大筛到实际余数

CP-ERR-0006 / Issue #81。**solver proof candidate，尚未独立验证。**
本笔记以 [S2] 的 Siegel–Walfisz 与最大双线性大筛引理为外部经典输入，
证明 G8 真正需要的特例；不假装已经取得或重审 Pan–Ding 1979 全文。
前轮 CP5 只作为对象和任务来源，不作为已经验证的数学前提。

## 1. 精确命题与来源边界

令 `log` 为自然对数，π(x;q,b) 计数 p≤x、p≡b (mod q) 的素数，
π(x) 不附加同余条件，Li(x)=∫₂ˣ dt/log t。φ、μ、ω 分别为 Euler 函数、
Möbius 函数和不同素因子个数。χ 在不与其模数互素的整数上延拓为零。

> **命题 WBV-G8（候选）。** 对每个固定实数 A≥3，存在 C_A、N_A，
> 使对每个整数 N≥N_A、每个复权序列 a_N(m) 满足
> \[
> |a_N(m)|\le1,\qquad
> \operatorname{supp}(a_N)\subset[N^{6/11},N^{2/3}],
> \]
> 并且 a_N 不随 q 改变，都有：令 Q=N^{1/2}/(log N)^{A+8}，则
> \[
> \sum_{q\le Q}\max_{(b,q)=1}\left|
> \sum_{(m,q)=1}a_N(m)
> \left[\pi(N/m;q,bm^{-1})-\frac{\operatorname{Li}(N/m)}{\varphi(q)}\right]
> \right|\le C_A\frac{N}{\log^A N}. \tag{1}
> \]
> C_A、N_A 统一于所有这些权和余类；不依赖 eta、epsilon0。

权可以依赖 N，甚至有复数符号；绝对值始终在完整 m 和之外。
这里只有固定公共双线性截断 mp≤N；不宣称任意 m-dependent 端点、q-dependent 权、
更高分布水平或完整 WEH。A>2 的一般要求可用 A'=max(3,A) 满足并缩小 Q。
N_A 的有效数值没有给出：小导子处使用的 SW 仍有非有效常数。

[S1] 的 Lemma 3.1 及 (5.37) 是待核查调用，不是 (1) 的证明。
Pan 1980 出版者摘要 [S3] 给出相关均值定理，采用 π 主项且权条件写法不同；
它不等于已取得 1979 正文。本轮改用可逐式读取的 [S2] 建立本身更窄的桥。
所有来源定位、实际可见页面及未取得的原 PDF 哈希见 source-lock.json。

## 2. 两个经典输入与三个初等准备

**SW 输入。** [S2] 引言给出特征形式的 Siegel–Walfisz：固定 D 时，在
模数 d≤log^D y 上，ψ(y,χ)−δχ y 有超越任意固定对数幂的节省；常数非有效。
由去掉高素数幂、分部求和，得到本证明采用的具体推论：固定 D,J，充分大的 N 上，
对 1<d≤log^D N 的非主本原特征及 N^{1/3}≤y≤N^{5/11}，
\[
\left|\sum_{p\le y}\chi(p)\right|\ll_{D,J}y\log^{-J}N,
\quad |\pi(y)-\operatorname{Li}(y)|\ll_J y\log^{-J}N. \tag{2}
\]
说明这一步的一致性：ψ 与 θ 的差至多 O(√y log²y)。分部积分在 √y 分开；
低段用平凡界，高段 t≥√y≥N^{1/6}，从而 d≤log^{D+1}t 对充分大的 N 成立。
在高段使用任意更强的固定对数节省，低段及素数幂误差为幂次节省。
π−Li 的 q=1 情况同理；Li 的积分起点只产生固定常数。这里未假定一个有效的数值 N_A。

**最大双线性大筛输入。** [S2] Lemma 6.1（式 (6.2)）适用于任意复系数及
两个整数区间，给出
\[
\sum_{d\le T}\frac d{\varphi(d)}\sum_{\chi\bmod d}^{*}
 \max_y\left|\sum_{m\in I,n\in J\atop mn\le y}u_m v_n\chi(mn)\right|
\le c_3\sqrt{(|I|+T^2)(|J|+T^2)}\,\|u\|_2\|v\|_2
 \log(2M_1P_1). \tag{3}
\]
M₁、P₁ 是两区间的上端点，星号表示本原特征，c₃ 是源文的绝对常数。
源文由乘法大筛 (6.1)、半整数截断、积分核及 Cauchy 推导此式。
本轮实际读取其 HTML 公式和证明；不把模数 T 当成本笔记的 T(N) 等其他对象。
(3) 保留整个双曲线截断，故无需用未控制的矩形边界带来替代 mp≤N。

**初等准备。** 对 Q≥1，
\[
\varphi(dl)\ge\varphi(d)\varphi(l),\qquad
\sum_{q\le Q}\frac1{\varphi(q)}\le3(1+\log Q). \tag{4}
\]
第一式逐素因子成立，无须假设 (d,l)=1。第二式由
n/φ(n)=∑_{r|n} μ²(r)/φ(r) 和
\[
\sum_r\frac{\mu^2(r)}{r\varphi(r)}
=\prod_p\left(1+\frac1{p(p-1)}\right)
\le\exp\left(\sum_{n\ge2}\frac1{n(n-1)}\right)=e<3
\]
推出。还将使用 ∑_{m≤N^{2/3}}1/m≤1+log N，以及 ω(q)≤log q/log2。

## 3. 精确正交性：不能遗漏的主特征修正

先把 (1) 中 Li 替换为 π，并将此误差记作 Eπ(q,b)。定义
\[
S_q(\chi)=\sum_{mp\le N\atop p\ {\rm prime}}a_N(m)\chi(mp),
\quad
D_q=\sum_{(m,q)=1}a_N(m)\sum_{p\le N/m\atop p\mid q}1.
\]
特征正交性精确给出
\[
E_\pi(q,b)=\frac1{\varphi(q)}
\sum_{\chi\ne\chi_0}\overline{\chi(b)}S_q(\chi)
-\frac{D_q}{\varphi(q)}. \tag{5}
\]
原因是主特征计数的 p 必须与 q 互素，而 π(N/m) 包含整除 q 的素数。
当 a_N 有符号时 D_q 不一定非负，必须以绝对值控制；由 (4)，其总代价为
\[
\sum_{q\le Q}\frac{|D_q|}{\varphi(q)}\ll N^{2/3}\log^2N. \tag{6}
\]

**精确失败对照。** N=254 的实际 G8 乘积集合为 {25,35}，取 q=3,b=2。
同余计数总数为 3，而 ∑π(N/m)=8，φ(3)=2，故 Eπ=−1。
非主特征项之和为零；D₃=2，所以 (5) 的 −D₃/φ(3)=−1 正好补足。
这与 CP5 的 H=0 不矛盾：H 是提取乘积 m 与筛模数不互素造成的修正，
D_q 则是输出的素数 p 整除 q 的修正。两者对象不同。
例如取示意水平 Q₀=15≤√254，Z₀=√15，q=3 是实际光滑支撑的模数，
所有 m 的素因子仍≥5>Z₀，但 p=3 并没有被这一事实排除。
这个有限身份反例不声称 N=254 已超过渐近定理的起点。

## 4. 导子下降：非本原特征仍有互素筛选

非主 χ (mod q) 由唯一导子 d>1 的本原 χ* 诱导。写 q=dl，允许 d,l 有公因子。
则
\[
\chi(n)=\chi^*(n)\mathbf1_{(n,l)=1},\quad
S_q(\chi)=\sum_{mp\le N}
 a_N(m)\mathbf1_{(m,l)=1}\mathbf1_{(p,l)=1}\chi^*(m)\chi^*(p). \tag{7}
\]
χ* 已经在 (n,d)>1 时为零；额外 l 不能删去。例：q=6,d=3,n=2，
诱导特征值为零，但本原模3特征在2处为−1。

由 (4)、三角不等式及 |χ(b)|≤1，(5) 的非主部分至多
\[
\sum_{d>1}\frac1{\varphi(d)}\sum_{l\le Q/d}\frac1{\varphi(l)}
 \sum_{\chi^*\bmod d}^{*}|S_{d,l}(\chi^*)|. \tag{8}
\]
固定 l 后，a_N(m)1_{(m,l)=1} 和 1_{p prime,(p,l)=1} 是不随 d 改变的系数，
正好可以应用 (3)。这解释了为什么允许 N-dependent 权，不等于允许任意 q-dependent 权。

## 5. 小导子：SW 的统一量词和移除的素数

置 L=log N，D₀=L^D；本节 D 是一个固定指数，不是前节 D_q。
对 1<d≤D₀，由 (2) 和从素数和中删去 p|l 的平凡代价，
\[
|S_{d,l}(\chi^*)|\ll_{D,J}N L^{1-J}+N^{2/3}L. \tag{9}
\]
m 的支撑保证 N/m∈[N^{1/3},N^{5/11}]，所以所有 SW 常数对 m 统一。
第一项先对每个 m 用 (2)，然后只用 ∑1/m≤1+L；第二项使用
至多 N^{2/3} 个 m、每个最多 ω(l) 个被删素数。
一个导子的本原特征至多 φ(d) 个。故 (4)、(8) 给小导子贡献
\[
\mathcal E_{\rm small}\ll_{D,J}
 N L^{D+2-J}+N^{2/3}L^{D+2}. \tag{10}
\]
(9) 里的移除项和 (6) 的主特征项不是同一个分解位置，二者都必须在这个上界推导中保留。
它们随后一起包含于总 C_A，不向已经使用 (1) 的 G8 契约重复收费。

## 6. 大导子：矩形支撑、双曲线与全部对数损失

对大导子使用 R<d≤2R，R=D₀·2^j；末块截在 Q。
对 m 使用半开 dyadic 区间 M≤m<2M，M 为2的幂，只保留与实际支撑相交的块。
因此
\[
N^{6/11}/2<M\le N^{2/3},\quad P=\lfloor N/M\rfloor,
\quad MP\le N,\quad P\le2N^{5/11}. \tag{11}
\]
若边界恰好相等，把第一处严格号改为≤亦不影响下述界。
在矩形中令素数系数仅支撑 p≤P，并仍保留 mp≤N。每个合法 (m,p) 恰好出现在一个块；
矩形并没有被当成全等于双曲线区域。区间长度不超过 M、P，平方范数不超过 M、P。

固定 l，应用 (3) 至 T=2R，再以 d>R 去掉 d 因子，单个 m 块得到
\[
\sum_{R<d\le2R}\frac1{\varphi(d)}\sum_{\chi^*}^{*}|S_{M,l}(\chi^*)|
\ll\frac L R\sqrt{(M+4R^2)(P+4R^2)MP}
\ll L\left(R\sqrt N+N^{5/6}+N^{8/11}+\frac N R\right). \tag{12}
\]
这里 log(2(2M−1)P)≤log(4N)；系数含 (·,l)=1 仍满足同样范数界。
第二步可直接平方根展开核查：根号除以 R 至多
MP/R+2√(MP)(√M+√P)+4R√(MP)，再使用 (11)。
没有素数密度估计、权的 Siegel–Walfisz 条件或隐藏的逐 m 余数乘数。

现在求和：(4) 控制 l≤Q/R 的权和为 O(L)；导子块满足
∑R≤2Q、∑1/R≤2/D₀、块数 O(L)；m 块数也为 O(L)。取略松但统一的界：
\[
\mathcal E_{\rm large}\ll L^4
 \left(Q\sqrt N+N^{5/6}+N^{8/11}+N/D_0\right). \tag{13}
\]
所用四个对数来自最大双线性引理、l 权和、m 块数、以及中间两项的导子块数；
前后两项本可少付一个对数，本轮没有据此优化 B。
这一步对所有 |a_N|≤1 统一，而不只是对每个固定权分别存在不同的常数。

## 7. π 主项转 Li；选择参数并完成 (1)

由 (2)，总主项替换成本不超过
\[
\sum_{q\le Q}\frac1{\varphi(q)}
 \sum_{(m,q)=1}|a_N(m)|\,|\pi(N/m)-\operatorname{Li}(N/m)|
\ll_J N L^{2-J}. \tag{14}
\]
将 (6)、(10)、(13)、(14) 合并。对给定 A≥3，选择
\[
B=D=A+8,\qquad J=2A+12,\quad Q=\sqrt N/L^B. \tag{15}
\]
最终八项上界的 (N幂,log N幂) 如下，均与实际程序账本一致：

| 来源 | N幂 | 对数幂 |
|---|---:|---:|
| 大导子 Q√N | 1 | 4−B=−A−4 |
| 大导子 N/D₀ | 1 | 4−D=−A−4 |
| 大导子 M 侧 | 5/6 | 4 |
| 大导子 p 侧 | 8/11 | 4 |
| 小导子 SW | 1 | D+2−J=−A−2 |
| 小导子 p\|l 移除 | 2/3 | D+2 |
| 主特征 p\|q 修正 | 2/3 | 2 |
| π→Li | 1 | 2−J=−2A−10 |

固定的幂次节省 N^(−δ) 吸收任何固定对数幂。取 N 足够大使 D₀≤Q、
SW 的所有起点及上述吸收同时成立，就得到 (1)。
A→(D,J)→SW 常数/起点→C_A,N_A；没有在选 eta 后再让 C_A 随 eta 改变。
B 的显式表达并不意味着 N_A 有有效数值。

## 8. 向 G8 的精确实例化与不重复收费

重新定义实际提取乘积集合（不要求读者相信旧 proof.md）：
\[
\mathcal M_N=\{m=p_1p_2:N^{3/11}\le p_1\le p_2,
 p_1p_2^2\le N,\ (m,N)=1\},\quad f_N=\mathbf1_{\mathcal M_N}.
\]
唯一素因数分解保证 f_N≤1；即使 p₁=p₂ 也只有一个无序分解。
m≥N^{6/11}；由 p₁³≤N 和 m≤√(Np₁) 得 m≤N^{2/3}。
其曲边和 N-dependent 性只改变系数内容，不改变范数界或 q 独立性。

对 (q,N)=1 取 (1) 中 b=N mod q。对 m∈M_N，有 (m,N)=1 且 m>1，
所以 m∤N，N/m 不是整数，**严格与非严格的素数计数端点完全相同**。
无需为每个模数或每个 m 添加一个虚假的端点误差。

实际上界筛 Q=√N/L^B、Z=√Q。q|P_N(Z) 的素因子<Z≤N^{1/4}，
而 m 的素因子≥N^{3/11}。故 (m,q)=1，仍有提取乘积修正 H=0；
但不能因此抹去 (5) 的主特征 D_q。对带索引序列
B+=(N−mp)_{m∈M_N,p prime,mp<N}，精确余数为
\[
r_B(q)=\sum_{m\in M_N}
 [\pi_{<}(N/m;q,Nm^{-1})-\operatorname{Li}(N/m)/\varphi(q)]. \tag{16}
\]
因此 (1) 的全模数最大余类估计覆盖 CP5 的平方自由、光滑、(q,N)=1 子集。
不必声称 [S1] 的任意端点版 Lemma 3.1 已被本笔记全部证明。

若所用上界筛提供至多 L_eta=exp(8eta^(−3)) 组权，|λ_l(q)|≤1、支撑于这些模数，
则 (1) 立即给出
\[
\left|\sum_l\sum_q\lambda_l(q)r_B(q)\right|
\le L_\eta C_A N/\log^A N. \tag{17}
\]
C(N)≥1/2（由 ∏_{n=2}^M(1−1/n²)=(M+1)/(2M) 和正的额外因子得到），
所以除以 S_N=C(N)N/log²N 后为 **2 L_eta C_A log^(2−A)N**。
G8 在最终下界组合的系数为−2，故除以4之前的有害成本为
**4 L_eta C_A log^(2−A)N**，固定 eta 后随 N 趋零。
D_q、诱导修正、SW/PNT 转换已经包含在 C_A 内，不能再计一遍。

此结论将 CP5 的 U-WBV 从未展开假设推进为一个可独立审查的源定理应用链候选。
它没有验证上界线性筛的 C_s 统一性，没有独立验证 CP5 其余交换/积分步骤，
没有把新旧主系数余量写入全局账本，更没有闭合十二项或证明哥德巴赫猜想。

## 9. 实际检验、失败边界及后续

check_wbv.py 只用整数/Fraction。它以 Möbius 反演的本原特征核
\[
K_d(x,y)=\mathbf1_{(xy,d)=1}
\sum_{e\mid d}\mu(d/e)\varphi(e)\mathbf1_{x\equiv y\pmod e}
\]
核查有限的特征正交、导子提升及大筛平方和，并对实际 G8 对象检验 (5)、
(16) 的 π 版本、严格端点、光滑互素支撑和 dyadic 覆盖。
该整数实现不以浮点特征值代替精确身份。有限大筛实例不能替代经典定理 (3)。
代码还检查八项指数账本及错误符号、缺失修正、非法权范围等负面输入。
真正的渐近常数或 N_A 没有通过扫描有限 N “计算”出来。

下一最优先任务：沿 [S1] Lemma 2.5 追到原始线性筛定理，核查
C_s(K) 是否对 eta 和当前序列族统一；不要因为 (1) 已有候选就认为这个不同缺口自动消失。
G3/G10 的非公共端点也必须分别重新实例化，不直接套用本命题。

## 来源

[S1] Li–Liu, *Theorem (1+1.9) on the Goldbach Conjecture*, arXiv:2606.05224v2,
(1.12)–(1.13), Lemmas 2.5/3.1, §5.3。
https://arxiv.org/html/2606.05224v2

[S2] Akbary–Hambrook, *A variant of the Bombieri–Vinogradov theorem with explicit constants and applications*,
arXiv:1309.2730v2，2013-12-04；引言 SW、(6.1)、Lemma 6.1/(6.2) 及证明。
https://arxiv.org/html/1309.2730v2

[S3] Pan Chengdong, *A new mean value theorem and its applications*, Chinese Annals of Mathematics
1(1) (1980),149–160，出版者摘要。只用于辨认文献接口，不作为本证明不可见的数学输入。
https://camath.fudan.edu.cn/camaen/ch/reader/view_abstract.aspx?file_no=1B114&flag=1

[S4] 山东大学作者书目中 Pan–Ding 1979 条目，Special Issue II,149–161。
https://www.prime.sdu.edu.cn/info/1011/1005.htm
