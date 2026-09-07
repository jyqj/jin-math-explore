# G7 显式下筛与连续移动边界

CP-ERR-0011；Issue #115。**solver proof candidate，未独立验证。**
本轮承接 CP10，并重新读取冻结的 #41 G7 候选。旧候选只提供问题、来源和比较基线，
下列局部推导自足；不提升旧候选，也不宣称证明二元哥德巴赫或 Li–Liu 主定理。

## 1. 原对象、源输入和端点

记 [S1] 为 Li–Liu `arXiv:2606.05224v2`，采用其 §5.2 原定义，
而不采用 (5.31) 中额外的 1/v 或 (5.32) 展开时遗漏的 gamma 上限。
两处问题已在旧记录出现，本轮不是首次发现。

设 N>=16 为偶数，T=log N，0<epsilon0<=1/2，Y=(1-epsilon0)N，并设
\[
 a=4/53,\quad b=4/33,\quad g=3/11,\quad c=1/2-2a=37/106,
 \quad z=N^a,\quad \mathcal R=[a,b]\times[b,g].
\]
g 是指数，不是 Euler 常数 gamma_E。令 A={N-p:p<Y，p为素数}，
A_m 是被 m 整除的子序列，未除以 m；P_N(z)=prod_{p<z,p∤N}p。
\[
G_7=\sum_{z\le p_1\le N^b\le p_2\le N^g,\ (p_1p_2,N)=1}
 S(A_{p_1p_2};\mathscr P(N),z),\quad S_N=C(N)N/T^2. \tag{1}
\]
C(N) 是 [S1] (1.3) 的乘积。由全整数乘积
prod_{n=2}^M(1-n^-2)=(M+1)/(2M)，取 prime-minus-one 子集及额外>=1的因子，得 C(N)>=1/2。

**端点引理。** 对整数 N，N^(4/33) 不可能是素数 p：否则 N^4=p^33，
取 p-adic 赋值得 4v_p(N)=33，矛盾。因此 (1) 中 p1<p2 自动成立。
可等价使用 p1<N^b<=p2。两个区间的素数测度不相交，既没有三角域的1/2，
也没有需要扣除的共享素数原子。这不是对任意实阈值成立的断言。

采用三个明确的外部输入：

**U-BJS**：[S2] BJS v6 Theorem 6、Table 1 的常密度下筛。
在其小素数例外集合乘积 W、乘积条件满足时，对 D>=z²，实际质量 M 的序列满足
\[
 S\ge(f(s)-154\epsilon e^2h_{BJS}(s))V_N(z)M
 -\sum_{d\mid P_N(z),\ d<WD}|r_M(d)|,\quad s=\log D/\log z, \tag{2}
\]
其中 0<epsilon<=1/200，s>=2 时 0<e²h_BJS(s)<=1。
154 来自表中该行和常数的单调性；导入定理与表值，不声称重做原数值证明。

**U-BV**：对 A0>=4，可取 B=A0+8，存在 C_BV 和起点，使
\[
R=N^{1/2}/T^B,\qquad
\sum_{n<R}\max_{(v,n)=1}\sup_{2\le y\le N}
 |\pi_{<}(y;n,v)-\operatorname{Li}(y)/\varphi(n)|
 \le E:=C_{BV}N/T^{A0}. \tag{3}
\]
Li(y)=integral_2^y dt/log t。[S3] p3 给出 maximal psi 形式。
用节省 A0+2、B=A0+8，右边第二项 sqrt(N)R log^6N 为 O(N/T^(A0+2))；
素数幂的粗界每模数 O(sqrt(N)T²) 更小。分部求和在 y>=2 上有有界总权，
由 Li 下限产生的常数/phi(n) 总计 O(log N)，亦可吸收。严格端点由左极限取得，
不为每模数另加1。这里导入经典定理，常数和起点不因 epsilon0、epsilon 或素数对而变化。

**U-M**：经典 Li、素数倒数 Mertens 与乘积 Mertens 渐近。
所用一致性在下文说明，未给出有效数值常数或完整数值 N0。
本轮不用原始 Iwaniec C_s、L_eta 或 CP6 加权分布候选。

## 2. 固定小素数预筛与两个合法模式

U-M 给固定 K，使任意偶数 N、2<=u<v 有
\[
\prod_{u\le p<v,p\nmid N}(1-1/(p-1))^{-1}
 \le(\log v/\log u)(1+K/\log u). \tag{4}
\]
先对全部奇素数用 Mertens 和收敛的 prime-minus-one 平方尾积，有限小 u 增大 K；
删去 p|N 只减小左边。这是统一的一侧估计，不是原 C_s 量词的证明。
固定 epsilon 后取 w=max(3,exp(2K/epsilon))，P0=prod_{p<w}p，
W_N=prod_{p<w,p∤N}p。最终要求 z>w；P0 固定且 W_N|P0。
对 u>=w，(4) 给相对误差<=epsilon/2；对 u<w 则从 w 起用 (4)。
由此满足 (2) 所需的严格乘积条件 (1+epsilon)log z/log u。
小素数没有从最终筛中删除，它们通过 W_N 放大余数范围。

令 h_star=(B log T+log P0)/T。写 m=p1p2、u=log p1/T、v=log p2/T。

* **对数模式**：D_m=R/(P0 m)，delta=h_star。
* **固定模式**：D_m=N^(1/2-sigma)/m，delta=sigma>0；额外要求 h_star<=sigma。

两种模式都有 m W_N D_m<=R。实际合法条件完全相同：
\[
 D_m\ge z^2\quad\Longleftrightarrow\quad u+v\le c-\delta.
 \qquad s_m=(1/2-u-v-\delta)/a. \tag{5}
\]
先从 (1) 删去非法的非负项，再调用下筛。
固定非法角落 u+v>c 不是随 N 消失的条带。
所保留区域 \(\mathcal R_\delta=\mathcal R\cap\{u+v\le c-\delta\}\) 上
2<=s_m<=smax=1061/264。临界线 s=2 可以使用 (2)，即使其主因子为负。

P0 可以极大，不计算它不等于把它设成1。
固定模式仍须支付完整起点 h_star<=sigma；对数模式不得抹去核漂移。

## 3. 连续的零延拓比较核

定义
\[
 k(s)=0\ (s\le2),\qquad k(s)=\log(s-1)/s\ (2<s\le smax).
\]
在 2<s<=smax，
\[
 k'(s)=\{s/(s-1)-\log(s-1)\}/s^2.
\]
因为 log(smax-1)<6/5（exp(6/5) 的前三次 Taylor 和已大于797/264），
s/(s-1)>=1061/797，故分子>=523/3985>0。
又 smax<5，故 k'>1/200；另一方面 k'<=1/[s(s-1)]<=1/2。
在 s=2 处 k 连续；延拓到左侧仍非负、单调且1/2-Lipschitz。
还可用下述范围分解得 k<=1/2。

由 [S1] Lemma 2.2（亦可由 [S2] 延迟微分方程逐段积分）得到
\[
 \psi(s):=f(s)/(2e^{\gamma_E})
 =\{\log(s-1)+\mathcal T((s-4)_+)\}/s\quad(s\ge2), \tag{6}
\]
其中 T 项只在 s>4 出现，且
\[
\mathcal T(w)=\int_0^w\frac{\log(1+x)}{2+x}\log\frac{3+w}{3+x}\,dx,
\quad0\le\mathcal T(w)\le w^3/36.
\]
最后一个界用 log(1+x)<=x、(2+x)>=2 及 log((3+w)/(3+x))<=(w-x)/3 积分即可。
本区间 w<=5/264，因此 T<1/1000。对 s<=3，k<=(s-2)/s<=1/3；
对 s>=3，分子<=6/5+1/1000、分母>=3。故 0<=k<=psi<=1/2。
因 0<gamma_E<1，0<=f<3。于是 (2) 的主因子绝对值至多3，不需要预先假定它非负。

置 K_delta(u,v)=k((1/2-delta-u-v)/a)，定义两个不同的固定量：
\[
 I_\delta=53\iint_{\mathcal R}K_\delta(u,v)\frac{du\,dv}{uv},\qquad
 g_\delta=53\iint_{\mathcal R}\psi((1/2-\delta-u-v)/a)\frac{du\,dv}{uv}, \tag{7}
\]
psi 在 s<=2 也延拓为0。I_delta<=g_delta，I 是比较量，不是未经修正的源端等式。
K_delta 在合法边界连续归零，在每个变量上非增；不需要用有跳跃的指标函数做主项转移。

## 4. 全部素数对共用一个 BV 预算，包括 d=1

对保留的 m，令 X_m=Li(Y)/phi(m)、M_m=|A_m|、Delta_m=M_m-X_m。
在 d|P_N(z) 上，(m,d)=1，且
\[
 |(A_m)_d|=\pi_{<}(Y;md,N),\quad
 r_m(d)=|(A_m)_d|-X_m/\varphi(d),\quad
 r_{M,m}(d)=r_m(d)-\Delta_m/\varphi(d). \tag{8}
\]
映射 (p1,p2,d)->p1p2d 是单射：两个大于等于 z 的素因子各一次，
其余因子均小于 z；两个素数分属不相交区间，顺序唯一。
实际余数条件 d<W_N D_m 给 md<R。d=1 同样属于该支撑，r_m(1)=Delta_m。
于是
\[
 \sum_{m,d}|r_m(d)|\le E,\qquad \sum_m|\Delta_m|\le E. \tag{9}
\]
没有素数对个数因子，也不能把第二式左端改成净偏差的绝对值。

由 n/phi(n)=sum_{d|n}mu²(d)/phi(d)，以及
prod_p(1+1/[p(p-1)])<=exp(sum_{n>=2}1/[n(n-1)])=e<3，有
\[
 \sum_{n<R}1/\varphi(n)<3(1+\log R).
\]
所以 (8) 的实际质量余数总和 <=(4+3log R)E。
逐项对带符号主因子 B_m=f(s_m)-154epsilon e²h_BJS(s_m) 使用
B_m V M_m >= B_m V X_m-3|Delta_m|，得到
\[
G_7\ge 2e^{\gamma_E}V\operatorname{Li}(Y)
 \sum_{m\ {\rm legal,good}}\frac{k(s_m)}{\varphi(m)}
 -154\epsilon V\operatorname{Li}(Y)\sum_{m\ {\rm legal,good}}\frac1{\varphi(m)}
 -(7+3\log R)E. \tag{10}
\]
正主项和负罚项分开，不能对整个可能为负的括号随意改分母。
因 log R<=T/2、T>=1、C(N)>=1/2，最后一项除以 S_N 至多17 C_BV T^(3-A0)。

## 5. 没有边界跳跃的双测度转移

在 [a,b]、[b,g] 上分别置
mu1=sum_{z<=p<N^b}(1/p)delta_{log p/T}，
mu2=sum_{N^b<=p<=N^g}(1/p)delta_{log p/T}，lambda_i(dt)=dt/t。
令 L1=log(b/a)<1/2，L2=log(g/b)=log(9/4)<1；这些粗界来自正项指数级数。
r_N 是两个闭 CDF 与其 lambda_i CDF 的偏差上确界的最大值，包含起点原子约定。
U-M 给 r_N=O_a(1/T+1/z)。假设 r_N<=1/2，则质量 M1<=1、M2<=3/2。

> **命题 M（单调转移）。** 若 0<=h<=1/2 连续非增，而带符号测度 nu 的闭 CDF
> 绝对值<=r，则 |integral h dnu|<=r/2。

证明：含左端点的 Stieltjes 分部积分给 h(right)F(right)-integral F dh。
其绝对值 <=r(h(right)+TV(h))=r h(left)<=r/2。
不假定起点无原子；端点质量未遗漏。
依次用在 (mu1-lambda1)×mu2 和 lambda1×(mu2-lambda2)，得
\[
 \left|\iint K_\delta d\mu_1d\mu_2-\iint K_\delta d\lambda_1d\lambda_2\right|
 \le\tfrac12r_N(M2+L1)\le r_N. \tag{11}
\]
这一界统一于 delta。合法区域移动不制造额外 CDF 跳跃项。

p|N 的坏素数倒数质量 beta1<=1/(az)，beta2<=1/(bN^b)<=1/(bz)。
删除坏点的 K 主项至多损失 (beta1 M2+beta2 M1)/2。
对正主项用 1/phi(m)>=1/m，便得
\[
53\sum_{m\ {\rm legal,good}}\frac{k(s_m)}{\varphi(m)}
 \ge I_\delta-53r_N-\frac{11925}{16z}. \tag{12}
\]
不再扣一次三角测度对角：这里是两个不相交素数区间的矩形乘积。
对负罚项则用上界
\[
 \sum_{m\ {\rm legal,good}}1/\varphi(m)
 \le M1M2/(1-1/z)^2\le6. \tag{13}
\]

## 6. 原生下界合同及量词顺序

记 A_N=2e^gamma Li(N)V/(53 S_N)，q_N=|A_N-1|。
乘积 Mertens 与 Li 给 q_N=O_a(1/T+1/z)，统一于偶数 N：
prime-minus-one 收敛尾积为1+O(1/z)，而 N 的>=z素因子至多1/a个，各缺失因子为1+O(1/z)。
这补足与 N 有关的奇异乘积，不把只删素数的一侧估计误当双侧等式。

theta=1-Li(Y)/Li(N) 满足 0<=theta<=32epsilon0/21：
Li(N)>=(N-2)/logN，Li(N)-Li(Y)<=epsilon0 N/log(N/2)，N>=16 时相乘的比值至多32/21。
保留原截断不能用扩大的集合下界代替。

假设 q_N<=1。由正主项非负及 (12)，无论其右侧是否为负，
A_N(1-theta) 所造成的损失最多 (q_N+theta)I_delta。
第8节证书给 I0<4，单调性给 I_delta<=I0。
(13)、e^gamma>=1、A_N<=2 给罚项系数154*53*6=48972。
合并 (10)-(13)：
\[
\boxed{\frac{G_7}{S_N}\ge I_\delta-
 [\tfrac{128}{21}\epsilon_0+4q_N+53r_N+\tfrac{11925}{16z}
   +48972\epsilon+17C_{BV}T^{3-A0}].} \tag{14}
\]
域条件为上述源输入起点、z>w、r_N<=1/2、q_N<=1、A0>=4，以及 (5) 的模式条件。
G7 在 [S1] (5.2) 中系数+1，所有亏损均在最终下界中相减，最后才除4。
本合同没有 C_s、L_eta 或 CP6 加权 BV，代价是 P0 水平与换基对数。

固定模式选 sigma=10^-7。第8节 I_sigma>=3.7902931。
给局部总损失 d0=3×10^-6，先固定 K，再取
\[
 \epsilon_0=\epsilon=\min\{1/400,\ d0/[4(128/21+48972)]\}.
\]
固定损失<=d0/4；此后固定 w,P0,A0,B,C_BV，最后增大 N 使剩余损失<=3d0/4、
z>w 和 h_star<=sigma。于是条件性地最终 G7/S_N>=3.7902901>3.79029。
这是存在性结论。T>=max{(2B/sigma)²,2log(P0)/sigma,1} 仅是 h_star<=sigma 的几何充分条件，
不是包含所有源常数的有效数值 N0，也没有计算巨大的 P0。

## 7. 二阶条带与一阶总损失不能混淆

对 0<=delta<=a/2，zero-extension 的1/2-Lipschitz性直接给
\[
0\le I_0-I_\delta\le \frac{53}{2a}L1L2\,\delta
 <\frac{2809}{16}\delta. \tag{15}
\]
这里已经包含移动区域和保留域内核漂移，不能再重复加同一条带成本。
单独考察条带 c-delta<u+v<=c，k(s0)<= (c-u-v)/(2a)，uv>=ab，积分得
\[
0\le\text{strip loss}\le\frac{b-a}{a^3b}\delta^2
 =\frac{14045}{16}\delta^2. \tag{16}
\]

总损失确实具有一阶下界，而不只是估计方法粗糙：取子矩形
[a,b]×[b,3b/2]。因 c-5b/2>=a/2，所有点在该 delta 范围仍合法。
第3节 k'>1/200 给
\[
I_0-I_\delta\ge\frac{53\delta}{200a}L1\log(3/2)
 \ge\frac{53}{120}\delta. \tag{17}
\]
最后用 log(b/a)>=(b-a)/b=20/53、log(3/2)>=1/3。
因此总损失不是 O(delta²)。对数模式可用 I0 加上 (2809/16)h_star 的单次亏损；
固定模式改用 I_sigma，没有 N-dependent 漂移项，但要求更强起点并牺牲系数余量。

## 8. 一维证书及五阶小角修正

t=u+v 的截片给
\[
l(t)=\max(a,t-g),\quad r(t)=\min(b,t-b),\quad
W(t)=t^{-1}\log\frac{r(t)(t-l(t))}{l(t)(t-r(t))}.
\]
对所选的三个 delta=0,10^-7,5×10^-7，delta<c-a-g=1/1166，所以分段端点为
\[
a+b,\quad2b,\quad a+g,\quad c-\delta.
\]
完整保留 gamma 上限的积分是
\[
I_\delta=\int_{a+b}^{c-\delta}H_\delta(t)W(t)dt,\quad
H_\delta(t)=\frac{4\log((1/2-\delta-t-a)/a)}{1/2-\delta-t}. \tag{18}
\]
这里没有额外1/v或三角域1/2。把上限 g 换成 c-u 会增加旧 #41 已记录的正三角形，
其增量在 delta=0 时<=1/557568；本轮未把这项假增益加入系数。

令 e_delta=max(0,1/2-delta-4a-(a+b))。正的高阶 T 修正仅在
(u-a)+(v-b)<e_delta 内，那里 s>=4、uv>=ab。由 T(w)<=w³/36，
\[
0\le g_\delta-I_\delta\le
 \frac{1}{36a^5b}\int_{x+y<e_\delta}(e_\delta-x-y)^3dxdy
 =\frac{e_\delta^5}{720a^5b}. \tag{19}
\]
e0=5/3498；(19) 在 delta=0 为625/22383509372928<2.793×10^-11。
这是正修正的解析上界，不是把它设为0。由此能同时界定完整固定核而不求嵌套积分。

### 人工求积余项

每个平滑段上令 y=1/2-delta-t，L=log((y-a)/a)。有
\[
H'=4[L/y^2-1/(y(y-a))],\quad
H''=4[2L/y^3-2/(y^2(y-a))-1/(y(y-a)^2)].
\]
统一 t>=19/100、y>=3/20、y-a>=3/40、0<=L<=6/5。
W=A(t)/t 中四个对数的参数为斜率0或1的仿射函数，位于[3/40,1]；
因此 |A|<=12、|A'|<=4/(3/40)、|A''|<=4/(3/40)²。
用乘积法则计算得到
\[
 |(HW)''|\le333783040000/185193<2000000.
\]
每段8192个中点，真实积分误差<=2000000 sum(length³)/(24×8192²)。
50位 mpmath.iv 包住所有中点运算，二进制端点精确转 Fraction，再加解析误差并向外舍入到18位。
分段点仅是积分边界，不声称跨点二阶可微。

实际计算共73728个中点：

| delta | I_delta 区间 | 完整 g_delta 的额外上宽 |
|---|---|---|
| 0 | [3.790296429629882382, 3.790299606400463397] | <=2.793e-11 |
| 1e-7 | [3.790293206551658497, 3.790296383322238964] | <=2.792e-11 |
| 5e-7 | [3.790280314228679342, 3.790283490999257618] | <=2.788e-11 |

选定的方便下界3.7902931低于旧零间隙比较下界，是参数取舍，不是新纪录。
在5e-7处，即使加上 (19)，完整 g_delta 上端点3.790283491027131158仍低于3.79029。
这否定的是该固定核比较，不是实际 G7 计数的上界或哥德巴赫反例。

## 9. 复现、审查与下一步

`check_g7_explicit.py --compute` 重算三个积分；`--check` 只重放有限测试并核对12个哈希，
不做求积。一次完整主计算实际16.10秒；normal/-O只对有限与检查模式比较。
有限 AP 模型使用 N=200..1200 step100、z=3/5/7、分界11/13、上界31、w=3/5、
R=16N、Y=3N/4、X=3N/7。X 是**人为有理主项**，不是 Li 实测误差，也不声称这些小 N 满足 BV。
单调转移测试用有理离散测度和非增的截断线性替代核；不是渐近定理的数值证明。

实际2327个有限实例、20项负面控制，均为同上下文回归，不是独立验证。
源定理、解析覆盖、实现信任与全局拼接必须分别审查。
本轮不改变全局账本或原始 Cs 审计状态；不用因子化权不等于修好了所有 factorable-only 支路。
下一任务：G3/G10 交换上界的范围与余数审计，先核对能否实例化已有绝对分布接口，
尤其不能把 G8 的权支撑自动搬给它们。

[S1] J. Li, J. Liu, *Theorem (1+1.9) on the Goldbach Conjecture*, arXiv:2606.05224v2,
https://arxiv.org/html/2606.05224v2 ，Lemma 2.2、§5.2、(5.2)、(5.31)-(5.32)。
[S2] M. Bordignon, D. R. Johnston, V. Starichkova, *An explicit version of Chen's theorem and the linear sieve*,
arXiv:2207.09452v6, https://arxiv.org/html/2207.09452v6 ，Theorem 6、Table 1。
[S3] R. C. Vaughan, *The Bombieri–Vinogradov Theorem*,
https://personal.science.psu.edu/rcv4/Bombieri.pdf ，p3 maximal theorem。
访问、截图与未获得的源字节哈希详见 source-lock.json。
