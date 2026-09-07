# A-RH-CONGEST-0018: direct sampling instead of cell matching

Date: 2026-09-07. Issue #114. **Solver proof candidate; no independent receipt.**
Historical parent: A-RH-MATCH-0017 at `3be6e0543aee9f26180a90a6ceac5ca288c3bd51`.
The mathematical pivot is to bypass its supplied-cell/deletion interface, not
claim that the minimum matching cost is small. The source consequence below
is WEAKER than Lamzouri's already stated 0.6725007... result [L, Theorem 1.1].
It is a test of a new repository route, not a new best proportion or an RH proof.
References and pinned predecessors are in [source-scope.md](source-scope.md).

## 1. Arbitrary orbits, arbitrary multiplicities, independent matrix dimension

Let a finite conjugation-invariant multiset have total mass N>0 and n simple
real elements. Combine repetitions at the same complex point BEFORE deciding
which elements are simple. A real orbit has integer mass m>=1 and depth a=0;
a nonreal orbit has even total mass m>=2, center t, and members
`t +/- i a/(2 pi)` with mass m/2 each. The centers may be arbitrarily crowded.
No mass clipping, distinct-cell indexing, depth cap or independence of vectors
is assumed. Let q>=1 be an independently chosen matrix dimension.

Set u_j=(j-(q-1)/2)/q and v_t(j)=exp(2 pi i t u_j)/sqrt(q). For simple real
orbits form the columns V=v_t. For the NONSIMPLE orbits form columns
`sqrt(m) v_t cosh(a u)` and `sqrt(m) v_t sinh(a u)` of G and H. Write

    S=VV*, P=GG*, B=HH*, T=S+P-B,
    rho=N/q, s=n/q, delta=(n+||T||_F^2-2N)/q.                 (1)

T is Hermitian Toeplitz, with diagonal rho; S has diagonal s. In particular
q is NOT a spatial cell count, and rho need not be one or at most two.
The nonsimple positive part has at most (N-n)/2 columns, irrespective of how
large its multiplicities are. Each orbit contributes its full original mass
to tr(T), because cosh(a u)^2-sinh(a u)^2=1 pointwise.

For an integer d between ceil(q/2) and q, put alpha=d/q, w=2alpha-1, and
let T_d be the leading d-by-d principal block. Define the sampled per-dimension
energy and the sampled per-mass moment by

    E_alpha^(q)=||T_d||_F^2/(alpha^2 q),
    M_alpha^(q)=E_alpha^(q)/rho=||T_d||_F^2/(alpha^2 N).         (2)

Only these integer dimensions are used; no irrational-alpha replication of
the SOURCE list will be needed. The two source scales 1 and 3/4 are handled
by taking q divisible by four.

## 2. Signed slack, re-derived without geometry

Let U=range(G), E=range((I-P_U)V), F=(U+E)^perp, and denote their projections
by P_U,P_E,P_F. Put r=dim U, e=dim E, nu=N-n, and

    Q0=2P_U+P_E, R=T-Q0, J=Q0-I,
    xi=tr(P_U S), zeta=tr((I-P_U)B), zeta_F=tr(P_F B).

Direct trace expansion gives the exact identity

    D:=q delta=n+||T||_F^2-2N
      =||R||_F^2+2(nu-2r)+2xi+2zeta+2zeta_F+n-e.             (3)

For clarity, tr(P_U T)=nu+xi+zeta, while
tr(P_E T)=n-xi-zeta+zeta_F. Substitute these into
`||T-Q0||_F^2=||T||_F^2-2tr(TQ0)+4r+e` to obtain (3).
Since r<=nu/2 and e<=n, every term on the right is nonnegative. Thus

    delta>=0, and ||R||_F^2+2xi<=D.                            (4)

These elementary signed-slack ideas occur in earlier rounds and are compatible
with the Hilbert-space setup in [L, Proposition 2.1]. Here (3) is proved directly;
no earlier mathematical receipt, column condition number or Bessel bound is used.

## 3. The mixed selected-row lemma

The missing simple-sector charge can be handled directly instead of extracting
separated simple atoms or rounding to cells.

**Lemma.** For any coordinate projection C of rank c,

    tr C(T^2-2T+S) >= -sqrt((4c+2n)D).                         (5)

Proof. Write V_U=P_U V and V_E=P_E V. All columns of V lie in U+E, so

    S-P_E = P_U S P_U + P_E R P_E + P_E B P_E
                                 + V_U V_E* + V_E V_U*.

Indeed compression of T=S+P-B to E gives `P_E R P_E=P_E S P_E-P_E B P_E-P_E`.
Also `Q0^2-2Q0=-P_E`. Therefore there is the exact expansion

    tr C(T^2-2T+S)
      = tr(K_C R)+tr C(R^2+P_U S P_U+P_E B P_E)
                                      +2 Re tr(C V_U V_E*),
    K_C=CJ+JC+P_E C P_E.                                     (6)

The middle trace is nonnegative. On the orthogonal decomposition U+E+F, J
has scalar blocks 1,0,-1. Each block of K_C is the corresponding block of C
multiplied by one of 2,1,0,-1,-2; the E,E multiplier is 1. Thus

    ||K_C||_F <= 2||C||_F=2sqrt(c).

This is a Frobenius block calculation, not a claim about the operator norm of
a general Schur multiplier. The last trace in (6) has absolute value at most
`2||V_U||_F ||V_E||_F <= 2sqrt(n xi)`, because C is a contraction and
`||V_E||_F^2=n-xi<=n`. Cauchy-Schwarz and (4) now give

    2sqrt(c)||R||_F+2sqrt(n xi)
        <=sqrt(4c+2n) sqrt(||R||_F^2+2xi) <=sqrt((4c+2n)D).

This proves (5), including zero-dimensional sectors and c=0. The simple
vectors need not be mutually orthogonal. No uniform synthesis bound is used.

## 4. A mixed Toeplitz floor without cells, clipping or depth truncation

For a Hermitian Toeplitz matrix with diagonal rho, let h=q-d and choose the
central coordinates C={h,...,d-1}, so c=2d-q. Exact diagonal counting gives

    ||T_d||_F^2-||T_h||_F^2 = tr C T^2.                        (7)

If z_k is the squared modulus of its k-th Toeplitz coefficient, its coefficient
on the left is `2[(d-k)_+-(h-k)_+]`; on the right it counts both orientations
of distance k from the central FULL rows. They agree. Diagonal coefficients
are c, and T_0 is empty. This is the central-row identity used in round 15,
not a newly claimed identity about Toeplitz matrices.

Since `tr CT=c rho`, `tr CS=c s` and `||T_h||_F^2>=h rho^2`, (5)-(7) prove

    E_alpha^(q) >= f_alpha(2rho-s)+c_alpha rho^2
                           -sqrt((4w+2s)delta)/alpha^2,
    f_alpha=(2alpha-1)/alpha^2, c_alpha=(1-alpha)/alpha^2.        (8)

In per-mass notation, let sigma=n/N and d0=sigma+M_1^(q)-2=delta/rho. Then

    M_alpha^(q) >= f_alpha(2-sigma)+c_alpha rho
                          -sqrt((4w/rho+2sigma)d0)/alpha^2.    (9)

The result requires alpha q integer, not a spatial period or a mean-one source.
All original multiplicities and finite depths are retained. At n=0, this
recovers the simple square-root version of the earlier hole bound. An all-simple
integer lattice with N=q has T=S=I and delta=0; (8) yields E_(3/4)>=4/3,
correctly avoiding the false hole-only value 20/9. With rho=1 and s->2/3,
delta->0, (8) gives 44/27 directly, without the earlier block-localization chain.

This is a genuine change of the geometric interface: (8) works even when many
orbits lie in one physical unit interval. It does NOT show that a low-cost
matching exists, nor that a source's discrete energy equals its continuous energy.
That separate issue is addressed next.

## 5. Exact sampling dictionary and an explicit alias bound

For any complex difference z define the entire sampled kernel

    K_(q,alpha)(z) = [sin(pi alpha z)/(alpha q sin(pi z/q))]^2, (10)

with removable values understood when d=alpha q is an integer. A finite
geometric sum and conjugation reindexing give

    M_alpha^(q) = N^(-1) sum_(z_i,z_j) K_(q,alpha)(z_i-z_j),
    M_alpha^cont = N^(-1) sum_(z_i,z_j) sinc(alpha(z_i-z_j))^2. (11)

Both lists count multiplicity. These are COMPLEX squares, not a termwise
absolute-square replacement. The full sums are real nonnegative: the first
is (2), the second is the corresponding continuous-box Hilbert-Schmidt norm.
The factor alpha^2 in (2) and (10) is essential.

Suppose the real-coordinate diameter of the list is at most theta q, with
0<=theta<1. Put a_i=2pi|Im z_i|, counting each list member, and

    C_theta=(2/pi^2)[(1-theta)^(-2)+(1-theta)^(-1)].

**Sampling lemma.** For every such finite list,

    |M_alpha^(q)-M_alpha^cont|
       <= C_theta [sum_i exp(alpha a_i)]^2/(N alpha^2 q^2)
       <= C_theta N exp(2alpha A)/(alpha^2 q^2),                (12)

where the last bound is used only if max a_i<=A. Neither point separation nor
bounded multiplicity appears.

Proof. The classical partial-fraction identity [D, 4.22.4] gives

    H(v):=csc(v)^2-v^(-2)=sum_(k!=0)(v-k pi)^(-2).

For |Re v|<=pi theta, its absolutely convergent series has modulus at most
`(2/pi^2)sum_(k>=1)(k-theta)^(-2)<=C_theta`, by the first term plus an integral.
At v=0 the singularity is removable. Direct algebra gives

    K_(q,alpha)(z)-sinc(alpha z)^2
                = sin(pi alpha z)^2 H(pi z/q)/(alpha^2 q^2).  (13)

Use `|sin(x+iy)|^2<=exp(2|y|)` and
`2pi|Im(z_i-z_j)|<=a_i+a_j`, then sum absolute values with multiplicity.
This proves both bounds in (12). Bounds for H require only the real strip;
there is no hidden small-imaginary-part assumption in that step.

**Necessary scope guard.** Two distinct real simple points at 0 and q have,
for q divisible by four and alpha in {1/2,3/4,1}, sampled moment 2 and continuous
moment 1. Their sampled vectors are collinear up to a phase, while their
continuous sinc cross term is zero. The error is exactly 1 as q grows.
Their diameter is q, not theta q for a fixed theta<1. Thus the real-diameter
margin in (12) cannot be silently omitted. These are not actual zeta zeros.

## 6. Actual source sampling at fixed subcritical bandwidth

The sole external arithmetic input PC is the fixed-test pair-correlation
formula stated in [L, Lemma 3.1], together with the classical asymptotic
`N(T)~V_T=T log(T)/(2pi)`, the critical strip and reflection symmetry.
PC has not been independently audited here. Its derived rectangular moment,
recorded in round 16, is re-derived briefly to expose all dependencies.

For a FIXED even compact C^2 nonnegative profile r of support length <1, put
q_r=r*r and `ell=log T`. In the coordinates
`z_rho=-i(rho-1/2)ell/(2pi)`, the exact deweighting identity is

    sum rhat(z-z')^2
      =sum q_r_hat(z-z') w(rho-rho')
          -(4ell^2)^(-1)sum (q_r'')_hat(z-z') w(rho-rho').      (14)

It follows from `w=(1+pi^2(z-z')^2/ell^2)^(-1)` and Fourier differentiation.
PC applies to each of the TWO FIXED tests separately. q_r'' is Lipschitz
because q_r'''=r''*r' is bounded. Consequently the limit of (14) divided by
V_T is `int r^2+int |v|(r*r)(v)dv`.

For fixed 0<b<1, sandwich the indicator of [-b/2,b/2] between nonnegative
compact C^2 profiles with transition width e and support length <1. For example
use `1-10t^3+15t^4-6t^5` on each transition. Nonnegative convolution preserves
the ordering, and the full pair sum equals the integral of the convolution
against `|sum_z exp(2pi i z v)|^2`. Take T->infinity with b,e fixed, and only
then e->0. The two limits of the sandwich are b+b^3/3. After division by b^2,

    M_b(T) -> kappa(b)=1/b+b/3, for every fixed 0<b<1.           (15)

No termwise positivity, zero depth, cell assignment or moving-test estimate
is used. This does not prove the endpoint b=1 asymptotic.

Now fix theta in (0,1), KEEP ALL actual zeros with 0<gamma<=T, set x=theta z,
and choose the MATRIX DIMENSION

    q(T)=4 ceil(V_T/4).                                       (16)

It is not a number of assigned cells. The real diameter is <=theta V_T<=theta q,
max normalized depth is at most `A_T=theta log(T)/2`, and `N/q->1`. For the
same zero list at both alpha=1 and alpha=3/4, (12) gives

    |M_alpha^(q)(T)-M_(alpha theta)(T)|
      <= C_theta N T^(alpha theta)/(alpha^2 q^2)
       = O_(theta,alpha)(T^(alpha theta-1)/log T) ->0.           (17)

Thus growing depths are controlled directly by the subcritical bandwidth and
q^2 denominator; no assertion that normalized depths are bounded or their tail
mass is small is required. Large local congestion and high multiplicities are
also allowed. No actual large matrix or zero list was computed in this round.
Equations (15)-(17) give the two sampled source moments kappa(theta) and
kappa(3theta/4). They are NOT replaced at finite theta by 4/3 and 19/12.

## 7. A source-conditional scalar consequence, weaker than the literature

Let sigma_* be the liminf simple-critical-line fraction, and take a subsequence
of heights realizing it. Fix theta FIRST. Equations (3), (15)-(17) show
`sigma_*+kappa(theta)-2>=0`; allowing theta to approach one gives sigma_*>=2/3.
Apply (9) on that same subsequence, and then let theta increase to one. This
uses fixed-bandwidth limits in that order, never theta=theta(T). With
`epsilon=sigma_*-2/3>=0` and alpha=3/4, the necessary inequality becomes

    5/192 <= epsilon/2+sqrt((10/3+2epsilon)epsilon).             (18)

The right side is strictly increasing. Its equality root is

    epsilon_*=(10sqrt(4162)-645)/672
              =0.000201852160078095907596217452778... .        (19)

To verify the algebra, the root satisfies
`64512 epsilon^2+123840 epsilon-25=0`; the relevant root is positive and
less than 5/96, so squaring introduces no sign reversal. An exact rational
lower certificate is

    (5/192-1/10000)^2-(10/3+2/5000)/5000
                         =89617/14400000000>0,

which proves epsilon_*>1/5000. Conditional on PC and the stated standard source
facts, the candidate deduction is therefore

    liminf N_0^s(T)/N(T) >= 2/3+epsilon_*
                         =0.66686851882674476257426... .       (20)

**This is NOT a new record.** [L, Theorem 1.1] already states the stronger
`3/2-cot(1/sqrt(2))/sqrt(2)=0.672500703679...`. That theorem is not used to
prove (20); it is the benchmark against which the present weaker deduction is
reported. The contribution is the finite mixed-row/alias interface, not an
improvement to the known simple-zero proportion. Decimal evaluations are not
interval certificates; (18)-(20) have exact algebraic meanings.

## 8. Research status, failure boundaries and next action

The historical matching problem is not solved or disproved here. Instead this
route makes small matching cost unnecessary for its own weaker source bound:
no clipping, deletion, orbit-to-cell injection, fixed normalized depth cap,
local occupancy bound, H coverage or Omega coherence is used in (8)-(20).
The real-diameter margin, constant-modulus real columns, fixed-test PC input,
source strip/asymptotic and height-then-bandwidth limit order remain explicit.
No claim is made for arbitrary tapers or at bandwidth one with finite-height
uniform error. No upstream theorem or earlier candidate becomes independently
verified through this solver re-derivation.

The frozen checker evaluates exact coefficient/multiplier/scalar identities,
finite crowded and higher-multiplicity matrices, selected-coordinate expansions,
sampling against continuous signed pair sums, separate quadrature, and resonant
alias guards. Matrix range calculations use an explicit SVD threshold only for
numerical diagnostics. Universal claims rely on the proofs above, not that
threshold, random tests or generic repository CI.

Next proposed task A-RH-PROFILE-0019: audit the new mixed-row and alias lemmas
first, then derive a comparable selected-row inequality for nonconstant even
profiles and determine whether it improves on, or has an obstruction at, the
existing Montgomery--Taylor benchmark. Do not spend further rounds advertising
tiny improvements above 2/3 while ignoring the stronger source result. Any new
profile must keep its discrete/continuous normalization and fixed-test limits.
No RH proof, independent receipt or mathematical-authority promotion is claimed.
