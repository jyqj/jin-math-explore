# A-RH-RMS-0011: RMS transfer and the remaining global-phase obstruction

**Evidence:** `proof_candidate`. Solver continuation, not independent verification.
Mathematical parent: A-RH-PER-0010, commit
`d00192b4b2cfb5669c2560c5f02e8d6ed3988a59`, README blob
`0757e3da76c7a22b1945fbab133ba46fe5c73f8a`.
The new transfer proof is finite-dimensional and self-contained below. Section 5
re-derives the parent's anchor input so that its additional hypotheses are visible.
No statement here supplies a representation or an arithmetic budget for zeta zeros.

## 1. Model and normalization

Let Q be a positive integer, indexed by p=0,...,Q-1. Assume

    m_p in {0,1,2}, sum m_p=Q,
    t_p=p+tau_p, 0<=tau_p<1,
    0<=a_p<=A<infinity, a_p=0 when m_p!=2.

A mark 0 is a vacancy, mark 1 is simple real, and mark 2 is either a real
double (a=0) or the pair t_p +/- i a_p/(2*pi), each member of multiplicity one.
The simple fraction is s=#{p:m_p=1}/Q. This is a supplied cell representation,
not a representation extracted from a small defect. Quantitative anchor claims
require s>0; the RMS comparison itself also applies when s=0.

Define, for real v and 0<alpha<=1,

    B(v)=sum_p m_p exp(2*pi*i*t_p*v) cosh(a_p*v),
    b_j=B(j/Q)/Q,
    L_alpha=1/alpha+(2/alpha^2) sum_{j=1}^{Q-1}(alpha-j/Q)_+ |b_j|^2,
    delta=s+L_1-2.                                                   (1)

An endpoint j=alpha Q has zero weight. The definition does not require alpha Q
integer. Set u_j=(j-(Q-1)/2)/Q and e_t(j)=exp(2*pi*i*t*u_j)/sqrt(Q).
Let G and H have columns sqrt(m_p)e_{t_p}cosh(a_p u) and
sqrt(m_p)e_{t_p}sinh(a_p u), respectively. Then

    T=GG*-HH*,  T(j,k)=B((j-k)/Q)/Q,
    diag(T)=1,  ||T||_F^2/Q=L_1.                                    (2)

The last identity follows by counting Q-|j-k| entries per diagonal. In particular,
this is not a numerical approximation of a continuous operator.

There is also the parent's exact periodic-limit interpretation. Repeat the cells
M times at spacing Q, use unit-normalized exponentials on [-alpha/2,alpha/2], and
write D_M(v)=sum_{l=0}^{M-1}exp(2*pi*i*l*v). The signed operator energy is

    E_(alpha,M)=alpha^(-2) integral_{-alpha}^{alpha}
        (alpha-|v|)|B(v)|^2 |D_M(Qv)|^2 dv.

Periodize w(v)=(alpha-|v|)_+|B(v)|^2 by W(x)=sum_k w((x+k)/Q).
Changing variable gives E/(MQ)=integral_0^1 W(x)|D_M(x)|^2 dx/(alpha^2 M Q^2).
Continuity and the Fejer approximate identity give W(0)/(alpha^2 Q^2), which is
(1), since B(0)=Q and |B(-v)|=|B(v)|. Here M tends to infinity for each fixed
pattern; no uniform finite-repetition error as Q grows is asserted.

## 2. Collision cap under nearest-coset rounding

Choose any theta in [0,1). Round with the fixed tie convention

    k_p=floor(t_p-theta+1/2), e_p=t_p-theta-k_p,
    M_j=sum_{k_p=j mod Q} m_p,
    E_ph=(1/Q)sum_p m_p e_p^2, E_dep=(1/Q)sum_p m_p a_p^2.

The periodic extension of the rounding interval
[theta+k-1/2,theta+k+1/2) has length one. It intersects at most two supplied
integer unit cells. Each contains at most one orbit of mass at most two.
Consequently M_j<=4 (for Q=1, mean mass one gives M_0=1). This includes wraparound
and ties. Collisions are aggregated, never removed. Moreover

    sum M_j=Q,  sum M_j^2 >= sum m_p^2=(2-s)Q.                        (3)

Let G0 have columns sqrt(m_p)e_{theta+k_p}, and T0=G0G0*. Fourier vectors at
different integer residues modulo Q are orthogonal. Those differing by Q are
collinear, possibly with a unit scalar due to the centered grid. Thus

    ||G0||_op^2=max_j M_j<=4,  diag(T0)=1.                           (4)

No assertion that rounding is injective or preserves the number of simple marks
is needed. The collision cap is specific to the supplied one-cell model.

## 3. Dimension-free RMS operator comparison

Set, with continuous values at A=0,

    U_A=sqrt(2) exp(pi/2) cosh(A/2),
    V_A=sqrt(2) exp(pi/2) sinh(A/2),
    c_A=(cosh(A/2)-1)/A, c_0=0,
    z_A=sinh(A/2)/A, z_0=1/2,
    X_A=pi(U_A+2),
    Y_A=(U_A+2)c_A+V_A z_A,
    R_A=sqrt(X_A^2/4+4Y_A^2).

**Lemma 1.** For every model and every theta above,

    ||T-T0||_F/sqrt(Q)
      <= X_A sqrt(E_ph)+Y_A sqrt(E_dep)
      <= R_A sqrt(4E_ph+E_dep/4).                                  (5)

All constants in this lemma are independent of Q.

Proof. The matrix with columns e_{p+1/2} is unitary. Expand
exp(2*pi*i*(tau_p-1/2)u), cosh(a_p u) and sinh(a_p u) in their absolutely
convergent power series. Multiplication by u has norm at most 1/2,
|tau_p-1/2|<=1/2, max sqrt(m_p)<=sqrt(2). Termwise operator bounds and summation
therefore give ||G||_op<=U_A and ||H||_op<=V_A. This argument works even if
neighboring centers almost collide; it does not invoke a separated-frequency
large-sieve estimate on the finite grid.

Strip depth at the original centers before changing phases. For |u|<=1/2,

    |exp(2*pi*i*e*u)-1|<=pi |e|,
    cosh(a*u)-1<=c_A a, |sinh(a*u)|<=z_A a.

The latter inequalities follow from convexity of cosh(x)-1 and sinh(x) on
[0,A/2], with their values at zero. At A=0, a=0 and the limits are harmless.
Summing squared entries, including the 1/Q in the normalized vectors, gives

    ||G-G0||_F/sqrt(Q)<=pi sqrt(E_ph)+c_A sqrt(E_dep),
    ||H||_F/sqrt(Q)<=z_A sqrt(E_dep).

Use GG*-G0G0*=(G-G0)G*+G0(G-G0)*, (4), and
||HH*||_F<=||H||_op||H||_F. The triangle inequality proves the first bound in
(5). Cauchy-Schwarz applied to (2 sqrt(E_ph), sqrt(E_dep)/2) proves the second.
There is no entrywise-to-matrix dimension factor. QED.

## 4. Every short scale, without an integrality restriction

Let b_j^0 be the coefficients of the rounded real configuration. Since b_0=b_0^0=1,
T-T0 has zero diagonal. Its normalized squared Frobenius norm equals

    2 sum_{j=1}^{Q-1}(1-j/Q)|b_j-b_j^0|^2.

For 0<alpha<=1 and 0<=x<=1,
(alpha-x)_+<=alpha(1-x). Thus the weighted coefficient-error norm at scale alpha
is at most ||T-T0||_F/sqrt(alpha Q). The reverse triangle inequality in this
weighted Euclidean space proves

    |sqrt(L_alpha-1/alpha)-sqrt(L_alpha^0-1/alpha)|
      <= [X_A sqrt(E_ph)+Y_A sqrt(E_dep)]/sqrt(alpha).               (6)

For alpha>1/2 define f_alpha=(2alpha-1)/alpha^2. The rounded integer occupancy
formula, pairing Fourier frequencies j and Q-j, is

    L_alpha^0=1/alpha+sum_{j=1}^{Q-1}F_alpha(j/Q)|Mhat(j)|^2,
    F_alpha(x)=((alpha-x)_++(alpha-1+x)_+)/alpha^2,
    Mhat(j)=Q^(-1)sum_p M_p exp(2*pi*i*p*j/Q).

The coset phase cancels in the squared moduli. F_alpha>=f_alpha, and Parseval
with (3) gives sum_{j!=0}|Mhat(j)|^2=sum M_p^2/Q-1>=1-s. Consequently

    sqrt(f_alpha(1-s)) <= sqrt(L_alpha-1/alpha)
        +[X_A sqrt(E_ph)+Y_A sqrt(E_dep)]/sqrt(alpha).               (7)

This is the new standalone transfer theorem. It uses only a supplied rounding,
not a small-defect hypothesis. It does not yet supply an appropriate theta.

## 5. Precisely the inherited anchor input

The following recapitulates Sections 2-3 of the frozen parent; it is retained
as a proof-candidate dependency, not silently upgraded by being restated.
Put B_*=16/3 and

    C_A=7+(B_*/4)[2cosh A+1+sqrt(4cosh(A)^2-3)].

For s>0, a simple-anchor phase theta can be chosen so that

    4E_ph+E_dep/4 <= eta,
    eta=C_A(pi^2 Q^2+A^2/4) delta/(sQ),  delta>=0.                  (8)

Here is the finite Hilbert-space argument and its connection to (1).
For finitely many repetitions on the long box, let S be the sum of simple unit
atoms, P the positive nonsimple g/double operator, and N_- the negative pair h
operator (each pair's columns have weight sqrt(2)). Write Aop=S+P-N_-,
U=range(P), E=span((I-P_U)f_i), F=(U+E)^perp, and Qop=2P_U+P_E.
If n is the simple count, nu is the nonsimple mass and N=n+nu, set
xi=tr(P_U S), zeta=tr((I-P_U)N_-), zeta_F=tr(P_F N_-). Direct expansion using
tr(P)-tr(N_-)=nu and tr(S)=n gives the exact identity

    D:=n+||Aop||_HS^2-2N
     =||Aop-Qop||_HS^2+2(nu-2dim U)+2xi+2zeta+2zeta_F+(n-dim E).    (9)

Every term is nonnegative: one nonsimple orbit has mass two and contributes
one positive column, so dim U<=nu/2; also dim E<=n. Finite spans suffice.

For completeness the positive-energy extraction is as follows. Each parity
class of supplied integer cells is 1-separated. A q-separated real exponential
family on [-1/2,1/2] has Bessel bound 2+2/(3q^2): majorize the indicator by
2(1-|u|)_+, Fourier transform to 2 sinc(x)^2, and sum row bounds with
sum_{k>=1}1/k^2=pi^2/6. Combining the two parity classes gives B_*.

Let V be simple synthesis, V_E=P_E V, and write its polar factorization
V_E=(V_E V_E*)^(1/2)W with WW*=I_E (zero-rank cases are interpreted on the zero
space). For the simple Gram matrix Gamma, expansion gives

    Gamma-I=Z+B-C,
    Z=W*P_E(Aop-Qop)P_EW,
    B=V*P_U V+W*P_E N_- P_EW >=0, C=I-W*W >=0,
    ||Z||_F^2<=D, tr(B+C)<=D.

Since Gamma<=B_* I, X=Gamma-I has operator norm at most 13/3. Trace pairing
gives ||X||_F^2<=||X||_F sqrt(D)+(13/3)D, hence ||X||_F^2<=7D
(the quadratic is positive at sqrt(7), since 7-sqrt(7)-13/3>0).
This is ordered off-diagonal simple-simple sinc-square energy.

Nonsimple g/h synthesis has squared operator bounds
C_g=2B_*cosh(A/2)^2, C_h=2B_*sinh(A/2)^2, by the same power series argument
on the continuous box. Splitting H into U and its orthogonal complement bounds
its simple cross energy, together with the g energy, by

    (C_g+C_h)xi+B_*zeta+2sqrt(C_h B_* xi zeta).

The largest eigenvalue of this two-variable quadratic form is
(B_*/2)[2cosh A+1+sqrt(4cosh(A)^2-3)]. Since xi+zeta<=D/2, the sum of the
simple-simple and simple-nonsimple positive two-channel energies is <=C_A D.

The correlation of an anchor with a target of real separation d and depth a is

    |sinc(d+i a/(2*pi))|^2
     =[sin(pi*d)^2+sinh(a/2)^2]/[pi^2*d^2+a^2/4].                  (10)

For a nonsimple target its two g/h squared correlations, including mass two,
are exactly the corresponding positive energy. Self simple terms have zero
phase/depth cost and may be omitted. Restrict to anchor-target pairs in the
same period, where |d|<Q. Bound the numerator below by
4 dist(d,Z)^2+a^2/4 and the denominator above by pi^2 Q^2+A^2/4. Divide by the
number of repetitions, use D_M/(MQ)->delta from (1), and average over the sQ
anchors. This proves (8). Discarding other periods is legitimate only in the
positive two-channel energy, not in the original signed complex sum.

## 6. Improved growth condition and explicit budget threshold

Combining (5)-(8) proves, for 1/2<alpha<=1 and s>0,

    sqrt(f_alpha(1-s)) <= sqrt(L_alpha-1/alpha)+R_A sqrt(eta/alpha). (11)

For fixed A and s bounded below, eta=O_A,s(Q delta), and the new error is
O_A,s,alpha(sqrt(Q delta)). The parent's coefficientwise estimate instead was
sqrt(Q)(pi sqrt(eta)+4 k_A eta), k_A=(cosh A-1)/A^2, k_0=1/2.
It required Q^2 delta->0. Equation (11) only requires **Q delta->0**.
This is an asymptotic improvement, not a claim that our conservative constant
is smaller for every finite Q.

In particular, for bounded A, s->2/3, Q delta->0 and u2->0, the hypothesis

    L_(3/4)<=19/12+u2

is impossible: (11) would imply sqrt(8/27)<=1/2. At s=2/3 and exact short
budget, put g=sqrt(8/27)-1/2. The explicit necessary lower bound is

    delta >= d_RMS(Q,A)
      := (3/4)(2/3)Q g^2 / [R_A^2 C_A(pi^2 Q^2+A^2/4)] > 0.       (12)

For a short-budget error u2 with 1/4+u2>=0, replace g by
max(0,sqrt(8/27)-sqrt(1/4+u2)); a positive threshold requires this gap positive.
If also L_1<=4/3+u1, then delta<=u1, so u1<d_RMS rules out both exact budgets
in this model. Neither budget is proved here for actual zeta zeros.

At A=log(2), actual 70-digit evaluations (not interval certificates) give:

| Q | Parent threshold | New threshold | New / parent |
|---|---:|---:|---:|
| 6 | 2.63435533225e-8 | 5.21429905446e-9 | 0.19793 |
| 48 | 4.13776150796e-10 | 6.52004278493e-10 | 1.57574 |
| 96 | 1.03525966141e-10 | 3.26003430733e-10 | 3.14900 |
| 384 | 6.47654439293e-12 | 8.15009585811e-11 | 12.58402 |

The old constant remains better for some small Q. Use the larger of the two
valid lower thresholds, or the smaller comparison error, rather than erasing
that fact. The new threshold scales as Q^(-1), the old one as Q^(-2).
No optimal finite constant is claimed.

## 7. A cyclic-strain obstruction to period-free global phase locking

Let Q=6k, k>=3, h=1/8, all a_p=0, and

    (m_0,...,m_5)=(1,1,1,1,2,0), repeated,
    tau_p=1/2+h sin(2*pi*p/Q).                                    (13)

This satisfies the same mean-one, s=2/3 and supplied-cell assumptions, with no
large depth and no discontinuity at the periodic boundary. Since m is 6-periodic,
its Fourier coefficients at frequencies 1 and 2 vanish when k>=3. Therefore
weighted mean sin=0 and weighted mean sin^2=1/2. In particular

    min_theta (1/Q)sum_p m_p dist(tau_p-theta,Z)^2 = h^2/2=1/128.   (14)

To check the minimization rather than just a trial phase, let d=dist(theta-1/2,Z).
If d<=1/4, all relevant differences have magnitude <=3/8 and no wrapping occurs;
the cost is d^2+h^2/2. If d>=1/4, every distance is at least d-h>=1/8, giving
cost >=1/64>1/128. The minimizer is theta=1/2 modulo one.

For distinct p,q write ell=dist(p-q,QZ), 1<=ell<=Q/2. The cyclic Lipschitz
bound gives |tau_p-tau_q|<=2*pi*h*ell/Q. Thus

dist(t_p-t_q,QZ)>=ell/2 for Q>=18, and the geometric sum yields

    |<e_{t_p},e_{t_q}>|
     = |sin(pi(t_p-t_q))|/[Q|sin(pi(t_p-t_q)/Q)|]
     <= 2*pi^2*h/Q.

The denominator is at least 2 dist(t_p-t_q,QZ)>=ell; the numerator is at most
pi|tau_p-tau_q|. Since all depths vanish, diagonal mark contributions cancel
from delta and (2) gives exactly

    delta=(1/Q)sum_{p!=q}m_p m_q |<e_{t_p},e_{t_q}>|^2
          <=4*pi^4*h^2/Q ->0.                                   (15)

Equations (14)-(15) refute a uniform global-phase estimate E_ph<=C delta.
More generally they refute E_ph<=c(Q)delta with c(Q)=o(Q). Thus order Q cannot
be removed from *this global-phase intermediate estimate*. This does not prove
that the factor Q in the two-scale theorem itself is necessary.

This is NOT a configuration satisfying both target budgets. Here is an analytic
short-scale check, separate from the numerical samples. For real periodic atoms,
positivity of individual sinc squares and the O(ell^(-2)) tail give

    L_alpha=(1/Q)sum_p sum_{ell in Z}m_p m_{p-ell}
      sinc(alpha(ell+tau_p-tau_{p-ell}))^2.

For each fixed ell, tau_p-tau_{p-ell}->0 uniformly as Q->infinity. For ell!=0,
|ell+tau_p-tau_{p-ell}|>=3|ell|/4, giving a summable bound independent of Q.
Dominated convergence reduces the limit to the unstrained period-six word.
Formula (1) for that word, using the exact rational sixth-root cosine values,
gives

    L_(3/4) -> 398/243 = 19/12+53/972 > 19/12.                     (16)

The code recomputes this rational constant; the continuum of Q values and the
phase minimization rely on the arguments above, not on a finite scan.

## 8. Audit and next decisive frontier

An isolated verifier should audit: the rounding cap including modular ties;
the unitary-series synthesis constants; RMS normalization and trace cancellation;
the all-alpha weights and integer occupancy floor; every component of the
inherited signed slack and anchor limit; the threshold algebra; and the cyclic
strain's global minimization, defect bound and dominated-convergence argument.
Candidate and parent hashes must be bound to any receipt. This run supplies no
independent receipt and makes no literature-wide novelty claim.

A-RH-LOC-0012 is the proposed next attempt, not a completed result: for each
fixed A, determine whether the infimum over all Q and s=2/3 of

    max(delta, L_(3/4)-19/12)

is strictly positive in this cell model. A proof would need local phase gauges
or another mechanism that handles cyclic strain and anchor-free holes, without
assuming low variation or exact global phase locking. A counterexample must
satisfy BOTH budgets asymptotically; (13) does not. Actual-zero cell extraction,
weights, localization, exceptional operator energy and arithmetic moment
transfer remain additional, distinct obligations even if that model task closes.
