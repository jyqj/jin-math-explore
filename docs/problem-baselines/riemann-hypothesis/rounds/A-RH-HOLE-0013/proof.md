# A-RH-HOLE-0013: depth-coherent holes, realification, and a signed obstruction

Status: **proof_candidate**, not independently verified. Issue #79.
Parent: A-RH-LOC-0012 at `e1042ef83ff3a468dc0faf2d82d19e07b1e5be87`,
proof blob `a39aa5e3b2d146d50b33d27dd21d7a711499d7b0`.
This is a solver continuation. It does not close the unrestricted model problem
or supply a theorem about actual zeta zeros. All depths below are normalized
imaginary displacements: the pair is t +/- i a/(2 pi).

## 1. Model, inherited inputs and notation

Fix Q>=1, m_p in {0,1,2}, sum m_p=Q, t_p=p+tau_p with 0<=tau_p<1,
0<=a_p<=A<infinity and a_p=0 if m_p!=2. Extend periodically. Mark one is
simple real; mark two is a real double at a=0 or a conjugate pair otherwise.
Let s=#{m_p=1}/Q. On the unit-normalized box [-alpha/2,alpha/2], write

    B_a(v)=sum_p m_p exp(2 pi i t_p v) cosh(a_p v),
    L_alpha=1/alpha+(2/alpha^2)sum_{1<=j<alpha Q}
                         (alpha-j/Q)|B_a(j/Q)/Q|^2,
    delta=s+L_1-2>=0.                                           (1)

The all-real reference keeps the SAME centers and marks, replacing every a_p
by zero; denote its moments by L_alpha^0 and d_0=s+L_1^0-2. No rounding or
matching is used to define this reference.

For a finite cell block b of mass mu_b, its signed operator has kernel
alpha^(-1) B_a(u-v), and energy

    E_alpha(b)=int_{-alpha}^{alpha} w_alpha(v)|B_a(v)|^2 dv,
    w_alpha(v)=(alpha-|v|)_+/alpha^2.                            (2)

For pairwise calculations its real kernel is
K_alpha(d,a,b)=(1/4)sum_{e,f=+/-1}sinc(alpha[d-i(e a+f b)/(2 pi)])^2.
Individual complex summands need not be positive. Formula (2), not termwise
positivity of K, is used throughout this round.

Here are the precisely identified parent inputs. Put B_*=16/3. For any integer
L>=2, partition P=lcm(Q,L) cells starting at zero into L-blocks. Then

    |L_alpha-sum_b E_alpha(b)/P|<= b_{alpha,A}(L),
    b_{alpha,A}(L)=cosh(alpha A)^2/L
                        [8+32(2+log L)/(pi^2 alpha^2)].          (3)

A block is good if it has a simple mark and bad otherwise. Write k_* for the
least simple count in a good block, and take k_*=L if none are good. The
parent positive two-channel anchor estimate gives

    sum_good sum_p m_p a_p^2/P <= 4 eta_L,
    eta_L=C_A(pi^2 L^2+A^2/4)delta/k_*,
    C_A=7+(B_*/4)[2 cosh A+1+sqrt(4 cosh(A)^2-3)].                (4)

These are candidate dependencies, not already independently verified inputs.
Their mechanism can be checked without a source-level zeta assumption. For
(3), |K_alpha|<=cosh(alpha A)^2 and, when d!=0,
|K_alpha|<=cosh(alpha A)^2/(pi^2 alpha^2 d^2). At cell lag r>=2, |d|>=r/2,
and the crossing fraction of L-blocks is min(r/L,1). Sum both lag signs,
mass products <=4, and the harmonic/tail sums to obtain (3).

For (4), in a finite repeated family write Aop=S+P_+-N_-, U=ran P_+,
E=span((I-P_U)f_i : i simple), F=(U+E)^perp and Qop=2P_U+P_E. If nu is
nonsimple mass, n is simple count, xi=tr(P_U S), zeta=tr((I-P_U)N_-),
zeta_F=tr(P_F N_-), the exact signed slack is

    n+||Aop||_HS^2-2(n+nu)
      =||Aop-Qop||_HS^2+2(nu-2dim U)+2xi+2zeta+2zeta_F+n-dim E.

Its terms are nonnegative. Parity coloring of the supplied unit cells, followed
by the triangular-majorant Bessel bound 2+2/(3q^2) for a q-separated family,
gives B_*. The parent polar-Gram argument bounds simple off-diagonal energy by
7D, and the g/h cross term by (C_A-7)D. Thus total positive anchor energy is
<=C_A D. The modulus kernel is
[sin(pi d)^2+sinh(a/2)^2]/[pi^2 d^2+a^2/4]. Within an L-block its denominator
is <=pi^2 L^2+A^2/4 and its numerator is >=4 dist(d,Z)^2+a^2/4. Average over
anchors and pass from finite repetitions to (1). This proves (4) with the
parent's full Gram extraction as a pinned dependency. It does not assume all
signed pair summands are positive, nor infer coverage of bad blocks.

## 2. Exact common-depth domination

**Lemma 1.** In a finite block whose occupied atoms all have one depth c>=0,

    E_alpha(c)=int w_alpha(v) cosh(c v)^2 |B_0(v)|^2 dv
               >= E_alpha(0).                                 (5)

This holds for arbitrary real centers and nonnegative masses, at every alpha>0.
It needs no simple anchor, small defect, regular spacing or small common depth.
It is an energy inequality, NOT a Loewner-order assertion about the operators.
In the original model a good block will be assigned c=0; a bad block has only
marks 0/2, so assigning a common positive c does not turn simple marks into pairs.

Thus a hole with substantial, nonzero common depth can still be compared to
its real reference. This differs from charging the entire hole mass as lost.

## 3. A dimension-free cost for depth dispersion

For an L-block choose c_b=0 when it is good. When it is bad and mu_b>0, choose

    c_b=(sum_p m_p a_p)/mu_b,
    omega_b=sum_p m_p(a_p-c_b)^2.

For a vacant block take c_b=omega_b=0. Define

    Omega_L=sum_bad omega_b/P,
    V_L=sum_good sum_p m_p a_p^2/P + Omega_L <=4 eta_L+Omega_L.   (6)

Omega_L is weighted within-block depth variance divided by TOTAL mass P. It
is not a hole-mass proportion, and it does not penalize a nonzero common depth.
For hole mass h_L, 0<=Omega_L<=A^2 h_L/4 by the elementary variance bound.

**Lemma 2.** For two depth fields a,c in [0,A] on the same finite occupied cells,
with the same marks, let A_b and C_b be their signed operators. For 0<alpha<=1,

    ||A_b-C_b||_HS <= K_{alpha,A} sqrt(sum_p m_p(a_p-c_p)^2),
    K_{alpha,A}=sqrt(2 B_* alpha) sinh(alpha A),
    ||A_b||_HS, ||C_b||_HS <= J_{alpha,A} sqrt(mu_b),
    J_{alpha,A}=sqrt(2 B_*/alpha) cosh(alpha A).                  (7)

Proof. Real cell synthesis on the normalized alpha-box has squared norm at
most B_*/alpha. In the decomposition A_b=GG*-HH*, columns are
sqrt(m_p)e_{t_p}cosh(a_p u), sqrt(m_p)e_{t_p}sinh(a_p u).
Power series on |u|<=alpha/2 give

    ||G||op<=sqrt(2 B_*/alpha)cosh(alpha A/2),
    ||H||op<=sqrt(2 B_*/alpha)sinh(alpha A/2).

The mean-value theorem bounds column differences by
(alpha/2)sinh(alpha A/2)|a-c| and
(alpha/2)cosh(alpha A/2)|a-c|. Expand each difference GG*-G'G'* and HH*-H'H'*.
The two product terms in each expansion give K in (7). The separate HS norms
follow by multiplying operator and column HS bounds, using cosh^2+sinh^2=cosh(2x).
The argument remains valid at A=0; then K=0 and the only allowed depths are zero.

Sum the energy differences over disjoint blocks and use Cauchy-Schwarz and
sum mu_b=P. Since 2JK=2B_*sinh(2alpha A), put

    C_{alpha,A}=2B_* sinh(2alpha A).

Lemmas 1-2 and (3) then imply the main realification comparison

    L_alpha^0 <= L_alpha + epsilon_alpha(L),
    epsilon_alpha(L)=b_{alpha,A}(L)+b_{alpha,0}(L)
                                 +C_{alpha,A}sqrt(4 eta_L+Omega_L). (8)

Indeed sum E_0<=sum E_c<=sum E_a+C sqrt(V_L) P, and (3) is applied to both
the original and real-reference configurations. In particular

    0<=d_0<=delta+epsilon_1(L).                                 (9)

This controls energy, not distance to a global coset and not the original
operator's distance to its real reference. Only the blockwise perturbation to
common depth has a claimed HS bound. Common positive depth need not be small.

## 4. A finite real-model lower bound without simple anchors

Here every depth is zero, but phases and marks remain arbitrary. The exact
real pair expansion gives

    d_0=(1/P)sum_p sum_{q!=p}m_p m_q sinc(t_p-t_q)^2>=0.          (10)

The q sum uses the infinite periodic extension; same-center diagonal terms
have sum m_p^2/P=2-s. Different copies are different atoms. Absolute convergence
follows from one-cell geometry. Formula (10) is positivity available only in
the real reference, not in the original signed model.

Partition a superperiod into R-blocks, R>=2 independently of L. In each
nonempty block choose ANY occupied atom as a candidate anchor, average its
rounding cost with weights m_i, and then choose the best. Since block mass is
at least one and |t_i-t_j|<R,

    Z=sum_blocks sum_p 4m_p dist(t_p-theta_b,Z)^2,
    Z/P <= pi^2 R^2 d_0.                                      (11)

To verify (11), multiply an anchor's cost by its mass m_i and sum over anchors:
sin(pi d)^2>=4 dist(d,Z)^2 bounds this sum by pi^2 R^2 times the block's
ordered weighted off-diagonal sinc energy. Divide by its mass >=1, then sum
blocks and use (10). No simple mark is required; empty blocks contribute zero.

Nearest-coset rounding aggregates mass into at most R+2 consecutive integer
sites with mass <=4 per site. Squared mass can only increase. On the alpha-box,
the real-phase HS comparison gives error at most

    (X_alpha/2)sqrt(Z/P),
    X_alpha=pi alpha[sqrt(2 B_*/alpha)+2/sqrt(alpha)].

For alpha>1/2 put f_alpha=(2alpha-1)/alpha^2, c_alpha=1/alpha-f_alpha. The finite
integer occupancy estimate obtained by periodization and Parseval is

    sum E_rounded/P >= I_alpha(R,s)-W_alpha(R),
    I_alpha(R,s)=f_alpha(2-s)+c_alpha R/(R+2),
    W_alpha(R)=32[3+log(R+2)]/(pi^2 alpha^2 R).                  (12)

The constant-mode term uses Cauchy-Schwarz over at most P/R nonempty blocks.
For the boundary term, periodization adds real nonnegative sinc squares;
with masses <=4 its added energy is at most
32[H_{K-1}+K/(K-1)]/(pi^2 alpha^2) per K=R+2 sites, hence (12).
The nonzero Fourier symbol floor is f_alpha. These arguments do not require
alpha R integer or R dividing the original period.

The direct-sum HS triangle inequality and real localization now prove

    L_alpha^0 >= G_alpha(R,s,d_0),
    G_alpha(R,s,d)=
      [sqrt((I_alpha(R,s)-W_alpha(R))_+)-k_alpha R sqrt(d)]_+^2
                  -b_{alpha,0}(R),
    k_alpha=pi X_alpha/2.                                     (13)

This is an explicit finite inequality for every Q,R. It is not a novel claim
that real near-orthogonality has local rigidity; the new role is a quantified,
anchor-independent component in the signed hole comparison.
Combining (8)-(9) with monotonicity of G in d gives

    L_alpha >= G_alpha(R,s,delta+epsilon_1(L))-epsilon_alpha(L). (14)

All square roots and both positive parts have their stated domains. L and R
are separate freely chosen integers, and no limit interchange is used in (14).

## 5. Consequences with the order of limits explicit

Consider any sequence with a common finite cap A, arbitrary periods Q_n,
s_n->2/3 and delta_n->0. Define partitions at shift zero as above and put

    Omega_* = liminf_{L->infinity} limsup_{n->infinity} Omega_{n,L}. (15)

First fix L and let n tend to infinity. Then eta_{n,L}->0. Taking a sequence
of L realizing (15), the boundary terms in (8) disappear. This yields

    limsup_n d_{0,n} <= C_{1,A} sqrt(Omega_*),
    liminf_n (L_{alpha,n}-L^0_{alpha,n})
                              >=-C_{alpha,A}sqrt(Omega_*).     (16)

Each statement uses inequalities valid for every fixed L, so no n-dependent
choice of partition or reversal of the limits is implicit. With R fixed,
continuity and monotonicity of (13) give

    liminf_n L_{alpha,n} >=
      G_alpha(R,2/3,C_{1,A}sqrt(Omega_*))
                              -C_{alpha,A}sqrt(Omega_*).       (17)

In particular, if **Omega_*=0**, take R to infinity AFTER these limits:

    liminf_n L_(3/4,n) >= 44/27 = 19/12+5/108.                  (18)

There is no bound on H, the parent's anchor-free mass fraction, in (18).
The new hypothesis is local depth coherence in the precise sense (15), not
an assertion that (15) vanishes for every small-defect sequence. If H=0 then
Omega_*=0 follows from Omega_L<=A^2 h_L/4. Conversely, a large H can coexist
with Omega_*=0. The parent's H<10.72% criterion can still be stronger in other
classes; retain both criteria rather than claiming one subsumes the other.

An explicit positive tolerance is also available. For A>0, alpha=3/4, set

    g_R=sqrt((I_(3/4)(R,2/3)-W_(3/4)(R))_+)
                                      -sqrt(19/12+b_(3/4,0)(R)),
    omega_R(A)=[(g_R)_+/(k_(3/4) R sqrt(C_(1,A))
                                      +sqrt(C_(3/4,A)))]^4.    (19)

If both limiting budgets delta_n->0 and limsup L_(3/4,n)<=19/12 hold, then
Omega_*>=omega_R(A) for every R with g_R>0. To see this put t=Omega_*^(1/4).
The clipped norm inequality (17) implies

g_R <= k_(3/4) R sqrt(C_(1,A)) t + sqrt(C_(3/4,A)) t,

using sqrt(u+v)<=sqrt(u)+sqrt(v); if the inner positive part is zero the same
necessary inequality holds directly. This proves (19). No optimization claim
is attached to choosing R. At A=0 all depths vanish and (18) applies directly.

### Exact conservative tolerance, not a floating certificate

For A<=log 2, R=8192, the two budgets are incompatible whenever Omega_*<=10^-33.
Here is a rational certificate of sufficiency. At A=log 2,
C_1=20, C_(3/4)=28 sqrt(2)/3<14 and
k_(3/4)=pi^2(sqrt(2)+sqrt(3)/2)<25. Thus the denominator in (19) is
<125R+4. Use 9<pi^2<10 and log(R+2)<10 to obtain

    I-W >=32/27+(4/9)R/(R+2)-(512/81)13/R >=(509/400)^2,
    19/12+b <=19/12+[8+(512/81)12]/R <=(101/80)^2.

The last comparisons are exact rational inequalities at R=8192, hence g_R>=1/100.
The log bound follows, for example, from the rational partial sum
sum_{j=0}^{10}10^j/j!>8194. Finally

    [1/(100(125*8192+4))]^4 >10^-33.

The standard bound 3<pi<22/7 suffices for the pi inequalities. All finite rational
checks are executed by the checker. The tolerance is very conservative and
should not be described as numerically competitive or sharp. Seventy-digit
formula evaluation of (19) is reported separately, without interval certification.

## 6. Exact failure of unqualified variable-depth erasure

**Counterexample to a stronger block lemma, not to RH or the two-budget target.**
Take three mass-two centers at 1/2,3/2,5/2, alpha=3/4, and depths (0,2/15,0).
They occupy three supplied cells, form a valid finite anchor-free block, and
have total mass six; a finite block is not required to have mean mass one.
Put epsilon=alpha*(2/15)=1/10 and scale v=alpha x in (2). Removing the harmless
central phase, its transform is 2[2cos(3 pi x/2)+cosh(epsilon x)]. Thus

    E_alpha(a)-E_alpha(0)=C epsilon^2 + Rem,
    C=2/3-512(pi+1)/(27 pi^4) <=-1/10,
    |Rem|<=(2/5)epsilon^4.                                   (20)

Derivation: for w(x)=(1-|x|)_+, int w x^2=1/6 and int w x^4=1/15.
Twice differentiating sinc(d)^2 gives
int w x^2 cos(2 pi d x)=-(sinc(d)^2)''/(4 pi^2); at d=3/4 this equals
-64(pi+1)/(27 pi^4). Expanding the squared transform gives C as above.
For |z|<=epsilon, cosh z-1=z^2/2+r with |r|<=cosh(epsilon)z^4/24.
The squared-transform remainder is at most
[cosh(epsilon)^2+cosh(epsilon)]epsilon^4 x^4; cosh(1/10)<2 gives (20).
The coefficient bound follows rationally from 3<pi<22/7:
C <= 2/3-2048/[27(22/7)^4] <-1/10. Consequently

    E_(3/4)(0,2/15,0)-E_(3/4)(0,0,0) <=-3/3125<0.             (21)

So even exact integer-coset centers do not license erasing independently
varying depths at the short scale. This is exactly why (8) keeps a dispersion
charge. The example does not show Omega_*>0 along delta->0 sequences and does
not prove that the depth-coherence hypothesis is necessary for the final target.

## 7. Scope gain, surviving problem and audit

The parent's three-run family has Q=6k: 4k simple marks, k vacancies, k pairs
at depth log 2, all phases 1/2. For every fixed L, only O(L) mass near the
interfaces affects good blocks. All bad blocks have a common occupied depth,
so Omega_{k,L}=0 exactly, while h_{k,L}->1/3. Its long defect tends to zero;
its short moment tends to 16/9. These asymptotics follow from the finite
homogeneous-run Fejer estimate E_alpha=m^2 ell/alpha+O_A,alpha(log ell) and
the signed interface bound (3), as proved in the parent. Thus H=1/3 excludes
this family from the parent's coverage criterion, while (18) applies. This
checks compatibility, not a newly invented counterexample or a first proof
of that particular family's short energy. Arbitrary phases and rapidly changing
marks within depth-coherent bad blocks remain allowed by the new theorem.

The unresolved interface is now explicit: remove the small-Omega_* assumption,
prove a substitute operator-energy constraint for depth-incoherent holes, or
construct a genuine sequence meeting BOTH budgets. The finite example (21)
and the parent's scalar relaxed point do not do this. Proposed next attempt:
A-RH-DISP-0014, a signed depth-covariance estimate without a common-depth gauge.

An independent verifier must audit (3)-(4)'s pinned dependency, common-depth
energy versus operator order, every normalization in (7)-(14), the two partition
scales and limit order, the rational tolerance, and the analytic remainder in
(20). Tests are solver self-checks, not a receipt. No source cell extraction,
source weights/localization, exceptional-energy bridge, arithmetic moment bound,
unconditional zero-proportion improvement, literature-wide novelty or RH proof
is claimed. The new conditional theorem is a restricted-model research gain.
