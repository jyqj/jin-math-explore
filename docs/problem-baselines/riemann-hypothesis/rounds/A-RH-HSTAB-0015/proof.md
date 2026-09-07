# A-RH-HSTAB-0015 — uniform hole stability from central-row energy

Date: 2026-09-07. Status: **proof_candidate; no independent receipt**.
Issue #93. Immediate parent: A-RH-DISP-0014 at
`2f5bc3bf2ad050a363caa4cb08ea81d5679531bf`, proof blob
`5866044343f85fa6574bb18f42162927a5fe5c62`.
The principal result answers that candidate's equation (28) in its stated
periodic model. The mixed-model consequence additionally uses the explicitly
re-derived, unverified round-12 localization and good-block inputs below.
Nothing here identifies these models or their budgets with actual zeta zeros.

## 1. Model and normalization

For an integer Q>=1 choose one supplied orbit in each occupied cell:

    m_p in {0,1,2}, t_p=p+tau_p, 0<=tau_p<1,
    a_p>=0 finite, a_p=0 unless m_p=2.

A mark two is a real double when a_p=0 or a multiplicity-one conjugate pair
at t_p +/- i a_p/(2 pi) otherwise. Define

    rho=Q^(-1)sum m_p, s=Q^(-1)#{p:m_p=1},
    B(v)=sum_p m_p exp(2 pi i t_p v)cosh(a_p v), b_j=B(j/Q)/Q,
    E_alpha=rho^2/alpha+(2/alpha^2)sum_(1<=j<alpha Q)
                              (alpha-j/Q)|b_j|^2,
    delta=s+E_1-2rho.                                           (1)

The quantities are per supplied cell, NOT per zero when rho!=1. An endpoint
j=alpha Q has weight zero. Depths need not be bounded uniformly for the
hole theorem; a common cap A is explicitly needed for the mixed-model bridge.

Let u_j=(j-(Q-1)/2)/Q and v_p(j)=exp(2 pi i t_p u_j)/sqrt(Q).
Give G,H the columns sqrt(m_p)v_p cosh(a_p u), sqrt(m_p)v_p sinh(a_p u).
Then the Hermitian Toeplitz matrix T=GG*-HH* satisfies

    T(j,k)=b_(j-k), diag(T)=rho, ||T||_F^2/Q=E_1.                (2)

Here b_-j=conj(b_j). For d=alpha Q integer, and T_d the first d rows/columns,

    ||T_d||_F^2/(alpha^2 Q)=E_alpha.                            (3)

The power alpha^2 in (3) is essential. Repeating the pattern M times at cell
period Q changes neither E_alpha nor delta: its coefficient at j/(MQ) vanishes
unless M divides j, in which case it is b_(j/M). Consequently rational alpha
can always be handled by repeating the pattern to make alpha Q integer.
Continuity of the finite sum (1) extends results from rational to real alpha.

The same quantity is the fixed-pattern infinite-repetition limit of the
unit-normalized continuous-box signed energy. Indeed that energy is
alpha^(-2) integral (alpha-|v|)_+ |B(v)|^2 |D_M(Qv)|^2 dv, with
D_M(x)=sum_(l=0)^(M-1)exp(2 pi i l x). After periodizing the compactly supported
continuous weight and applying the Fejer approximate identity, division by MQ
gives exactly (1). No uniform finite-M approximation is assumed in this step.

## 2. An exact Toeplitz identity, not a phase-rigidity theorem

**Lemma 1 (central rows).** Let T be any Hermitian Toeplitz Q-by-Q matrix with
constant real diagonal rho. For ceil(Q/2)<=d<=Q put h=Q-d, c=2d-Q and
C={h,...,d-1}. With T_0 empty,

    ||T_d||_F^2 = ||T_h||_F^2 + sum_(i in C)(T^2)_(ii).         (4)

Proof. Put z_k=|b_k|^2 for k>0. The energy of T_n is
n rho^2+2 sum_(k>0)(n-k)_+ z_k. The coefficient of z_k in the sum of the
central full-row norms is 2 min(c,(d-k)_+). The elementary identity
(d-k)_+-(h-k)_+=min(c,(d-k)_+) proves (4), including c=0 and h=0.
The rows on the right are rows of the FULL Q-by-Q matrix, not rows of T_d.

**Lemma 2 (projection perturbation on selected rows).** Suppose T=2Pi+R,
where Pi is any orthogonal projection and R is Hermitian. For any c selected
coordinates C and any D>=||R||_F^2,

    sum_(i in C)(T^2-2T)_(ii)
       >= -[c-(sqrt(c)-sqrt(D))_+^2].                           (5)

Proof. J=2Pi-I satisfies J*=J and J^2=I. Thus
T^2-2T=JR+RJ+R^2. For the coordinate projection P_C, put x=||RP_C||_F.
The trace of R^2 on C is x^2, while
|tr(P_C JR)|=|<JP_C,RP_C>_F|<=sqrt(c)x.
The selected-row trace is therefore at least x^2-2sqrt(c)x, with 0<=x<=sqrt(D).
Its minimum on this interval is exactly the right side of (5).
There is no operator norm, gap, dimension-dependent estimate or sign
assumption on the entries of T in this proof.

In particular, combining (4)-(5) and ||T_h||_F^2>=h rho^2 gives

    ||T_d||_F^2 >= 2rho c+h rho^2
                         -[c-(sqrt(c)-sqrt(D))_+^2].           (6)

This is the main mechanism. Recovering an approximately common phase,
controlling polynomial roots, or approximating a Toeplitz projection by a
circulant matrix is unnecessary for the energy conclusion.

## 3. The uniform saturated-hole theorem

A hole has only marks 0/2. Let r be its occupied-cell count, so rho=2r/Q.
For the G,H of section 1 let U=range(G), u=dim U, Pi=P_U,
zeta=||(I-Pi)H||_F^2. Since tr T=2r and tr(Pi T)=2r+zeta,

    D:=Q delta=||T||_F^2-4r
       =||T-2Pi||_F^2+4(r-u)+4zeta >=0.                        (7)

Every term is nonnegative because G has r nonzero columns. No independence
of the exponential columns, bound on their condition number, or depth cap is
used. This re-derives the parent's anchor-free signed slack directly.

Define for 1/2<=alpha<=1

    w=2alpha-1, f_alpha=w/alpha^2, c_alpha=(1-alpha)/alpha^2,
    mu_w(t)=w-(sqrt(w)-sqrt(t))_+^2, t>=0.

At w=0 take mu_0=0. Equations (3), (6), and (7) prove

    E_alpha >= 2 f_alpha rho+c_alpha rho^2
                               -mu_w(delta)/alpha^2.          (8)

First prove it for integer alpha Q, then use the exact replication and
continuity argument of section 1. This handles Q=1, empty holes, full holes,
colliding-near-boundary centers and nonintegral alpha Q without approximation.
Although the stronger clipped error is useful for finite delta, the simpler
mu_w(t)<=2sqrt(wt) yields, at alpha=3/4,

    E_(3/4) >= (16/9)rho+(4/9)rho^2
                              -(16sqrt(2)/9)sqrt(delta).       (9)

**This supplies the period-uniform modulus requested in parent (28)**. It is
uniform even across finite depth caps A: (9) itself does not contain A. This
is a candidate proof of that restricted-model statement, not independent
verification, not a new theorem about zeta zeros, and not a claim that the
square-root rate is optimal.

The no-simple-mark hypothesis matters. A fully simple real integer lattice
has s=1, rho=1, delta=0 and E_(3/4)=4/3. Applying (9) to it would wrongly
require 20/9. The mixed problem cannot be handled by dropping that hypothesis;
the next sections separate simple-containing and anchor-free blocks.

## 4. From periodic holes to the finite blocks that actually occur

Now assume the MIXED model has mean mass rho=1 and a common finite depth cap A.
Fix any integer L>=2, and partition P=lcm(Q,L) cells into consecutive L-blocks.
All normalizations in this section divide by P. Define

    b_(alpha,A)(L)=cosh(alpha A)^2/L *
                         [8+32(2+log L)/(pi^2 alpha^2)].        (10)

If F_alpha(b) is the continuous-box energy of one FINITE block, the signed
localization estimate is

    |E_alpha-sum_b F_alpha(b)/P|<=b_(alpha,A)(L).               (11)

Here is its proof and sign boundary. The pair kernel is

    K_alpha(d,a,a')=(1/4)sum_(e,f=+/-1)
               sinc(alpha[d-i(e a+f a')/(2pi)])^2.

It is real after summation but need not be nonnegative. Its absolute value
is at most cosh(alpha A)^2 and, for d!=0, at most
cosh(alpha A)^2/(pi^2 alpha^2 d^2). For cell lag j>=2, separation is >=j/2
and a mass product is <=4. The fraction of pairs crossing L-block boundaries
is min(j/L,1). Count both orientations, use the first bound at lag one and
sum j^-1 and j^-2 for the other lags. This gives (10)-(11). The infinite
periodic pair expansion is absolutely convergent; it follows from finite
repetitions by dominated convergence with these same bounds. No favorable
cross-block sign is assumed.

A finite mixed block with mass M_b and simple count n_b has signed slack

    D_b=n_b+F_1(b)-2M_b>=0.                                    (12)

For audit, write its operator Aop=S+P_+-N_-, where S is the simple part.
Set U=range(P_+), E=span((I-P_U)f_i: i simple), F=(U+E)^perp,
Qop=2P_U+P_E; let nu=M_b-n_b, xi=tr(P_U S),
zeta=tr((I-P_U)N_-), zeta_F=tr(P_F N_-). Direct expansion gives

    D_b=||Aop-Qop||_HS^2+2(nu-2dim U)
                   +2xi+2zeta+2zeta_F+n_b-dim E.               (13)

One mass-two orbit contributes one positive column, so dim U<=nu/2;
also dim E<=n_b. This proves (12) on finite spans.
By (11), sum_b D_b/P<=delta+b_(1,A)(L).

Call a block bad when n_b=0. Let beta be its cell fraction, and h its mass
fraction. Periodize EACH bad block with period L and write its own normalized
long defect as delta_b^per. Then (7) and (11) applied to this repeated block give

    0<=delta_b^per<=D_b/L+b_(1,A)(L),
    sum_bad (L/P)delta_b^per<=delta+(1+beta)b_(1,A)(L).           (14)

Thus small average global slack controls the average periodic bad-block
slack, including both localization errors. It is not assumed that every
individual block has a small defect.

Use (8), its simpler square-root error, and (11) for these bad blocks.
Cauchy-Schwarz, both for mass and for the square-root errors, proves

    sum_bad F_alpha(b)/P >= 2f_alpha h+c_alpha h^2/beta
      -K_alpha sqrt(beta[delta+(1+beta)b_(1,A)(L)])
      -beta b_(alpha,A)(L),
    K_alpha=2sqrt(2alpha-1)/alpha^2.                            (15)

If beta=0, h=0 and the entire right side is interpreted as zero. Vacant bad
blocks are included in beta; their zero masses cause no division by zero.
This completes the finite-block/averaging bridge missing from the parent.

## 5. Good blocks: the precise inherited input

The following details identify the dependency on A-RH-LOC-0012 sections 3-4
rather than treating its unverified candidate as a receipt. Put B_*=16/3 and

    C_A=7+(B_*/4)[2cosh A+1+sqrt(4cosh(A)^2-3)],
    eta=C_A(pi^2 L^2+A^2/4)delta.                               (16)

Choose the best simple anchor in each good block. Its nearest-coset rounded
phase errors e_p give costs Z_b=sum_p m_p(4e_p^2+a_p^2/4). Then

    sum_good Z_b/P<=eta.                                       (17)

For completeness, here are the required extraction steps from (13).
Parity coloring of supplied integer cells gives two 1-separated real families.
Majorize the long box by 2(1-|u|)_+; its Fourier transform is 2sinc(x)^2.
Row summation gives Bessel constant 2+2/(3q^2) for a q-separated family,
hence B_* for the two parity classes. For simple synthesis V and Gamma=V*V,
the polar factor W of P_E V gives

    Gamma-I=Z+B-C, ||Z||_HS^2<=D, B,C>=0, tr(B+C)<=D,
    Z=W*P_E(Aop-Qop)P_EW,
    B=V*P_U V+W*P_E N_- P_EW, C=I-W*W.

The coisometry W has WW*=I_E. Since Gamma<=B_*I, trace pairing with Gamma-I
bounds its squared HS norm by its HS norm times sqrt(D), plus (13/3)D.
The positive quadratic root is below sqrt(7D). This bounds the ordered
simple-simple energy by 7D.
Nonsimple g/h synthesis has squared bounds
C_g=2B_*cosh(A/2)^2 and C_h=2B_*sinh(A/2)^2, by norm-convergent depth series.
Splitting H over U and U-perpendicular bounds its simple correlations plus
the g correlations by
(C_g+C_h)xi+B_*zeta+2sqrt(C_h B_*xi zeta).
Its largest two-by-two eigenvalue, together with xi+zeta<=D/2, gives total
positive simple-to-all energy <=C_A D.

The modulus correlation is
[sin(pi d)^2+sinh(a/2)^2]/[pi^2 d^2+a^2/4]. Within a block |d|<L; its numerator
is >=4dist(d,Z)^2+a^2/4. Average over the block's simple anchors, of which
there is at least one, and discard only positive interactions from this
new two-channel energy. Apply to finite P-repetitions and take their limit.
This proves (17), including its per-P normalization. No hole coverage is used.

Let f=f_alpha, c=c_alpha. Define

    U=sqrt(2B_*/alpha)cosh(alpha A/2),
    V=sqrt(2B_*/alpha)sinh(alpha A/2),
    c_d=(cosh(alpha A/2)-1)/A, z_d=sinh(alpha A/2)/A,
    X=pi alpha(U+2/sqrt(alpha)), Y=(U+2/sqrt(alpha))c_d+V z_d,
    R_(alpha,A)=sqrt(X^2/4+4Y^2),
    W_alpha(L)=32[3+log(L+2)]/(pi^2 alpha^2 L),
    I=f[2(1-h)-s]+c L/(L+2)(1-h)^2/(1-beta).                  (18)

At A=0, c_d=0 and z_d=alpha/2. At beta=1, necessarily h=1,s=0; set I=0.
The good-block lower bound is

    sum_good F_alpha(b)/P >=
                [sqrt((I-W_alpha(L))_+)-R_(alpha,A)sqrt(eta)]_+^2. (19)

Here are the finite-boundary details. Nearest-coset rounding aggregates at
most two original cells at a site, so its mass is <=4. It fits in L+2
integer sites and can only increase squared masses. On the normalized
alpha-box, the original g/h synthesis norms are <=U,V, and rounded synthesis
norm is <=2/sqrt(alpha). Removing depth before changing phase, the column
bounds pi alpha|e|, c_d a and z_d a give an HS operator error <=R sqrt(Z_b).
Direct-sum triangle inequality gives the square-root error in (19).
Periodizing real occupancy in L+2 sites and applying the sinc-square Fourier
symbol gives f sum m^2+c M_b^2/(L+2). The extra periodic real interactions are
nonnegative and at most 32[3+log(L+2)]/(pi^2 alpha^2) per block: count external
lags with mass products <=16 and at most min(j,L+2) pairs per orientation.
Summing and using Cauchy-Schwarz for good-block masses gives exactly I-W.
This derivation keeps collisions, boundary terms and both positive parts.

## 6. Closing the mixed-model gap without coverage or depth dispersion

Since each cell has mass <=2, 1-h<=2(1-beta). Therefore 0<=I<=2/alpha.
For any I,W,z>=0,

    [sqrt((I-W)_+)-z]_+^2 >= I-W-2z sqrt(I).

Combine this with (15), (19) and the global signed localization (11).
Cauchy-Schwarz also gives

    (1-h)^2/(1-beta)+h^2/beta >=1,

with the zero-mass endpoint conventions already stated. The factor L/(L+2)
in I is <=1, so the sum of the two constant-mode terms is at least
c L/(L+2). We obtain, for every L>=2,

    E_alpha >= f_alpha(2-s)+c_alpha - Err_(alpha,A)(L,delta),    (20)

where the entirely explicit, period-independent error is

    Err=2c_alpha/(L+2)+W_alpha(L)
      +2R_(alpha,A)sqrt(2 C_A(pi^2 L^2+A^2/4)delta/alpha)
      +K_alpha sqrt(delta+2b_(1,A)(L))+2b_(alpha,A)(L).          (21)

This is a finite theorem for every Q and every allowed mean-one configuration.
It assumes neither a bound on hole mass H nor a small local depth variance
Omega nor Q*delta->0, nor a common phase. A common finite depth cap A and the
supplied one-orbit-per-unit-cell representation remain hypotheses.

For a sequence with fixed A, arbitrary periods, s_n->2/3 and delta_n->0,
first fix L in (20); take liminf in n, and then let L->infinity. Every error
term vanishes in this order. Equivalently, for 0<delta<=1/8 take
L=ceil(delta^(-1/3)); (21) is O_(alpha,A)(delta^(1/6)sqrt(log(2/delta))).
At delta=0 let L->infinity directly. In particular,

    liminf E_(3/4) >=44/27=19/12+5/108.                        (22)

Thus the period-free two-budget problem for this BOUNDED-DEPTH CELL MODEL has
a candidate resolution. This is a model result, not a proof that zeta zeros
admit this representation, not a new unconditional zero proportion, and not RH.
The rate in (21) is deliberately conservative, not claimed optimal.

## 7. An exact positive finite tolerance

For A<=log 2, take L=2^24. At alpha=3/4 the following majorants hold:

    C_A<15, R_(alpha,A)<10, K_alpha<3,
    eta<=151 L^2 delta, 2R sqrt(2eta/alpha)<420L sqrt(delta).

They use 3<pi<22/7, log 2<1, cosh(A)<=5/4,
cosh(alpha A/2)<9/8, sinh(alpha A/2)<3/8,
sqrt(2B_*/alpha)<4 and 2/sqrt(alpha)<12/5. Specifically,
X<(22/7)(3/4)(9/2+12/5),
Y<(9/2+12/5)(9/64)+(3/2)(27/64); these give R^2<100 by rational arithmetic.
Also C_A<43/3<15 and (8/3)151<21^2. Limits at A=0 are harmless.

Use log L<24, log(L+2)<25 and pi^2>9 to define rational upper bounds

    B1=25/(16L)[8+(32/9)26],
    Ba=25/(16L)[8+(512/81)26], Wb=(512/81)28/L.

For 0<=delta<=10^-24 the checker verifies EXACTLY

    420L/10^12<1/100,
    10^-24+2B1<1/40000,
    8/[9(L+2)]+Wb+2Ba<1/1000.

Hence Err<1/100+3/200+1/1000=13/500. The remaining gap is

    5/108-13/500=137/6750>0.                                   (23)

For example, the stipulated budgets E_1<=4/3 and E_(3/4)<=19/12 would then
force s>2/3+10^-24: otherwise 0<=delta=s+E_1-2<=10^-24, while (20)-(23) give
a short excess of at least 137/6750-(8/9)10^-24>0, a contradiction.
This minute coefficient is merely an explicit, nonoptimized MODEL certificate.
It must not be reported as an actual zeta-zero proportion. The 2^24 value is
a partition scale in a scalar inequality, not a matrix size that was simulated.
The separate binary64 evaluation of (21) is not an interval certificate.

## 8. Audit, tests, and remaining source task

The standalone hole proof (4)-(9) is independent of the old exact equality
classification and requires no phase or depth-covariance theorem. It should be
audited first; the full mixed claim additionally requires the finite-boundary,
signed-slack and good-block proofs in sections 4-6. A failure in those inputs
need not invalidate the standalone hole lemma. All claims remain candidates.

The checker records 153,272 integer coefficient identities (Q<=96), eight
rational certificate comparisons, abstract projection-row tests, arbitrary-phase
hole models including large depths, exact pattern replication, finite signed
block budgets and mixed-model bounds. Quadrature is a separate numerical
implementation, not interval arithmetic. The conservative assembled bound is
vacuous on the small random mixed cases; its nonvacuous finite tolerance is
established by the analytic majorants and rational comparisons in section 7.
No random/finite test covers the universal mathematical quantifiers.

Next proposed task A-RH-SOURCE-0016: formulate and test an explicit source-to-cell
approximation with an operator-energy residual and depth-tail control. Neither
cell assignment, multiplicity reduction to 0/1/2, finite depth cap, nor the two
normalized rectangular budgets is established for actual zeta zeros here.
The standalone depth-uniform hole modulus does not make mixed localization
uniform as A grows: b_(alpha,A) grows exponentially. Generalizing that source
interface is now a distinct problem, not an excuse to reinsert solved model
assumptions. No automatic import of smooth optimized source profiles is valid.
Independent review must bind the candidate and the named parent dependencies;
same-run re-derivation and mechanical CI are not independent verification.
