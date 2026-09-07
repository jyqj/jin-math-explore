# CP-ERR-0009：G4/G5 显式上筛、逐素数质量误差汇总与一维证书

**solver proof candidate；未独立验证。** 本轮承接 CP8，不修改任何冻结前置。
本页重导必要接口，不以旧 PR 或旧检查器通过作为数学前提。
来源：[S1] Li–Liu v2 的 G4/G5 定义和 F 核；[S2] BJS v6 Theorem 6/Table 1；
[S3] Vaughan 的最大端点 BV。定理/表的导入、以下推导和计算证据是三个不同层级。

## 1. 目标与输入

固定充分大偶数 N，令
\[
a=4/53,\quad b_4=1/3,\quad b_5=3/11,\quad T=\log N,\quad z=N^a,
\quad \mathcal S_N=C(N)N/T^2.
\]
C(N) 是 [S1] 式 (1.3) 的奇异乘积；P_N(z) 是小于 z 且不整除 N 的素数之积。
对 0<epsilon0<1 保留原始集合 A_e={N-r:r<(1-epsilon0)N，r 为素数}，
A_e,p 表示其中被 p 整除的元素，**不是商集**。本轮目标为
\[
G_b=\sum_{z\le p\le N^b,(p,N)=1}S(A_{e,p};P(N),z),\qquad b=b_4,b_5. \tag{1}
\]
提取素数的两端均闭合，小筛素数使用严格端点。G4、G5 在最终下界组合中均带系数 -1。

采用以下精确外部输入。

**U-BJS。** 使用 [S2] Theorem 6 的常密度上界；对 0<epsilon<=1/200，
Table 1 和文中单调性允许取 C1<=154。主项采用序列真实质量 M，
余数是实际密度误差的绝对值之和，模数上限带有限异常素数乘积 W。
我们没有独立重建该定理或该表。其全模数绝对余数接口不等同于 well-factorable 权接口。

**U-BV。** 对固定 A0>=4，可取 B=A0+8、C_BV 和起点，使
\[
R=N^{1/2}/T^B,\quad
\sum_{d<R}\max_{(c,d)=1}\sup_{2\le y\le N}
 |\pi_{<}(y;d,c)-\operatorname{Li}(y)/\varphi(d)|
 \le E:=C_{BV}N/T^{A0}. \tag{2}
\]
Li(x)=integral_2^x dt/log t。[S3] p3 的 psi 形式给出
O_A(N/T^A+sqrt(N)R log^6(NR))。从 psi 去素数幂的逐模数代价
O(sqrt(N)T^2)，再用总变差有界的 Abel 算子转为 pi；额外 O(1) 端点每模数支付一次。
代入 B=A0+8 后这些项分别至多 O(N/T^(A0+2))、O(N/T^(A0+6)) 和 O(R)，
都可并入 (2)。严格计数通过左极限得到，Li 连续。
此处导入经典定理及这一标准转移，不依赖 CP6 的加权 BV 候选，也不宣称有效数值起点。

**U-M。** 使用通常的 PNT、素数倒数及乘积 Mertens 估计。固定指数 a、b 后的统一性
在第5节重导；小参数不会进入这些固定指数的常数。

## 2. 只为上界扩大；小素数例外必须降低水平

令 A*={N-r:r<N，r 为素数}。原集合包含于 A*，所有计数非负，所以只需上界 G_b(A*)。
这里去掉的是整个序列的截断，不混用截断质量与未截断余数。此步骤不能用于下界。

写 A*_p 为提取子序列，并定义
\[
M_p=|A^*_p|,\quad X_p=\operatorname{Li}(N)/(p-1),\quad \Delta_p=M_p-X_p.
\]
对 d|P_N(z)，p>=z 保证 (p,d)=1，故
\[
r_p(d)=\pi_{<}(N;pd,N)-\operatorname{Li}(N)/\varphi(pd),\quad
|A^*_{p,d}|=X_p/\varphi(d)+r_p(d),\quad r_p(1)=\Delta_p. \tag{3}
\]
N 为偶数且 >=4，端点 N 本身不是素数；但仍保留严格计数定义。
取小筛密度 g(ell)=1/(ell-1)，ell 为不整除 N 的奇素数，V_N(z)=prod(1-g(ell))。

由 U-M，可先固定与 N、p、epsilon 无关的 K_dim>0，使全部 2<=u<v 满足
\[
\prod_{u\le\ell<v,\ell\nmid N}(1-g(\ell))^{-1}
 \le\frac{\log v}{\log u}(1+K_{dim}/\log u). \tag{4}
\]
先对所有奇素数用 (1-1/(ell-1))=(1-1/ell)(1-1/(ell-1)^2) 建立上界，
有限小 u 区域增大常数；删除整除 N 的素数只减小左侧。
取
\[
w=\max(3,\exp(2K_{dim}/\epsilon)),\quad
P_0=\prod_{\ell<w}\ell,\quad W_N=\prod_{\ell<w,\ell\nmid N}\ell. \tag{5}
\]
P0 在 epsilon 固定后有限且与 N 无关；W_N|P0。除去这些例外素数后，
(4) 对 u>=w 的相对误差<=epsilon/2；对 1<u<w 从 w 起估计并用 log u<log w。
最终取 z>w，即得到 [S2] 式 (4) 对所有 1<u<z 的严格 (1+epsilon) 产品条件。
小素数并未从最终筛目标删除：它们出现在定理的余数上限 W_N D_p 中。

本轮选择
\[
D_p=R/(P_0p),\quad h_*=(B\log T+\log P_0)/T,\quad
s_p=\frac{1/2-\log p/T-h_*}{a}. \tag{6}
\]
若 0<=h_*<=5/318，则对两个完整区间都有
\[
D_p\ge z^2,\quad 2\le s_p\le45/8,\quad
pW_ND_p\le R. \tag{7}
\]
两区间的平方水平余量恰为5/318、89/1166。BJS 上界只要求 D_p>=z；
这里刻意采用更强条件，以保持统一的紧核区间，不声称几何起点最优。
绝不能把 D_p 设为 R/p，却忽略定理实际允许 d<W_N R/p。

## 3. 核心汇总引理：不乘提取素数个数

> **命题 A（逐素数质量换基汇总，候选）。** 对任一 b，若 (2)、(7) 成立，令
> \(r_{M,p}(d)=r_p(d)-\Delta_p/\varphi(d)\)。则
> \[
> \sum_p|\Delta_p|\le E,\qquad
> \sum_p\sum_{d\mid P_N(z),\ d<W_ND_p}|r_{M,p}(d)|
> \le(4+3\log R)E. \tag{8}
> \]

证明：pd 恰含唯一一个 >=z 的素因子 p，且其重数为1；d 的素因子均<z。
因此 (p,d)->pd 单射，包含 d=1。所有 pd<R，所以由 (2)
\(\sum_p\sum_d|r_p(d)|\le E\)。质量误差对应于互不相同的模数 p，
同样给出 sum|Delta_p|<=E。这不是先给每个 p 一个完整 BV 预算，再对 p 求和。

对任意 U>=1，
\[
\sum_{n<U}\frac1{\varphi(n)}\le3(1+\log U). \tag{9}
\]
因为 n/phi(n)=sum_{d|n}mu^2(d)/phi(d)，卷积与调和数上界给
(1+log U)sum_d mu^2(d)/(d phi(d))；该和的 Euler 乘积
<=exp(sum_p1/[p(p-1)])<=e<3。再对 r_M 使用三角不等式及 (9)，得到
E+3(1+log R)sum_p|Delta_p|，即 (8)。证毕。

对两个重叠 p 区间合并，映射最多有重数2，而不是1。等价地，使用
omega(p)=1_{p<=N^(1/3)}+1_{p<=N^(3/11)}<=2。本轮两个合同各支付一次 (8)。
另一方面，不能用 |sum_p Delta_p| 代替 sum_p |Delta_p|：两个误差 +1、-1
就使前者为0、后者为2。原生不同 p 的主系数也不同，净质量抵消没有所需控制力。
这是误差模型反例，不是素数分布或哥德巴赫反例。

BJS 需要真实质量 M_p，而不是任意解析 X_p；(3) 与上述 r_M 正是精确换基。
BJS 的上界主系数 Xi_p=F(s_p)+154epsilon e^2 h_BJS(s_p) 非负。
第4节给 F(s)<=2e^gamma，且 e^2 h_BJS(s)<=1、0<gamma<1，故 Xi_p<7。
由 M_p<=X_p+|Delta_p|、V<=1，主项换算额外成本<=7E。
因此得到无隐藏族乘子的原生合同
\[
\boxed{G_b\le V_N(z)\sum_p X_p[F(s_p)+154\epsilon e^2h_{BJS}(s_p)]
 +(11+3\log R)E.} \tag{10}
\]
空子序列可直接使用弱不等式处理。此处没有未知 Cs、L_eta，也没有加权 BV 输入。

## 4. 紧区间核界：漂移与正修正都保留

令 Phi(s)=F(s)/(2e^gamma)。[S1] Lemma2.2 或 [S2] 的延迟方程在本区间给出
\[
\Phi(s)=(1+J(s)+K_2(s))/s,\quad j(t)=\log(t-1)/t,
\]
其中 J(s)=0(s<=3)，否则 J(s)=integral_2^(s-1) j(t)dt；K2(s)=0(s<=5)，否则
\[
K_2(s)=\int_2^{s-3}j(t)\int_{t+2}^{s-1}\frac1v\log\frac{v-1}{t+1}\,dv\,dt. \tag{11}
\]
0<=j<=1，故 J<=s-3、J'<=1。利用 log((v-1)/(t+1))<=(v-t-2)/(t+1)
和 v(t+1)>=12 得
K2<=(s-5)^3/72，K2'<=(s-5)^2/24。
于是在2<=s<=45/8上，0<=Phi<=1；分段微分
Phi'=(J'+K2'-Phi)/s，并结合[2,3]的1/s公式，给出 |Phi'|<=1。
拼接点连续，因此整个区间为1-Lipschitz。无需假设 Phi 的全局单调性。
(10) 里不能把 s_p 替换为极限 s_0 而不付 h_* 成本。

## 5. 从素数和到固定积分，以及全部有符号成本

定义
\[
q_N=\left|\frac{2e^\gamma\operatorname{Li}(N)V_N(z)}{53\mathcal S_N}-1\right|,
\quad
r_N=\sup_{a\le t\le1/3}\left|\sum_{z\le p\le N^t}\frac1p-\log(t/a)\right|,
\]
\[
I_b=\int_a^b\Phi((1/2-u)/a)\frac{du}{u},\quad g_b=53I_b,\quad\ell_b=\log(b/a). \tag{12}
\]
CDF 包括下端点素数原子。对固定 a，U-M 给 r_N=O_a(T^-1+z^-1)、q_N=O_a(T^-1+z^-1)，
统一于偶数 N。后一结论中，prime-pair乘积尾项为O(1/z)，N的>=z素因子数<=1/a，
每个遗漏修正为1+O(1/z)。因此大素因子不会破坏 N 一致性。
C(N)>=1/2 可直接由 prod_{n=2}^m(1-n^-2)=(m+1)/(2m) 及 prime-minus-one 子集证明。

对 g(u)=Phi((1/2-u)/a)，sup|g|<=1、TV(g)<=(b-a)/a；含左端点的 Stieltjes 分部积分给
prime-sum误差<=(b/a)r_N。又
sum_{p>=z}(1/(p-1)-1/p)<=1/(ceil(z)-1)<=2/z。因此
\[
\sum_{z\le p\le N^b}\frac{\Phi(s_p)}{p-1}
 \le I_b+(h_*/a)(\ell_b+r_N)+(b/a)r_N+2/z. \tag{13}
\]
正主项中可去掉(p,N)=1的约束；上界的倒数修正不可以免费删除。
(13) 已支付一次该修正，后面不得重复记入旧 CP1 账目。

由于154/(2e^gamma)<=77，(10)给出完整未展开合同
\[
\frac{G_b}{\mathcal S_N}\le53(1+q_N)\left[I_b+\frac{h_*}{a}(\ell_b+r_N)
 +\frac ba r_N+\frac2z+77\epsilon(\ell_b+r_N+2/z)\right]
 +(22+6\log R)C_{BV}T^{2-A0}. \tag{14}
\]
若 T>=1、q_N<=1、r_N<=1/2，则 logR<=T/2；由 exp(3/2)>53/12（有限 Taylor 部分和即可证明），
两项 ell_b<3/2。故 ell_b+r_N<=2，且z>=2时ell_b+r_N+2/z<=3。
第7节证书给g4<24、g5<20。直接展开非负成本得
\[
\boxed{\frac{G_4}{\mathcal S_N}\le g_4+24q_N+2809h_*+\frac{2809}{6}r_N
 +212/z+24486\epsilon+25C_{BV}T^{3-A0},} \tag{15}
\]
\[
\boxed{\frac{G_5}{\mathcal S_N}\le g_5+20q_N+2809h_*+\frac{8427}{22}r_N
 +212/z+24486\epsilon+25C_{BV}T^{3-A0}.} \tag{16}
\]
相加后六项成本为
\[
\mathcal E_{45}=44q_N+5618h_*+\frac{28090}{33}r_N+424/z
 +48972\epsilon+50C_{BV}T^{3-A0}. \tag{17}
\]
在最终下界中，两项系数均为 -1，故 (17) 以减号出现，最后才除4。
这里BJS显式误差的粗常数可进一步优化，但没有把其数值当作零。

## 6. 共同二重修正降为一维积分

令 A0*=53/8（不要与 BV 指数 A0 混淆）、s*=45/8、sigma_b=(1/2-b)/a，
\[
H(s)=8\log\frac{s}{A0^*-s}.
\]
换元 u=a(A0*-s)，再用非负积分换序，得到
\[
g_b=H(s^*)-H(\sigma_b)+\mathcal J_b+\mathcal K,
\]
\[
\mathcal J_b=\int_2^{37/8}j(t)[H(s^*)-H(\max(\sigma_b,t+1))]dt. \tag{18}
\]
G4的sigma=53/24<3；G5的sigma=265/88>3，需要t=177/88处分段。
两sigma都小于5，所以K修正相同；两个J项并不相同。

在 (11) 对 s 求导，移动边界项为零。写 s=5+w，直接得
\[
K_2'(5+w)=\frac{\mathcal T(w)}{4+w},\quad
\mathcal T(w)=\int_0^w\frac{\log(1+x)}{2+x}\log\frac{3+w}{3+x}\,dx.
\]
于是对 0<=w<=5/8，再次换序得到
\[
\boxed{\mathcal K=\int_0^{5/8}\frac{\mathcal T(w)}{4+w}
 [H(s^*)-H(5+w)]\,dw.} \tag{19}
\]
这是本轮的新数值约化：旧 CP2 的64x64二维区间覆盖不再需要，但正修正本身没有删去。

把 log(1+x)/(2+x) 展开，令
\[
c_n=\sum_{j=1}^n\frac1{j2^{n-j+1}}<1,\quad
A_k=\frac1k\sum_{n=1}^{k-2}\frac{c_n}{(n+1)3^{k-n-1}},
\]
则绝对收敛的级数乘法和两次积分给
\[
\mathcal T(w)=\sum_{k\ge3}(-1)^{k-1}A_kw^k,\quad
0<A_k<1/(4k),\quad A_3=1/36,\ A_4=1/48. \tag{20}
\]
系数界来自(n+1)>=2和sum_{j>=1}3^-j=1/2，不要求交错项单调。
截到K=48时，统一误差
\[
e_T=\frac{(5/8)^{49}}{4\cdot49(1-5/8)}. \tag{21}
\]
因(19)中W=H(s*)-H(5+w)<=16、1/(4+w)<=1/4，积分层的多项式误差<=(5/2)e_T。

## 7. 严格求积界与真实运行结果

(18)的每个光滑段有 |j|<=1、|j'|<=1、|j''|<=2；
0<=W<16、|W'|<=32/3、|W''|<=80/9，故 |(jW)''|<=560/9<64。
W<16可用exp(2)>7>435/64；导数界由s>=3、A0*-s>=1得到。
每段8192中点，分别加上64 sum(length^3)/(24*8192^2)。

对(19)，log(1+x)<=x和log((3+w)/(3+x))<=(w-x)/3给
\[
0\le\mathcal T\le w^3/36<1/100,\quad
0\le\mathcal T'\le w^2/12<1/25,\quad
|\mathcal T''|\le w/6+w^2/36<1/8.
\]
取V=1/(4+w)，则|TV|<=1/400、|(TV)'|<=17/1600、|(TV)''|<=117/3200。
于是(19)真实被积函数的二阶导数绝对值小于
117/200+17/75+1/45<1。因此使用4096中点、余项(5/8)^3/(24*4096^2)，
再另加(21)的积分误差。我们对真实函数证明求积界，而不是对近似多项式的误差作循环假设。

全部中点和系数从Fraction进入50位mpmath.iv；二进制区间端点精确转有理数，再向外舍入18位。
实际运行共28,672个一维中点，二维网格数为0。输出：

```text
K in [0.000197235748259595, 0.000197236967692548]
g4 in [23.605686437359609383, 23.605687876075436255]
g5 in [19.519080862878462493, 19.519082283006322277]
safe uppers: 23.605688, 19.519083
```

这是固定积分包络，**不是**实际G4/G5计数的双侧区间。
相对旧CP2固定积分上界23.60573、19.51913，分别收紧0.000042、0.000047；合计0.000089。
相对原显示值23.60636、19.51976，合计余量0.001349。这些只是局部主系数敏感度，未写入全局账本。
去掉K的两个比较积分，其上端点都严格低于完整积分的下端点；不能把正修正当作可省略的上界误差。

## 8. 量词、完成范围和下一任务

给任意delta>0，先固定K_dim，再选
\[
\epsilon=\min(1/400,\delta/(4\cdot48972)).
\]
固定成本<=delta/4。随后固定w、P0、A0>=4、B=A0+8、C_BV，最后选择N，
使q_N、r_N、z^-1、h_*及T^(3-A0)之和在(17)中小于3delta/4，并满足全部源端和几何起点。
因此在声明输入下，最终G4+G5<=S_N(g4+g5+delta)。各项误差非负，
取delta=10^-5还能分别保住旧CP2的两个显示上界，因新余量各自大于10^-5。
这不提供有效数值N0；巨大P0虽固定但其起点代价没有被删去。

`check_upper.py` 的有限AP模型、合计预算、重数、精确系数与负面测试只核对有限身份；
其中X_p采用合成有理偏移，R=N，不能把这些测试当作真实Li误差或小N的BV/BJS成立证据。
BJS定理/表未重建，经典输入未重证，候选未独立审查，完整十二项与组合定理仍未闭合。
原Iwaniec的Cs源端审计也没有被改成PASS；只是本接口已不需要它。

下一solver任务：G6的显式下筛替换。先处理双素数提取质量、真实/离散对角和预筛水平，
再接回其数值证书；因子可分解权专属的G9/G11/G12分支不能无新输入改用绝对余数。

## 参考与版本边界

[S1] J. Li, J. Liu, *Theorem (1+1.9) on the Goldbach Conjecture*, arXiv:2606.05224v2,
https://arxiv.org/html/2606.05224v2 ，Lemma2.2、§5.2、(5.17)-(5.27)。
[S2] M. Bordignon, D. R. Johnston, V. Starichkova, *An explicit version of Chen's theorem and the linear sieve*,
arXiv:2207.09452v6, https://arxiv.org/html/2207.09452v6 ，Theorem6、Table1。
[S3] R. C. Vaughan, *The Bombieri–Vinogradov Theorem*,
https://personal.science.psu.edu/rcv4/Bombieri.pdf ，印刷p3。
确切阅读方式和缺少的PDF字节哈希见source-lock.json；没有声称文献首创或全篇独立验证。
