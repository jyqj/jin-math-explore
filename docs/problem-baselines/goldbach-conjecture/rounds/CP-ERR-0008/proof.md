# G1/G2 显式下界：实际质量换基、固定水平和可检验的参数取舍

**CP-ERR-0008；proof candidate；尚未独立验证。** 关联 #92，顺序承接 CP7；
CP3 的原有候选保持冻结。这里重建所需论证，不把任何旧候选的正确性当成前提。
本轮替代的是 G1/G2 的原生下界接口，不是整个哥德巴赫问题。

## 1. 固定对象与外部输入

设 N 为偶数，T=log N，N>=16，0<epsilon0<=1/2，并取
\[
a=4/53,\quad b=4/33,\quad z_1=N^a>2,\quad z_2=N^b,
\quad Y=(1-\epsilon_0)N.
\]
始终保留 [S1] (5.3) 的原序列
\[
\mathcal A=\{N-p:p<Y,\ p\text{ prime}\},\qquad M=|\mathcal A|,
\quad X=\operatorname{Li}(Y),\quad\operatorname{Li}(y)=\int_2^y\frac{dt}{\log t}.
\tag{1}
\]
令 P_N(z)=prod_{p<z,p∤N}p，G_i=S(A;P(N),z_i)，其中 S 按非负序列质量计数。
令 V_i=prod_{p<z_i,p∤N}(1-1/(p-1))，以及
\[
C(N)=\prod_{p>2}(1-(p-1)^{-2})\prod_{p>2,p\mid N}\frac{p-1}{p-2},
\qquad\mathcal S_N=C(N)N/T^2.
\tag{2}
\]
这是 [S1] 的归一化，最终组合给 G1、G2 的权分别为3、1，最后才除以4。
从 prod_{n=2}^m(1-n^-2)=(m+1)/(2m)，以及额外因子>=1，得到 C(N)>=1/2。

采用三个明示的源输入：

**U-BJS-v6。** [S2] Theorem 6 的常密度下界和 Table 1。
对 g(p)=1/(p-1)、有限例外素数乘积 W_N，若删去例外素数后的产品条件成立，
则当 D>=z^2 时，弱化其严格号后有
\[
S(\mathcal A;P(N),z)\ge [f(s)-\epsilon C_2(\epsilon)H(s)]MV_N(z)
-\sum_{d\mid P_N(z),\ d<W_ND}|r_M(d)|,
\tag{3}
\]
其中 s=log D/log z，r_M(d)=|A_d|-M/phi(d)，而 s>=3 时
H(s)=e^2 h_BJS(s)=3e^{2-s}/s。对0<epsilon<=1/200，采用其表及单调性给出的
C2(epsilon)<=154。零质量情形直接处理也满足上述弱不等式。
该定理及表中常数是导入输入，本轮没有重建其数值证明。

**U-BV-classical。** [S3] p.3 的最大端点 psi 形式，连同 p.1 的分部求和，给出：
对固定 A0>=4，可取 B=A0+8、C_BV 及起点，使
\[
R=N^{1/2}/T^B>1,\qquad
\sum_{d\le R}\max_{(v,d)=1}\sup_{2\le y\le N}
\left|\pi_{<}(y;d,v)-\frac{\operatorname{Li}(y)}{\varphi(d)}\right|
\le E:=C_{BV}N/T^{A_0}.
\tag{4}
\]
常数与 epsilon、epsilon0、P0 无关。具体换算见第2节。
这是真正的经典绝对 BV 输入，不使用 CP6 的加权分布候选，也不使用更高分布水平。

**U-Mertens。** 通常的 Li 渐近、Mertens 乘积估计及其固定指数下误差。
第3、5节解释所需的 N 一致性。源输入的接受与本轮推导的正确性是不同审查层。
原 Iwaniec C_s 的审计没有因此完成；本接口根本不需要 C_s 或 L_eta。

## 2. 原 AP 余数、严格端点与质量换基

对平方自由 d|P_N(z_i)，(d,N)=1，故有精确恒等式
\[
|\mathcal A_d|=\pi_{<}(Y;d,N),\quad
r(d)=|\mathcal A_d|-X/\varphi(d),\quad
\Delta=M-X=r(1),\quad r_M(d)=r(d)-\Delta/\varphi(d).
\tag{5}
\]
两行共享同一 M、X、Delta，不把它们假想为独立误差，也不免费删除 d=1。

为说明(4)的来源，给 [S3] 的 psi 定理使用节省指数 A0+2。
在 Q=R 时，其第二项为 O(N T^{6-B})=O(N T^{-A0-2})。
对每个余类，去掉素数幂的粗成本至多 O(sqrt(N) T^2)，在 d<=R 上求和为
O(N T^{2-B})。分部求和算子在 [2,N] 上的误差范数至多常数 2/log2；
从 y/log y 转为本笔记的积分自2起的 Li 时，还有 2/[phi(d)log2] 的端点常数。
第4节的倒数 totient 引理将其总和控制为 O(log R)，可并入 C_BV N/T^A0。
因此 B=A0+8 是一个充分选择，而不是最优或有效常数声明。
严格 p<Y 由非严格素数计数的左极限获得，Li 连续；不能再对每个 d 凭空增加1。

下界不能像上界那样把 Y 改成 N。保留原截断并定义
\[
\theta=1-\operatorname{Li}(Y)/\operatorname{Li}(N).
\]
由 Li(N)>=(N-2)/log N、log(N/2)>=(3/4)log N，得到
\[
0\le\theta\le\frac{32}{21}\epsilon_0.\tag{6}
\]
此常数统一于整个 epsilon0 区间，没有隐含 C(epsilon0)。

## 3. 固定小素数集合与完整水平成本

存在先于 N 和小参数固定的 K>0，使全体奇素数的产品满足
\[
\prod_{u\le p<v,p>2}(1-1/(p-1))^{-1}
\le\frac{\log v}{\log u}(1+K/\log u),\qquad 2\le u<v.
\tag{7}
\]
证明的输入只是 Mertens 乘积：将每项写为
(1-1/p)(1-1/(p-1)^2)，用第二个乘积的可收敛尾项，有限小 u 通过增大 K 覆盖。
删去 p|N 的素数只减小左端，因此同一 K 对全部偶数 N 可用。

先选0<epsilon<=1/200，再固定
\[
w=\max(3,\exp(2K/\epsilon)),\quad P_0=\prod_{p<w}p,
\quad W_N=\prod_{p<w,p\nmid N}p\mid P_0.
\tag{8}
\]
对 u>=w，(7) 的相对误差<=epsilon/2；对1<u<w，将乘积从 w 起算，
再用 log u<log w。z<=w 时剩余乘积为空。因此 BJS 所需的、对所有1<u<z成立的
严格产品条件被满足。没有从最终目标中丢弃这些小素数：它们进入 W_ND 的余数范围。

本轮固定
\[
\rho=10^{-6},\quad D_1=N^{\kappa_1},\quad\kappa_1=24/53,
\quad D_2=N^{\kappa_2},\quad\kappa_2=b(33/8-\rho)=4124999/8250000.
\tag{9}
\]
于是 s1=6、s2=33/8-rho 恒定，且 D_i>=z_i^2。必须满足
\[
h_*:=\frac{B\log T+\log P_0}{T}\le\sigma:=1/8250000,
\tag{10}
\]
因为 1/2-kappa1=5/106，1/2-kappa2=sigma。
(10) 保证 W_ND_i<=P0 D_i<=R，故(3)的每个余数模数均在(4)内。
固定水平不是 D_i/P0；P0 的成本在起点里支付，不能同时保留除以 P0 后的水平和零核漂移。

P0 有限但可能极大。一个充分的纯几何起点是
\[
T\ge\max\{1,(2B/\sigma)^2,2\log P_0/\sigma\}.
\tag{11}
\]
这是由 log T<=sqrt(T) 将两项各压到 sigma/2 得到，不是包含源起点的有效数值 N0。
前轮 rho=10^-8 的对应指数余量小100倍。在相同 B、P0 下，(11) 的平方项缩小10000倍、
线性项缩小100倍；实际总 N0 未计算，不能声称实际可检验范围扩大这些倍数。

## 4. 符号安全的下界换基

由 n/phi(n)=sum_{d|n}mu(d)^2/phi(d) 和调和和界，
\[
\sum_{n<R}\frac1{\varphi(n)}
\le(1+\log R)\prod_p(1+1/[p(p-1)])<3(1+\log R).
\tag{12}
\]
这里 Euler 乘积<=exp(sum_{n>=2}1/[n(n-1)])=e<3。
因此在第3节的实际筛支撑上，由(4)-(5)
\[
\sum|r_M(d)|\le(4+3\log R)E.\tag{13}
\]

写 Gamma_i=f(s_i)-154epsilon H(s_i)。将 BJS 的 C2 上界154代入只会降低主项，合法。
第6节的系数证书给 k1<15、k2<10，其中 k_i=c_i f(s_i)/(2e^gamma)，c1=53、c2=33。
0<gamma<1、e<3 故 f(s_i)<6 k_i/c_i<2；且154epsilon H(s_i)<=154/200<1。
于是 |Gamma_i|<=2。对任何 Gamma_i 符号都有
\[
\Gamma_i V_i M\ge\Gamma_i V_i X-2|\Delta|\ge\Gamma_i V_i X-2E,
\tag{14}
\]
其中0<V_i<=1。结合(3)、(13)得到原生的非渐近条件式
\[
G_i\ge[f(s_i)-154\epsilon H(s_i)]V_i X-(6+3\log R)E.
\tag{15}
\]
这里未先假设主因子为正。有限反例 M=3、X=2、Gamma=-1、V=1、E=1 表明：
将 M>=X-E 直接乘以负 Gamma 会给错误的 -3>=-1；正确的(14)给 -3>=-4。
更精确的 |Gamma|E 在此为1，但本轮统一使用2E。

没有 L_eta 乘子；额外一个对数来自(13)，不是可以忽略的表示方式差异。
在 T>=1、log R<=T/2 下，(6+3log R)E/S_N<=15 C_BV T^{3-A0}。
两行相加时，3G1+G2 要按权重3、1付费，不能只算两个副本。

## 5. 两行及其加权组合的显式契约

定义精确的归一化缺陷
\[
R_i=\frac{2e^\gamma\operatorname{Li}(N)V_i}{c_i\mathcal S_N},
\qquad q_a=|R_1-1|,\quad q_b=|R_2-1|.
\tag{16}
\]
它们与 epsilon0、epsilon 无关。对 z>2 有恒等式
\[
\frac{V_N(z)}{2C(N)\prod_{p<z}(1-1/p)}
=\prod_{p\ge z,p>2}(1-(p-1)^{-2})^{-1}
 \prod_{p\ge z,p\mid N}\frac{p-2}{p-1}.
\tag{17}
\]
大素因子个数<=log N/log z=1/a_i，两个尾项的相对误差为 O_{a_i}(z^-1)。
所以 U-Mertens 给 q_{a_i}=O_{a_i}(T^-1+N^{-a_i})，统一于偶数 N。
以下限定 q_a,q_b<=1，这只增加一个最终起点条件。

(15) 的正主项满足
k_i R_i(1-theta)>=k_i-k_i(q_i+theta)。负惩罚项单独上界，不能把 k_i减误差的整个括号当正数。
从 e>8/3 得 e^2>7、e^4>50，故
\[
H(6)<1/100,\qquad H(s_2)\le H(4)<3/28.
\]
结合 R_i<=2、e^gamma>1，有归一化 epsilon 成本<=154c_i H(s_i)epsilon。
由此得到
\[
\frac{G_1}{\mathcal S_N}\ge k_1-
[\tfrac{160}{7}\epsilon_0+15q_a+\tfrac{4081}{50}\epsilon+15C_{BV}T^{3-A_0}],
\tag{18}
\]
\[
\frac{G_2}{\mathcal S_N}\ge k_2-
[\tfrac{320}{21}\epsilon_0+10q_b+\tfrac{1089}{2}\epsilon+15C_{BV}T^{3-A_0}],
\tag{19}
\]
\[
\boxed{\frac{3G_1+G_2}{\mathcal S_N}\ge3k_1+k_2-
[\tfrac{1760}{21}\epsilon_0+45q_a+10q_b+
 \tfrac{19734}{25}\epsilon+60C_{BV}T^{3-A_0}].}
\tag{20}
\]
这些都是在原始有限 N 对象上的条件不等式，不是仅把极限小数相加。
原始 C_s、L_eta 和 CP6 的加权分布输入均未出现。损失是固定 P0 的水平成本与一个换基对数。

## 6. 五个固定核的真实有向证书及失败边界

从 BJS 的延迟微分定义，或 [S1] Lemma 2.2，在4<=s<=6积分换序得到
\[
\psi(s)=\frac{f(s)}{2e^\gamma}
=\frac1s\left[\log(s-1)+\int_2^{s-2}\frac{\log(u-1)}u
 \log\frac{s-1}{u+1}\,du\right].
\tag{21}
\]
令 j(u)=log(u-1)/u，L_s(u)=log((s-1)/(u+1))。
在2<=u<=s-2<=4，|j|<=1、|j'|<=1、|j''|<=2；可由
j'=1/[u(u-1)]-j/u、j''=-(2u-1)/[u^2(u-1)^2]-j'/u+j/u^2直接验证。
又0<=L_s<1、|L_s'|<=1/3、|L_s''|<=1/9，故
\[
|(jL_s)''|\le25/9<3.
\]
每个值取4096个中点，最终乘 c/s 后的解析求积误差不超过
\[
E_{c,s}=\frac cs\frac{3(s-4)^3}{24\cdot4096^2}.
\tag{22}
\]
所有中点、对数及算术使用50位 mpmath.iv；二进制端点精确转 Fraction，
加上(22)后向外舍入至18位小数。不使用 mp.quad 的启发式误差，也不把浮点中心值当上下界。
实际重新计算了五个对象，共20480个中点：

| 对象 | 有向区间 |
|---|---|
| 53 psi(6) | [14.877114447209748899, 14.877115500225139932] |
| 33 psi(33/8) | [9.115870450628733126, 9.115870450861563771] |
| 33 psi(33/8-10^-8) | [9.115870447035543370, 9.115870447268373959] |
| 33 psi(33/8-10^-6) | [9.115870091309334559, 9.115870091542159672] |
| 33 psi(33/8-2*10^-6) | [9.115869731989081516, 9.115869732221901098] |

k1是主动取s1=6后的比较系数，不是对原文使用f(53/8)的g1精确重算。
本轮选择保守 floor k1>=14.877114、k2>=9.11587009，仍分别高于原显示值14.87710、9.11587。
代价是 G2 floor 比 CP3 的9.1158704稍低；不是同时改善数值系数与起点。
过大的 rho=2*10^-6 连固定核的上端点都低于9.11587，故不能用该系数保住这个逐项比较目标。
这不提供实际 G2 计数的上界，不反驳原目标，更不是其他筛水平路线的不可行证明。

### 比较模式不可混搭

另可取 D1=N^(24/53)、D2=R/P0。若 h_*<=1/66，则 s2=33/8-h_*/b 属于[4,33/8]。
令U为(21)的中括号，则U'=(1+integral_2^(s-2)j(u)du)/(s-1)属于[0,1]。
又U<=2+(s-4)<=s，所以0<=psi<=1，psi'=(U'-psi)/s给 |psi'|<=1/4。
因此用极限系数 k20=33psi(33/8) 时，另付 (1089/16)h_* 的核亏损。
在此小区间，令 J 为(21)的积分，有 J<=(s-4)^3/36<=1/18432；
s/(s-1)-log(s-1)-J>=33/25-6/5-1/18432>0，故psi非减、33psi(s)<=k20<10。
这里 log(25/8)<6/5 可由 exp(6/5)>sum_{j=0}^4(6/5)^j/j!>25/8 精确检查。
于是(18)-(20)仍成立，但 G2 用 k20 并加上述漂移。该模式较宽松的起点不能与固定模式的零漂移合用。

## 7. 参数选择、来源边界与下一步

给任意delta>0，令 Cfix=320/21+1089/2，同时选择
\[
\epsilon=\epsilon_0=\min\{1/400,\delta/(4C_{fix})\}.
\tag{23}
\]
两行固定损失各<=delta/4。固定 w、P0，随后固定 A0>=4、B=A0+8及源常数，最后增大 N，
使(10)、q_i<=1、所有源起点成立，并让每行剩余的 q_i 和 T^{3-A0} 损失<=3delta/4。
因此原两行最终各满足 G_i/S_N>=k_i-delta。
取delta=4*10^-8，即仍有 G1/S_N>=14.87711396、G2/S_N>=9.11587005，均保住原显示目标。
这个共同 N 存在的推论不声称数值 N0，也没有控制其余十项或组合引理的误差。

有限 AP 与换基回归使用原始截断素数序列，但为测试任意换基的代数恒等式，X 取 M 加有理偏移；
这不是把该偏移当作真实 Li 误差，也不在小 N 上声称全部渐近假设成立。
同一上下文所做的符号/数值自检不是独立验证。BJS 定理及其表未重证；
BV 的非有效源常数保留，P0 未枚举。原 Iwaniec 源审计未关闭，只是这里不再依赖它。
新数值 floor 和敏感性收益未插入全局账本；旧候选无修改。

下一本地任务：给 G4/G5 提取单素数上界做同类替换，先证明逐 p 的实际质量换基如何汇总到
同一 BV 模数预算，再付 P0 的水平成本。不得将该绝对余数接口自动移植到仅有可分解权平均的 G9/G11/G12。

## 来源

[S1] J. Li, J. Liu, *Theorem (1+1.9) on the Goldbach Conjecture*,
https://arxiv.org/html/2606.05224v2 ，Lemma2.2、(5.1)-(5.16)。只使用列明定义、核公式及比较目标。

[S2] M. Bordignon, D. R. Johnston, V. Starichkova, *An explicit version of Chen's theorem and the linear sieve*,
https://arxiv.org/html/2207.09452v6 ，Theorem6、Table1、(4)-(11)及紧接其后的常数单调性说明。

[S3] R. C. Vaughan, *The Bombieri-Vinogradov Theorem*,
https://personal.science.psu.edu/rcv4/Bombieri.pdf ，pp.1,3。

[S4] mpmath 1.3.0 interval-context documentation,
https://mpmath.org/doc/current/contexts.html 。只用所固定版本的基本算术和log；该实现的信任基础仍需审查。
