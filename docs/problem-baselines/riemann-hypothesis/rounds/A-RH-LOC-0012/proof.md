# A-RH-LOC-0012: local gauges with an explicit anchor-free mass charge

Status: **proof_candidate**, not independently verified. Issue #75.
This continues A-RH-RMS-0011 at commit
`215e35afba58d1a80b0783a41fa4651c6841afba`, proof blob
`fe0e14d28ddf5116a8ddef690b7718652dbe92df`.
It removes the parent condition involving the global period only under a new,
explicit local-coverage hypothesis. The unrestricted period-free problem and
all transfers to actual zeta zeros remain open in this package.

## 1. Model, energy and block data

Fix an integer period Q>=1 and periodically extend

    m_p in {0,1,2}, sum_{p=0}^{Q-1}m_p=Q,
    t_p=p+tau_p, 0<=tau_p<1,
    0<=a_p<=A<infinity, a_p=0 when m_p!=2.

Mark one is a simple real atom; mark two is a real double when a_p=0, or the
conjugate pair t_p +/- i a_p/(2*pi), with multiplicity one per member otherwise.
Let s=#{p:m_p=1}/Q. For 0<alpha<=1 define

    B(v)=sum_{p=0}^{Q-1}m_p exp(2*pi*i*t_p*v)cosh(a_p*v),
    L_alpha=1/alpha+(2/alpha^2)sum_{1<=j<alpha Q}
                      (alpha-j/Q)|B(j/Q)/Q|^2,
    delta=s+L_1-2 >=0.                                         (1)

The nonnegativity is the finite signed Hilbert inequality below, followed by
the fixed-pattern repetition limit. The zero mode in (1) is exactly 1/alpha.
The expression is unchanged by replacing Q with an integer multiple period.
This follows either from geometric-sum cancellation in B or the repetition limit.

Choose ANY integer L>=2 and integer starting shift c. Work in the superperiod
P=lcm(Q,L), partitioned into P/L blocks of L consecutive supplied cells. No
assumption L divides the original Q is needed. A block is good when it contains
at least one simple atom, and bad otherwise. Define

    h = (mass in bad blocks)/P,
    beta = (number of bad blocks)/(P/L),
    k_* = minimum simple count in a good block.

Set k_*=L when every block is bad. Vacant bad blocks count in beta, not in h.
Always 0<=h<=1-s, beta>=h/2, and 1-beta>=s. These are cell/mass counts, not
hypotheses about the distribution of actual zeta zeros.

For each good block choose, among its simple atoms, an anchor phase theta_b
minimizing its total cost. Round t_p to theta_b+k_p with
k_p=floor(t_p-theta_b+1/2), and e_p=t_p-theta_b-k_p. Its cost is

    Z_b=sum_{p in b}m_p(4e_p^2+a_p^2/4).

Different blocks have different phases; there is no global matching assertion.

## 2. Signed cross-boundary localization

Let sinc(z)=sin(pi z)/(pi z), continuously extended at zero. The finite signed
energy of any block b on the unit-normalized alpha-box is

    E_alpha(b)=sum_{p,q in b}m_p m_q K_alpha(t_p-t_q,a_p,a_q),

    K_alpha(d,a,b)=(1/4)sum_{epsilon,epsilon' in {-1,1}}
       sinc(alpha[d-i(epsilon a+epsilon' b)/(2*pi)])^2.           (2)

The sign-conjugate sum is real; its summands need NOT be positive. Equivalently,
K_alpha is the integral of exp(2*pi*i*d*v)cosh(av)cosh(bv) against the
probability weight (alpha-|v|)_+/alpha^2. The latter representation gives
|K_alpha|<=cosh(alpha A)^2. If d!=0, the complex sine formula also gives

    |K_alpha(d,a,b)|<=cosh(alpha A)^2/(pi^2 alpha^2 d^2).          (3)

Indeed the imaginary displacement in (2) is at most A/pi and
|sin(pi alpha(d+iy))|^2<=cosh(pi alpha y)^2. No sign is discarded here.

The same fixed-period limit that gives (1) gives the absolutely convergent
pair expansion

    L_alpha=(1/P)sum_{p=c}^{c+P-1}sum_{q in Z}
                  m_p m_q K_alpha(t_p-t_q,a_p,a_q).

For cell lag r>=2, |t_{p+r}-t_p|>=r-1>=r/2 and m_p m_{p+r}<=4, so the
absolute summand is at most 16 cosh(alpha A)^2/(pi^2 alpha^2 r^2).
For r=1 use 4 cosh(alpha A)^2. For every r>0 the fraction of p whose
p and p+r lie in distinct L-blocks is exactly min(r/L,1). Count both signs,
use sum_{r=2}^L 1/r<=1+log L and sum_{r>L}r^-2<=1/L, to obtain

    |L_alpha - (1/P)sum_b E_alpha(b)| <= B_{alpha,A}(L),
    B_{alpha,A}(L)=cosh(alpha A)^2/L *
                     [8+32(2+log L)/(pi^2 alpha^2)].             (4)

This is uniform in Q and the phases/depths. It controls signed cross-block
terms rather than incorrectly assuming their positivity. The periodic pair
expansion follows directly by expanding the energy of M repetitions: weights
of any fixed cell lag converge to one, and (3) gives a summable tail independent
of M. This also justifies the interchange used here.

## 3. The retained signed-defect input

We explicitly identify the input inherited from the parent's section 5. On the
long box, for any finite repeated family let S be the simple positive operator,
P_+ the nonsimple positive g/double operator, N_- the negative pair h operator,
and Aop=S+P_+-N_-. Each nonsimple orbit contributes mass two and one positive
column; g/h columns for pairs carry sqrt(2). Let U=range(P_+),
E=span((I-P_U)f_i : i simple), F=(U+E)^perp and Qop=2P_U+P_E.
With n simple count, nu nonsimple mass, N=n+nu,
xi=tr(P_U S), zeta=tr((I-P_U)N_-), zeta_F=tr(P_F N_-), expansion gives

    D=n+||Aop||_HS^2-2N
     =||Aop-Qop||_HS^2+2(nu-2dim U)+2xi+2zeta+2zeta_F+n-dim E.   (5)

Every term is nonnegative: dim U<=nu/2 and dim E<=n. This uses only finite
spans and tr(P_+)-tr(N_-)=nu. The same identity applies on an alpha-box, since
its real atoms have norm one and each pair satisfies ||g||^2-||h||^2=1.
In particular, every bad block, including a vacant block, satisfies

    E_alpha(b)>=2 sum_{p in b}m_p.                               (6)

For reference, the positive anchor energy estimate derived from (5) is

    T_simple <= C_A D,
    C_A=7+(B_*/4)[2cosh A+1+sqrt(4cosh(A)^2-3)], B_*=16/3.        (7)

T_simple consists of ordered off-diagonal simple-simple sinc squares and both
positive simple-to-g/h squared correlations for nonsimple targets, with their
mass weights. It is NOT the original signed sum in (2).

Here are the details of the extraction, so the dependency can be audited.
Each parity class of occupied supplied cells is 1-separated. Majorizing the
long box by 2(1-|u|)_+ gives Bessel bound 2+2/(3q^2) for a q-separated real
family, by Fourier transformation and the row sum of 1/(qk)^2. The two parity
classes yield B_*. For simple synthesis V, polar factorization of P_E V gives
Gamma-I=Z+B-C, with ||Z||_HS^2<=D, B,C positive and tr(B+C)<=D:

    P_E V=(P_E VV*P_E)^(1/2)W, WW*=I_E,
    Z=W*P_E(Aop-Qop)P_EW,
    B=V*P_U V+W*P_E N_- P_EW, C=I-W*W.

Trace pairing with Gamma-I, whose operator norm is at most 13/3, gives
||Gamma-I||_HS^2<=||Gamma-I||_HS sqrt(D)+(13/3)D<=7D after solving the
quadratic inequality. Nonsimple synthesis has squared bounds
C_g=2B_*cosh(A/2)^2 and C_h=2B_*sinh(A/2)^2. Splitting h synthesis over U
and its orthogonal complement bounds its simple correlations plus the g
correlations by

    (C_g+C_h)xi+B_*zeta+2sqrt(C_h B_* xi zeta).

Since xi+zeta<=D/2, its largest two-by-two eigenvalue gives (7).
Zero-dimensional spaces are interpreted on their support. This is a solver
re-derivation of a frozen proof-candidate input, not a new independent receipt.

For an anchor-target separation d and target depth a, the positive correlation is

    |sinc(d+i a/(2*pi))|^2
       =[sin(pi d)^2+sinh(a/2)^2]/[pi^2 d^2+a^2/4].               (8)

Within one block |d|<L. Its numerator is at least
4 dist(d,Z)^2+a^2/4. Average over all anchors in that block, choose the best,
and sum over blocks. The discarded interactions are positive terms of (7).
Apply (7) to M superperiod repetitions and let M tend to infinity, using
D_M/(MP)->delta. It follows that

    (1/P)sum_{good b}Z_b <= eta_L,
    eta_L=C_A(pi^2 L^2+A^2/4)delta/k_*.                          (9)

For an entirely bad partition the left side is zero and (9) is vacuous.
The gain is that L replaces Q; no alignment between block phases is used.

## 4. Finite local RMS transfer and the integer boundary charge

Fix 1/2<alpha<=1. In a good block, let A_b and A_b^0 be respectively its
original signed alpha-box operator and its rounded, zero-depth real operator.
Nearest-coset rounding fits in K=L+2 consecutive integer sites. Each rounded
site receives at most two original cells, hence aggregate mass at most four.
Let M_j denote these nonnegative integer masses and mu_b=sum M_j. Then

    sum M_j^2>=sum_{p in b}m_p^2.                                (10)

On the normalized alpha-box, real cell synthesis has squared norm <=B_*/alpha
by restriction from the long box. Rounded lattice synthesis has squared norm
<=4/alpha. Set

    U=sqrt(2B_*/alpha)cosh(alpha A/2),
    V=sqrt(2B_*/alpha)sinh(alpha A/2),
    c=(cosh(alpha A/2)-1)/A, z=sinh(alpha A/2)/A,
    X=pi alpha(U+2/sqrt(alpha)),
    Y=(U+2/sqrt(alpha))c+Vz,
    R_{alpha,A}=sqrt(X^2/4+4Y^2),

with c=0,z=alpha/2 at A=0. Absolutely convergent depth power series prove the
bounds U,V. Remove depth before changing phase, and use

    |exp(2*pi*i*e*u)-1|<=pi alpha|e|,
    cosh(au)-1<=c a, |sinh(au)|<=z a  (|u|<=alpha/2).

From A_b=GG*-HH* and A_b^0=G0G0*, the Hilbert-Schmidt triangle inequality gives

    ||A_b-A_b^0||_HS <= X sqrt(sum m_p e_p^2)+Y sqrt(sum m_p a_p^2)
                     <=R_{alpha,A} sqrt(Z_b).

Taking the direct sum over good blocks proves

    |sqrt(sum_good E_alpha(b)/P)-sqrt(sum_good E_alpha^0(b)/P)|
                                  <= R_{alpha,A} sqrt(eta_L).    (11)

These are genuine continuous-box operators, not a quadrature assumption.

For finite real lattice occupancy M supported on K sites, periodize its sinc
energy with period K. The discrete symbol is

    F_alpha(x)=[(alpha-x)_++(alpha-1+x)_+]/alpha^2,
    f_alpha=(2alpha-1)/alpha^2, c_alpha=1/alpha-f_alpha.

For the zero frequency use F_alpha(0)=1/alpha. Poisson summation (equivalently
Fourier transforming sinc(alpha x)^2 to (alpha-|v|)_+/alpha^2), finite DFT
and Parseval give a periodized energy at least

    f_alpha sum M_j^2 + c_alpha mu_b^2/K.

Finite energy is smaller because periodization adds nonnegative real sinc
squares. The added energy is at most

    32/(pi^2 alpha^2)[H_{K-1}+K/(K-1)]
       <=32(3+log K)/(pi^2 alpha^2).                             (12)

To see every factor, for an external positive integer lag d the number of
ordered site pairs is min(d,K); each mass product is <=16. Sum both lag signs
with sinc(alpha d)^2<=1/(pi^2 alpha^2 d^2). There is no zero-lag external pair.
Thus (12) is an explicit finite-boundary correction, not a circular use of an
infinite-volume floor for a finite block.

All simple atoms are in good blocks, so sum_good m_p^2=P[2(1-h)-s].
Cauchy-Schwarz over (1-beta)P/L good blocks yields, when beta<1,

    sum_good E_alpha^0(b)/P >= I_alpha(L,h,beta,s)-W_alpha(L),
    I_alpha=f_alpha[2(1-h)-s]
             +c_alpha L/(L+2) (1-h)^2/(1-beta),
    W_alpha(L)=32[3+log(L+2)]/(pi^2 alpha^2 L).                   (13)

Set I_alpha=0 when beta=1 (then s=0,h=1).

## 5. The finite local-gauge ledger

Combining (4), (6), (11), and (13) proves the central candidate theorem:

    L_alpha >= 2h +
      [sqrt((I_alpha-W_alpha(L))_+) - R_{alpha,A}sqrt(eta_L)]_+^2
      - B_{alpha,A}(L).                                        (14)

This holds for every Q, every integer L>=2, every partition shift, all allowed
phases/depths and 1/2<alpha<=1. The two positive-part operations are essential.
Neither Q delta nor Q^2 delta appears. The price is an explicit h,beta charge;
it must not be silently set to zero. All constants are computable. They are
conservative and this package makes no finite-constant optimality claim.

## 6. Period-independent consequence, with exact limit order

Consider ANY sequence of such models with arbitrary periods Q_n, a common
finite depth cap A, s_n->2/3 and delta_n->0. For each L use the fixed starting
shift zero in the lcm(Q_n,L) superperiod, and define h_{n,L} as above. Put

    H=liminf_{L->infinity} limsup_{n->infinity} h_{n,L}.           (15)

Then 0<=H<=1/3. At alpha=3/4 the following consequence of (14) is

    liminf_n L_(3/4,n) >= F(H),
    F(H)=32/27+2H/9+(4/9)(1-H)^2/(1-H/2).                      (16)

Proof of the limits: fix L FIRST. Then eta_L->0 since k_*>=1. Use beta>=h/2
and c_alpha>=0 to lower-bound I_alpha by replacing beta with h/2. Replacing
L/(L+2) by one loses at most 2c_alpha/(L+2), because
(1-h)^2/(1-h/2)<=1. The positive-part term in (14) is at least I-W in the
zero-eta limit, and all involved quantities are uniformly bounded. The limiting
scalar F is decreasing on [0,1/3], as

    F'(h)=-2(3h^2-12h+8)/[9(h-2)^2] <0.

Take liminf in n, then a sequence of L tending to infinity that realizes
(15). The explicit B,W and the length correction vanish. This proves (16).
It does not interchange the limits or assume one uniform period.

The exact gap above the targeted short budget is

    F(H)-19/12 = (72H^2-101H+10)/[108(2-H)].                     (17)

Consequently the two short/long limiting budgets are incompatible whenever

    H < H_*=(101-sqrt(7321))/144
            =0.10720248331577142649... .                         (18)

The decimal is a 70-digit evaluation, not an interval certificate; (18) is the
exact threshold expression. H is mass divided by TOTAL mass, not a fraction
of only nonsimple mass. For H<=1/10, the gap is at least 31/10260. For H=0,
(16) gives 44/27=19/12+5/108, restoring the full ideal gap without a period
constraint. The threshold is sufficient, not an asserted sharp transition.

In particular, if some fixed R ensures every R consecutive cells contain a
simple atom throughout a sequence, H=0: take L>=R. No low-variation assumption
is needed. More generally, vanishing anchor-free mass in the precise sense
(15) suffices. Neither hypothesis is supplied for actual zeta zeros here.

## 7. Strict gain over the previous cyclic-strain obstruction

Take Q a multiple of 36, marks (1,1,1,1,2,0) repeated, all a_p=0 and

    tau_p=1/2+(1/8)sin(2*pi*p/Q).

The parent proved the optimal global phase variance equals 1/128 and
0<=delta<=pi^4/(16Q). In fact this family satisfies

    Q delta >=1/96.                                            (19)

For p/Q in [1/6,1/3) and q/Q in [2/3,5/6), the phase difference lies in
[sqrt(3)/8,1/4]. Its sine squared is >=3/16 using sin(pi x)>=2x on [0,1/2].
The finite geometric-sum inner product has squared modulus
sin(pi(t_p-t_q))^2/[Q^2 sin(pi(t_p-t_q)/Q)^2], at least 3/(16Q^2).
Each of the two intervals has total marked mass Q/6, exactly, since Q/6 is
multiple of six. Count both orientations in the parent's exact real defect
identity to get (19). Thus Q delta does NOT tend to zero: the preceding
round's sufficient condition genuinely does not cover this family.

But every three consecutive cells contain a simple atom, hence H=0. The new
local theorem does cover it. Its actual short limit remains 398/243>44/27;
this is compatible with the new lower bound, not an escape from both budgets.
No new claim of novelty for the slow-strain idea is made.

## 8. Why the unrestricted question remains open

The coverage charge cannot be inferred small from delta alone. For Q=6k,
put 4k simple marks, then k vacancies, then k double/pair marks, all phases 1/2.
Give every pair fixed depth log(2). Then s=2/3 and

    delta ->0,   for every fixed L: h_{k,L}->1/3,
    L_(3/4)->16/9=19/12+7/36.                                   (20)

Here is a proof of the asymptotics, not numerical extrapolation. Within a
homogeneous run of ell cells and mark m, the finite energy is
m^2 alpha^-2 integral (alpha-|v|)_+ cosh(a v)^2 |D_ell(v)|^2 dv.
Its periodized weight at zero is alpha. Its Lipschitz constant is bounded
by 2[cosh(alpha A)^2+2alpha A cosh(alpha A)sinh(alpha A)]. The Dirichlet first
moment is <=1/4+(log ell)/2, so the run energy is m^2 ell/alpha+O_A,alpha(log ell).
Inter-run interactions are O_A,alpha(log Q): repeat the counting in section 2
with three interfaces and minimum run length k. Thus (20) follows from
(4k+4k)/(6k alpha)=4/(3alpha). Only O(L) mass near interfaces affects h at fixed L.
This is a genuine model obstruction to deriving coverage, NOT a two-budget
counterexample: its short energy is too large.

A further exact relaxed obstruction identifies what the next method must add.
Even supplementing (6) with the asymptotic block zero-mode lower bound does
not close the hole branch by scalar algebra alone. At s=2/3, h=1/3, beta=2/9,
the relaxed short floor is

    (8/9)[2(1-h)-s]+(4/9)(1-h)^2/(1-beta)
       +max(2h,h^2/((3/4)beta)) =286/189 <19/12,                 (21)

with difference 53/756. The mass/cell constraints allow this scalar point.
It is NOT asserted to come from an actual near-extremal exponential family.
Thus these necessary scalar inequalities alone cannot exclude every residual
case. Stronger information about anchor-free blocks, not another global-phase
argument or only a second zero-mode inequality, is required.

## 9. Handoff

New analytic claims remain proof candidates. Audit (2)-(4) for complex signs,
(5)-(9) for inherited positive-energy scope, (10)-(13) for collisions and finite
boundary terms, and (14)-(18) for clipping and limit order. Check (19)-(21) as
three DIFFERENT scope statements. Numerical tests are finite regressions.

Next proposed task A-RH-HOLE-0013: derive a stronger short-energy constraint for
anchor-free near-zero-defect blocks, or construct an actual exponential family
approaching the relaxed point (21). The unrestricted infimum of
max(delta,L_(3/4)-19/12) over all Q, s=2/3 at fixed A is still unresolved.
Even a solution of that model task would leave the zeta cell representation,
source weights/localization, discarded operator energy and arithmetic moment
transfer as separate obligations. No RH result, unconditional zero proportion,
independent receipt or mathematical-authority promotion is claimed.
