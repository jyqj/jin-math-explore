# G8 显式筛替换：不再使用未知的 C_s 或 L_eta

**CP-ERR-0007；solver proof candidate；尚未独立验证。**
本轮承接 CP6 的“线性筛常数统一性”问题。结论是一个可审查的**替代接口**，
不是声称已获得无法访问的 Iwaniec 原文证明。它只适用于具有绝对余数平均界的 G8 支路。

## 1. 输入等级与一个先于常数的端点问题

[S1] Li–Liu v2 (2.8) 把水平 Q 的支撑写为 q<Q，又要求对每个
Q=Q1 Q2、Q1,Q2>=1，两个因子也满足各自的严格支撑。按印刷文字取 Q1=1，
第一个因子在全部正整数上为零，Dirichlet 卷积也为零。因此：

> **命题 E（字面定义退化，证明候选）。** 该严格支撑定义下，唯一的 well-factorable 权是零权。
> 证明：在允许的分解 1·Q 上应用支撑条件即可。这个推论覆盖任意 Q>=1，不靠有限枚举。

常见闭支撑约定 q<=Q 允许水平1的卷积单位 delta_1；把 q>=Q 改成 q>Q
可消除上述退化，但必须在依赖中显式注明约定修正，不能把两套端点混用。
本轮的替代路线不用 well-factorable 权，所以不依赖这个修正。
这不是对标准 well-factorable 定理的反驳，更不是论文主定理或哥德巴赫的反例。
即使修正端点，[S1] (2.13) 的隐含常数对 eta 的统一性仍需原始来源审查。

本笔记使用三类明确输入：

* **U-BJS**：[S2] Bordignon–Johnston–Starichkova v6 Theorem 6、Table 1 的常密度特例。
  此处导入该定理及表中已给出的常数，不声称独立重做其数值证明。
* **U-WBV**：第3节写出的绝对余数界。CP6 为它提供了候选证明，但没有独立 receipt；
  本轮把它保留为显式依赖，不以 PR 合并或测试通过替代该依赖的审查。
* **U-M**：通常的 PNT、素数倒数及乘积 Mertens 渐近。由它们推出的密度一致性在第4、8节说明。

Iwaniec 1980 的出版信息已核查，原 PDF 获取失败；其 C_s 审计仍为 UNRESOLVED。

## 2. 原目标、交换多重序列及非零异常成本

固定偶数 N>=16，0<epsilon0<1，c=3/11，z0=N^c。
令 A={N-b:b<(1-epsilon0)N，b为素数}，P(N) 为不整除 N 的素数集合。
S 计数未被指定小素数筛去的元素；序列均按重数计数，A_m 表示被 m 整除的子序列。
原对象为 [S1] §5.3：
\[
G_8=\sum_{z_0\le p_1\le p_2,\ p_1p_2^2\le N\atop(p_1p_2,N)=1}
 S(A_{p_1p_2};P(Np_1),p_2). \tag{1}
\]
定义
\[
\mathcal M_N=\{p_1p_2:z_0\le p_1\le p_2,\ p_1p_2^2\le N,\ (p_1p_2,N)=1\},
\quad \mathcal B=(N-mp)_{m\in\mathcal M_N,\ p\text{ prime},\ mp<N},
\tag{2}
\]
\[
X=\sum_{m\in\mathcal M_N}\operatorname{Li}(N/m),\qquad M=|\mathcal B|.
\]
Li(x)=integral_2^x dt/log t。乘积 m 的分解唯一，故其指示函数<=1，
支撑 N^(6/11)<=m<=N^(2/3)；但 B 的值可能重复，不可去重。

为不依赖旧候选的“等式”，重新给出所需的交换上界。
每个 a<N 最多有3个>=z0的素因子槽位，因为 z0^4>N，提取对重数至多3。
对 (1) 的存活项 a=p1p2 v，分别支付：
(a,N)>1 时输出素数 b 必整除 N，成本<=3 log N/log2；
p1²|a 时成本<=3 sum_{p>=z0} floor(N/p²)<=3N/(z0-1)；
v=1 时 p1p2<=N^(2/3)，由唯一分解成本<=N^(2/3)。
其余项若 v 合数，则含素因子<=N^(5/22)<z0，且该因子既不整除 N 也不等于 p1，
与存活矛盾；若 v 为小于 p2 的素数亦矛盾。所以其余项是有序三素数表示。
这些表示进入 (2) 的索引集合。若目标输出 b 为小于 Z 的素数，重数总计至多3Z。
因此对任何 2<=Z<=N^(1/4)，
\[
G_8\le S(\mathcal B;P(N),Z)+E_{exc},\quad
E_{exc}=N^{2/3}+\frac{3N}{N^{3/11}-1}+\frac{3\log N}{\log2}+3Z. \tag{3}
\]
这是上界方向的扩大，允许删去输出截断；不能把异常项免费丢弃。
本轮没有重算或提升旧 G8 交换候选，而是在此保留自足的必要组合论证。

## 3. 绝对分布输入：d=1 不能遗漏

对平方自由 (d,N)=1，写
\[
r(d)=\sum_{m\in\mathcal M_N,(m,d)=1}
 \left[\pi_{<}(N/m;d,Nm^{-1})-\frac{\operatorname{Li}(N/m)}{\varphi(d)}\right].
\]
采用如下精确 U-WBV 形式：对固定 A>=4，B=A+8，存在 C_A 和起点，使
\[
R=\frac{\sqrt N}{\log^B N},\qquad
\sum_{d<R,(d,N)=1}\mu^2(d)|r(d)|\le E_D:=C_A N/\log^A N. \tag{4}
\]
原 CP6 的常数允许从 A>=3 中选 A>=4，且与本轮小参数无关。
只有对实际 d|P_N(Z) 才有 (m,d)=1，因为 m 的全部素因子>=N^(3/11)>Z。
于是这些 d 上
\[
|\mathcal B_d|=X/\varphi(d)+r(d),\qquad r(1)=M-X. \tag{5}
\]
主特征中 p|d 的修正已在 CP6 的 r(d) 和 C_A 内，不能再称其为零。
(4) 必须包含 d=1；如果只导入非平凡模数或只导入带符号权平均界，后续推导不成立。

## 4. 用固定小素数集合换取任意小的显式误差

对 p∈P(N)（均为奇素数）取 g(p)=1/(p-1)，
在所需平方自由 d 上 g(d)=1/phi(d)。设 V_N(Z)=prod_{p<Z,p∤N}(1-g(p))。
通常的 Mertens 乘积估计给某个固定 K>0，使全部偶数 N、2<=u<v 满足
\[
\prod_{u\le p<v,p\nmid N}(1-g(p))^{-1}
\le\frac{\log v}{\log u}\left(1+\frac K{\log u}\right). \tag{6}
\]
理由：先对全体奇素数，用 (1-1/(p-1))=(1-1/p)(1-1/(p-1)^2)
和可收敛的第二个乘积取得强的一侧 Mertens 界；有限小 u 区域增大 K。
再删除整除 N 的素数只会减小左边。K 因而可以先于 N 和小参数固定。
这不等于证明原始 well-factorable 定理的 C_s 统一性。

给定 0<epsilon<=1/200，固定
\[
w=\max\{3,\exp(2K/\epsilon)\},\quad
P_0=\prod_{p<w}p,\quad W_N=\prod_{p<w,p\nmid N}p. \tag{7}
\]
P0 与 N 无关，W_N|P0。对 u>=w，(6) 的误差<=epsilon/2；
对 u<w<Z，从 w 起应用 (6)，再用 log u<log w；Z<=w 时乘积为空。
故任意1<u<Z都有
\[
\prod_{u\le p<Z,p\nmid N,p\ge w}(1-g(p))^{-1}
 <(1+\epsilon)\frac{\log Z}{\log u}. \tag{8}
\]
这正是 [S2] (4) 去掉有限异常素数集合后的条件。小素数没有从最终目标中消失：
它们通过定理中的 W_N 进入余数支撑，必须付出水平成本。

**合法水平选取：**
\[
D=R/P_0,\quad Z=\sqrt D,\quad
h_*:=\frac{B\log\log N+\log P_0}{\log N}. \tag{9}
\]
以下要求 log N>=1、0<=h_*<=1/4 以及 Z>=2（最终可令 Z>w）。
这给 log Z=(1/4-h_*/2)log N>=log N/8，且 Z<=N^(1/4)。
[S2] (10) 的实际余数范围为 d<W_N D<=R，完整落在 (4) 中。
不能取 D=R 后把 d<W_N R 当成 d<R。有限反例：W_N=3、R=D=100、Z=10 时，
105=3·5·7 是合法 Z-smooth 数，100<105<300；该例只反驳错误的支撑包含判断。

P0 可能极大。本轮只使用它在 epsilon 固定后为一个有限常数；没有计算这一个巨大乘积，
没有把固定 P0 所造成的起点成本隐藏成零，也没有给出可执行的数值 N0。

## 5. 定理的真实质量不能直接换成 X

[S2] Theorem6 对常密度给出的主项是 V_N(Z)M，而不是任取的 X V_N(Z)。
令 Delta=M-X。相应误差是
\[
r_M(d)=|\mathcal B_d|-M g(d)=r(d)-g(d)\Delta. \tag{10}
\]
特别 r_M(1)=0，但 r(1)=Delta 未必为零。若把 (5) 的 r(d) 原封不动代入该定理，
就错换了主项。本轮保留这个修正，不能用“两个量渐近相同”跳过它。

> **命题 H（统一 rebasing 成本，证明候选）。** 对 T>=1，
> \(\sum_{n<T}1/\varphi(n)<3(1+\log T)\)。因此实际筛支撑上的
> \(\sum|r_M(d)|\le(4+3\log R)E_D\)。

证明：n/phi(n)=sum_{d|n} mu²(d)/phi(d)，所以
\[
\sum_{n<T}\frac1{\varphi(n)}
\le(1+\log T)\sum_{d\ge1}\frac{\mu^2(d)}{d\varphi(d)}.
\]
后一和的 Euler 乘积<=exp(sum_p1/[p(p-1)])<=e<3，
因为 sum_{n>=2}1/[n(n-1)]=1。由 (4) 的 d=1 项，|Delta|<=E_D，
再对 (10) 使用三角不等式即得结论。
这个 logarithm 是保守的换主项成本，不声称最优，也不能在误差预算里省略。

例：单元素序列{3}，X=2，d=3，g(3)=1/2。
旧 r(3)=0，而新 r_M(3)=1/2；r(1)=-1 正好通过 (10) 修正。
这是有限筛数据的精确反例，不是 prime-distribution 或 Goldbach 反例。

## 6. 显式筛常数与原生上界

[S2] Table1 的 epsilon=1/200 一行给 C1=153、C2=154，且常数随 epsilon 减小不增。
因此本范围保守采用154。在 s=logD/logZ=2，e² h_BJS(2)=1，F(2)=e^gamma。
由该定理的上界（使用弱不等号也覆盖零质量序列），
\[
S(\mathcal B;P(N),Z)
\le(e^\gamma+154\epsilon)V_N(Z)M+\sum_{d\mid P_N(Z),d<W_N D}|r_M(d)|. \tag{11}
\]
BJS 的 h_BJS(s) 不要与 (9) 的 h_* 混淆。
0<gamma<1 给 e^gamma<3；154epsilon<=0.77；V<=1。
将 M<=X+|Delta| 代入 (11)，主项换算成本最多4E_D。
联立 (3)、命题 H 得
\[
\boxed{G_8\le(e^\gamma+154\epsilon)V_N(Z)X+
 (8+3\log R)C_A N/\log^A N+E_{exc}.} \tag{12}
\]
该界不出现原 C_s，不出现 L_eta=exp(8eta^-3)，也不用 well-factorable 定义。
代价是 P0 水平缩减及一个对数损失；它不是免费地把未知参数删掉。

## 7. 归一化：六项误差全部保留有害符号

取与 [S1] (1.3) 一致的
\[
C(N)=\prod_{p>2}(1-(p-1)^{-2})\prod_{p>2,p\mid N}\frac{p-1}{p-2},
\quad \mathcal S_N=C(N)N/\log^2 N.
\]
因 p−1 是整数 n>=2 的一个子集，prod_{n=2}^M(1−1/n²)=(M+1)/(2M)，有 C(N)>=1/2。
设
\[
J=\int_{c}^{1/3}\frac{du}{u}\int_u^{(1-u)/2}\frac{dv}{v(1-u-v)},\quad g_8=8J,
\]
\[
q_X=\max\{0,X\log N/N-J\},\qquad
q_V=\left|\frac{e^\gamma\log Z\,V_N(Z)}{2C(N)}-1\right|. \tag{13}
\]
两个缺陷都按实际对象定义，而不是自动给定数值零。要求 q_V<=1/2。
第9节给 0<g8<1。因 e^gamma>1，(12) 正主项/S_N 至多
\[
\frac{8(1+154\epsilon)(1+q_V)}{1-2h_*}(J+q_X). \tag{14}
\]
记 a_*=(1+154epsilon)(1+qV)/(1−2h*)。在声明范围内 a_*<=6，且
\[
a_*-1\le2q_V+4h_*+462\epsilon.
\]
证明：分子减去1−2h*后为 qV+2h*+154epsilon(1+qV)，分母>=1/2，qV<=1/2。
于是 (14)<=g8+48qX+2qV+4h*+462epsilon。

余数归一化后，由 logR<=logN/2、logN>=1，
\[
2(8+3\log R)C_A\log^{2-A}N\le19C_A\log^{3-A}N.
\]
综上得到本轮主要的候选契约：

> **命题 G（G8 的无 C_s 替代接口，条件证明候选）。**
> 在 (1)–(9)、U-BJS/U-WBV/U-M 及上述明确范围下，
> \[
> \boxed{\frac{G_8}{\mathcal S_N}\le g_8+
> 48q_X+2q_V+4h_*+462\epsilon+
> 19C_A\log^{3-A}N+\frac{2E_{exc}\log^2N}{N}.} \tag{15}
> \]
> G8 在总下界中的系数是 −2，故六项误差全部乘2，再与其余项组合，最后才除4。

(15) 完全替换本支路旧的 eta-sieve 成本，不是额外叠加在旧误差上。
原 CP6 中主特征、非本原修正已在 C_A 里；rebasing (10) 则是本轮新产生的成本。
不要把两者重复计费，也不要把命题 G 推广到只有带符号 well-factorable 平均界的支路。

## 8. 参数顺序、缺陷收敛与局部后果

先用 U-M 固定 K；给定 delta>0，取
\[
\epsilon=\min\{1/400,\delta/(4\cdot462)\}.
\]
再固定 w、P0，取 A>=4、B=A+8 和 U-WBV 的 C_A、起点，最后才选择 N。
这样固定损失462epsilon<=delta/4，而 h_*→0。P0 虽巨大但已固定。

证明 q_X→0 的上界足够：扩大 (2) 的 m 集去掉 (m,N)=1 不等式方向有利。
素数倒数测度在 [3/11,4/11] 上收敛到 du/u，因端点原子<=N^-c趋零；
乘积测度亦收敛。域 c<=u<=1/3,u<=v<=(1−u)/2 的边界对极限测度为零，
核1/(1−u−v)连续有界，离散对角质量<=N^-c sum1/p趋零。
又 Li(N/m) 的渐近在 N/m>=N^(1/3) 上一致，所以 limsup X logN/N<=J。
没有从这个定性证明生成伪数值误差率或共同阈值。

q_V→0 同样一致于偶数 N：对固定 Z，写有限乘积恒等式
\[
\frac{V_N(Z)}{2C(N)\prod_{p<Z}(1-1/p)}
=\prod_{p\ge Z,p>2}(1-(p-1)^{-2})^{-1}
 \prod_{p\ge Z,p\mid N}\frac{p-2}{p-1}.
\]
第一尾积为1+O(1/Z)；后者至多有logN/logZ<=8个因子，亦为1+O(1/Z)。
普通 Mertens 乘积完成归一化。其余 (15) 的项也趋零：A>=4；
E_exc/N=O(N^-1/3+N^-3/11+logN/N+N^-3/4)。

因此在已声明输入下，最终 G8/S_N<=g8+delta。
实际保守 g8 cap 为0.609611574；取 delta=8×10^-6，得到0.609619574<0.60962。
这说明原局部上界可以在不使用未知 C_s 的路线中保住，**不是**一个新的数值纪录。
没有源常数数值、可用 P0 枚举或有效数值 N0；特别，CP6 的 SW 来源仍保留非有效性。

## 9. 可复现固定积分及失败控制

对 J 先积分 v，再令 t=1/u−1，得到
\[
g_8=8\int_2^{8/3}\frac{\log(t-1)}t\,dt
=8\int_0^{2/3}\frac{\log(1+x)}{2+x}\,dx.
\]
对 |x|<1，
\[
\frac{\log(1+x)}{2+x}=\sum_{n\ge1}(-1)^{n+1}c_nx^n,
\qquad c_n=\sum_{k=1}^n\frac1{k2^{n-k+1}},\quad0<c_n<1.
\]
绝对收敛允许积分；截到 n=96 后的绝对尾界不超过
\[
\rho=\frac{8(2/3)^{98}}{98(1-2/3)}.
\]
程序实际用 Fraction 重算分子分母并向外舍入，得到
`[0.609611573201938690, 0.609611573201938694]`。
这也给出了第7节需要的0<g8<1。它不是实际有限 N 的 G8 计数区间。

有限检查覆盖端点卷积、totient除数恒等式、预筛支撑、实际多重序列、rebasing符号及主项放大。
同一 solver 编写的证明和检查器不是独立验证；BJS Table1 被引用而没有在本轮重算。
负面控制拒绝省略 P0、忽略 d=1、错写 log^(2−A)、使用未选的小 epsilon、
把 eta C(eta) 误认作趋零以及擅自提升来源/全局状态。

## 10. 研究边界与下一步

原任务的两个层次现已分开：**原始 C_s 量词审计仍未解决；G8 对它的依赖有了替代候选。**
适用差异是关键：G8 有绝对余数界，允许 BJS 的绝对余数；L35 等支路若只给权平均，
就不能删除权而获得绝对平均。不能把本轮结果宣传为已统一处理全部十二项。
下一 solver 任务可将同一预筛/质量转换机制实例化到 G1/G2 的下界，检查负主项情形和固定筛水平余量；
应保留旧候选，并把原 well-factorable 支路的端点与 C_s 源门槛另列。

[S1] J. Li, J. Liu, *Theorem (1+1.9) on the Goldbach Conjecture*, arXiv:2606.05224v2,
(2.6), (2.8)–(2.13), §5.3, (5.41), (5.51). https://arxiv.org/html/2606.05224v2

[S2] M. Bordignon, D. R. Johnston, V. Starichkova, *An explicit version of Chen's theorem and the linear sieve*,
arXiv:2207.09452v6, Theorem6, (3)–(11), Table1 and its monotonicity statement.
https://arxiv.org/pdf/2207.09452v6

[S3] H. Iwaniec, *A new form of the error term in the linear sieve*, Acta Arith.37(1980),307–320,
DOI10.4064/aa-37-1-307-320. Metadata only; original PDF acquisition failed.
