# A-RH-OFFDIAG-0020 — fixed-band positive tests resolve into height weights

Date: 2026-09-08. Issue #128. **Proof candidate; no independent receipt.**
This is a solver continuation, not the isolated review in #124.
Frozen parent: A-RH-PROFILE-0019 at
`0017c5895a91327adc18e0964a25f365cd60e4a3`, proof blob
`65b686c2dd56958a88daf9d35b3fecc7835f1d5b`.
Primary inputs and historical scope are separated in source-scope.md.

The new object is genuinely non-diagonal, but its matrix bandwidth is FIXED.
We evaluate its source side, identify the additional simple-height measure, and
prove a consistency boundary for this particular scalar-inequality family.
Neither that boundary nor the source evaluation is a new zero-proportion record.

## 1. Test family and finite signed inequality

Let a finite conjugation-invariant multiset have N>0 members, counting original
multiplicity, and n simple real members. Group repetitions before counting n.
A nonsimple real orbit has mass m>=2 and depth zero; a nonreal orbit has even
mass m and members t +/- ia/(2 pi), each of mass m/2. No cell assignment, gap,
clipping, or depth cap is imposed on this finite object.

On I=[-1/2,1/2] let r>0 be a real even exponential polynomial with integral one.
Frequencies may be real, not just integers. Choose q>=1 and put

    u_j=(j-(q-1)/2)/q, Z=q^(-1)sum_j r(u_j), p_j=r(u_j)/(qZ).

The real atom is v_t(j)=sqrt(p_j)exp(2 pi i t u_j). With V the simple columns,
and G,H the nonsimple sqrt(m)v_t cosh(a u), sqrt(m)v_t sinh(a u) columns, set

    S=VV*, T=S+GG*-HH*, D=n+||T||_F^2-2N.                       (1)

Choose a nonnegative real even exponential polynomial d on I, and a fixed
nonnegative trigonometric polynomial on the circle

    g(y)=sum_(|h|<=H) g_h exp(-2 pi i h y), g_-h=conj(g_h).

Let G_q(g)_(ij)=g_(i-j), and set

    C_q=diag(sqrt(d(u_j))) G_q(g) diag(sqrt(d(u_j))).            (2)

The matrix is positive semidefinite: for a vector v the Toeplitz quadratic
form is the integral of g times the squared modulus of its exponential
polynomial. Consequently

    ||C_q||op <= ||d||infinity ||g||infinity,
    ||C_q||F^2 = sum_(|h|<q)|g_h|^2
                        sum_(0<=j<q-|h|) d(u_j)d(u_(j+|h|)).   (3)

This gives q^(-1)||C_q||F^2 -> (integral_I d^2)(integral_0^1 g^2) at fixed H.
A nonzero g_h for h!=0 makes (2) non-diagonal. Autocorrelation coefficients of
any finite polynomial give convenient examples with g>=0; the theorem does
not assume real g_h or even g.

We use the finite positive-test inequality, re-derived here:

    D>=0,
    tr C(T^2-2T+S)>=-sqrt((4||C||F^2+2n||C||op^2)D), C>=0.     (4)

To check its inputs, write U=ran G, E=ran((I-P_U)V), F=(U+E)^perp,
Q0=2P_U+P_E, R=T-Q0, J=Q0-I, B=HH*, nu=N-n,
xi=tr(P_U S), zeta=tr((I-P_U)B), zeta_F=tr(P_F B). Trace expansion gives

    D=||R||F^2+2(nu-2dim U)+2xi+2zeta+2zeta_F+n-dim E.          (5)

All terms are nonnegative: dim U<=nu/2 and dim E<=n. The signed norm identity
for each pair is pointwise cosh^2-sinh^2=1. In the decomposition U,E,F,

    tr C(T^2-2T+S)
     =tr[(CJ+JC+P_E C P_E)R]
        +tr C(R^2+P_U S P_U+P_E B P_E)
        +2 Re tr(C (P_U V)(P_E V)*).

The middle trace is nonnegative. The block multipliers in the first bracket
have modulus <=2, hence its Frobenius norm is <=2||C||F. The last trace is
bounded in modulus by 2||C||op sqrt(n xi). Cauchy-Schwarz and
||R||F^2+2xi<=D prove (4). This is not a general Schur-multiplier operator-norm
assertion, and no numerical rank decision is needed for the proof.

## 2. Exact off-diagonal dictionary: the second point carries a height phase

Expand the full multiset into members z_a, including multiplicity, and define

    F_(r,q)(w)=q^(-1)sum_j r(u_j)exp(2 pi i w u_j),
    v(u)=sqrt(d(u)r(u)),
    H_(h,q)(w)=q^(-1)sum_(j=0)^(q-h-1)
                     v(u_j)v(u_(j+h))exp(2 pi i w u_j),
    beta_(h,q)=(qZ)^(-1)sum_(j=0)^(q-h-1) v(u_j)v(u_(j+h)).

For 0<=h<q, write

    L_h^(2)=N^(-1)sum_j sqrt(d(u_j)d(u_(j+h)))(T^2)_(j,j+h),
    L_h^(1)=N^(-1)sum_j sqrt(d(u_j)d(u_(j+h)))T_(j,j+h).

Direct expansion, using evenness of r in the second Fourier factor, gives

    L_h^(2)=(NZ^2)^(-1)sum_(a,b)
       exp(-2 pi i h z_b/q) H_(h,q)(z_a-z_b)F_(r,q)(z_a-z_b),
    L_h^(1)=beta_(h,q) N^(-1)sum_b exp(-2 pi i h z_b/q).         (6)

The simple version of L_h^(1) has the SAME beta and a sum only over original
simple real members. Negative lags are conjugates. Thus
tr(C_q T^2)/N=sum_h g_h L_h^(2), and similarly for T and S.
The exponential in (6) depends on z_b, not only on z_a-z_b. Equivalently, a
midpoint-centered H puts exp(-pi i h(z_a+z_b)/q) in front. Omitting this factor
would change the observable and cannot be justified by difference-only PC.

For strictly positive r,d, let M=||sqrt(dr)||infinity and L be a Lipschitz
constant of sqrt(dr) on I. For every complex w and 0<=h<q,

    |H_(h,q)(w)-F_(dr,q)(w)|
             <= (h/q)(ML+M^2) exp(pi |Im w|).                  (7)

Indeed compare the q-h retained products with v(u_j)^2 using the Lipschitz
bound, then charge the h missing endpoint terms. The bound explicitly costs
h/q. It is not uniform for h comparable to q. Nonnegative d with zeros will
be treated by d+epsilon and a uniform operator-norm approximation in section 5.

## 3. New source input derived from PC: macroscopic height weights

Use the fixed-test unconditional pair-correlation input PC stated in [L,
Lemma 3.1], as in the parent, and the classical Riemann-von Mangoldt formula
with its O(log T) remainder [R]. We do NOT independently audit those theorems.
For fixed 0<theta<1 set ell=log T and

    z_rho=-i theta(rho-1/2)ell/(2pi),
    V_T=T ell/(2pi), q(T)=4ceil(V_T/4), N=N(T).

The critical strip implies a_rho=2pi|Im z_rho|<=theta ell/2. Reflection in
the critical line preserves every restriction by ordinate. Also N/q->1.
The O(log T) remainder implies that each real ordinate interval of length one
in [0,T] contains at most M_T=O(log(T+2)) zeros, WITH multiplicity. We need
this upper bound, NOT a falsely uniform local asymptotic for every unit interval.

Let f,k be fixed nonnegative even exponential polynomials on I, zero outside.
Write F_f(z)=integral_I f(u)exp(2pi i z u)du and

    K_(f,k)(rho,rho')=F_f(z_rho-z_rho')F_k(z_rho-z_rho'),
    B_theta(f,k)=theta^(-1)integral_I f k
                    +theta integral_(I x I)|u-v|f(u)k(v)du dv.

**Height-weighted moment theorem (conditional on PC and [R]).** For every
fixed complex C^1 function a on [0,1],

    (1/N)sum_(rho,rho') a(gamma'/T) K_(f,k)(rho,rho')
                 -> B_theta(f,k) integral_0^1 a(y)dy.          (8)

No simple-zero restriction is present in this double sum. The proof follows;
this is not an assumption of a stronger twisted-PC theorem.

### 3.1 Kernel tails and a uniform signed interface charge

Finite exponential expansions, or one integration by parts, give

    |F_f(z)| <= C_f exp(pi |Im z|)/(1+|Re z|).

For sufficiently large T (depending on fixed theta), this implies

    |K_(f,k)(rho,rho')|
             <= C_(theta,f,k) T^theta/(1+|gamma-gamma'|)^2.    (9)

The exponent follows from 2pi|Im(z_rho-z_rho')|<=a_rho+a_rho'<=theta ell.
No favorable sign of a complex kernel summand is assumed.
Across an arbitrary real cut Y, place unit bins immediately to its left and
right, indexed by i,j>=0. There are at most M_T^2 pairs for each bin pair,
the distance is at least i+j, and at lag l=i+j there are at most l+1 bin
pairs. Hence, including both orientations,

    sum_(gamma<=Y<gamma' or gamma'<=Y<gamma) |K_(f,k)|
       <= 2 C_(theta,f,k) T^theta M_T^2
                             [1+log(2ceil(T)+3)] = o(N).      (10)

After division by N this is O(T^(theta-1)log(T+2)^2), uniformly in Y.
The constants in (9)-(10) depend on fixed profiles and theta; no effective
PC remainder or endpoint uniformity is claimed.
The same binning gives the absolute pair bounds

    sum |K_(f,k)| <= C T^theta N M_T,
    sum |gamma-gamma'| |K_(f,k)|
                           <= C T^theta N M_T[1+log(T+2)].    (11)

### 3.2 Prefix limits, and why dominated convergence is legitimate

Define the possibly nonmonotone step function

    A_T(y)=(1/N)sum_(0<gamma,gamma'<=yT) K_(f,k)(rho,rho').

For EVERY conjugation-invariant sublist the full sum equals the integral of
(f*k) against the nonnegative exponential density. Thus A_T(y)>=0. The same
holds for the complementary ordinate sublist. Equation (10) therefore gives

    0<=A_T(y)<=A_T(1)+o(1), uniformly in y in [0,1].            (12)

This is the missing uniform bound; one must not use monotonicity of A_T.

For each fixed y>0, PC implies

    A_T(y) -> y B_theta(f,k).                                  (13)

Here the rescaling requires care: at cutoff yT the effective bandwidth is
eta_T=theta log T/log(yT)->theta<1, not a fixed test literally. This small
INTERIOR variation is covered by a fixed-envelope argument. For any epsilon>0
with theta+2epsilon<1, all rescaled nonnegative profiles
eta^(-1)f(v/eta), eta^(-1)k(v/eta), for |eta-theta|<epsilon, admit fixed
nonnegative inner/outer compact C^2 envelopes. Their L1 and L2 errors from the
theta profiles tend to zero as epsilon->0. Construct them using derivative
bounds on the common interior, a boundary strip of width O(epsilon), and
nonnegative smooth cutoffs. PC applies to each fixed convolution Q and Q'';
Q'''=f''*k' is bounded. Fourier differentiation removes the PC weight exactly:

    unweighted_sum(Qhat)
       =weighted_sum(Qhat)-weighted_sum((Q'')hat)/(4log(yT)^2).

The second term tends to zero after normalization. Positivity of the COMPLETE
convolution integral preserves the sandwich. First let T->infinity with all
envelopes fixed, and only then epsilon->0. Finally N(yT)/N(T)->y proves (13).
This argument does not cover a bandwidth tending to the SUPPORT ENDPOINT one.
At y=0 the prefix is empty. It also proves A_T(1)->B_theta(f,k), used in (12).

### 3.3 Integrate the prefixes, not a guessed simple-height distribution

Finite Stieltjes integration, valid for signed step increments, gives

    (1/N)sum a(max(gamma,gamma')/T) K_(f,k)
               = a(1)A_T(1)-integral_0^1 a'(y)A_T(y)dy.

The uniform bound (12) and pointwise limit (13) justify dominated convergence.
The limit is B_theta(f,k) integral a. Replacing max(gamma,gamma') by gamma'
changes the sum by at most ||a'||infinity/T times the second bound in (11),
divided by N. This is O(T^(theta-1)log(T+2)^2)->0. Equation (8) follows.
The proof handles complex a by its real and imaginary parts. All depths and
multiplicities remain present; nothing here says that simple zeros alone have
a uniform height distribution.

## 4. From the exact lag product to its source limit

The parent shifted-product sampling estimate applies to F_(dr,q)F_(r,q).
For fixed exponential polynomials f,k of frequency radius <=Lambda and
coefficient sums A_f,A_k, if |Re z|+Lambda<=vartheta q<q, it states

    |F_(f,q)(z)F_(k,q)(z)-F_f(z)F_k(z)|
     <= pi^2 cosh(pi |Im z|/q)(1+2Lambda) A_f A_k
                    exp(2pi |Im z|)/(3 sinc(vartheta)^2 q^2). (14)

For audit: D_q(w)=sinc(w)m(pi w/q), m(v)=v/sin v;
|sin v|>=sinc(vartheta)|v| on the stated complex strip, and
|sin v-v|<=|v|^3 cosh(|Im v|)/6. Expand the product of two m factors and use
|sinc(w)|<=exp(pi|Im w|)/max(1,|w|). For the two fixed shifts their normalized
quadratic ratio is <=2(1+2Lambda), proving (14). Removable points use the entire
finite sums. Also Z=1+O_r(q^-2).

Take vartheta=(1+theta)/2. The source margin in (14) holds eventually, and the
summed error divided by N is O(N T^theta/q^2)=o(1). For (7), the discrete
F_(r,q) has bound C exp(pi|Im z|)/(1+|Re z|) on the same margin. Unit-bin
summation of this ONE-power denominator is O(N M_T[1+log T]). Thus (7), even
after multiplication by exp(-2pi i h z_b/q), contributes only
O_h(T^(theta-1)log(T+2)^2)=o(1) to (6), for each FIXED h.
The exponential has modulus <=exp(h theta ell/(2q))=1+o(1).

Replace exp(-2pi i h z_b/q) by exp(-2pi i theta h gamma_b/T).
Its uniform error is O_h(ell/q): the imaginary displacement is O(ell), and
V_T/q=1+O(1/q). Equation (11) controls the product error by o(1), without
assuming a bounded absolute pair moment. Apply (8) with f=dr, k=r and
 a(y)=exp(-2pi i theta h y). Consequently

    L_h^(2) -> B_theta(dr,r) integral_0^1 exp(-2pi i theta h y)dy,
    L_h^(1) -> (integral_I dr) integral_0^1 exp(-2pi i theta h y)dy. (15)

For the second formula one only needs beta_(h,q)->integral dr, the strip,
and the ordinary zero-count measure N^(-1)sum delta_(gamma/T) -> dy.
All normalizers in (6) are retained before taking limits.

Strict positivity of d was used only for the Lipschitz estimate (7). To allow
a fixed nonnegative d with zeros, first replace it by d+epsilon. Uniformly in q,

    ||C_q(d+epsilon)-C_q(d)||op
      <= ||g||infinity sqrt(epsilon)(2sqrt(||d||infinity)+sqrt(epsilon)).

For T^2 the trace difference divided by N is bounded by this norm times
||T||F^2/N, which is bounded by the source profile limit. For S it is bounded
by the norm times n/N. For T use its signed column decomposition only if its
trace norm is controlled; instead use the exact linear formula (6), where
|beta(d+epsilon)-beta(d)| obeys the same uniform bound and the finitely many
normalized exponential sums are bounded by the critical strip. Thus let
T->infinity first, then epsilon->0. This proves (15) for d>=0 without silently
assuming a uniform trace-norm bound for the signed T.

## 5. What the simple sector adds

Take any subsequence on which sigma_T=n(T)/N(T) converges to sigma and the
finite measures

    nu_T=(1/N(T))sum_(simple critical-line zeros) delta_(gamma/T)

converge weakly to nu. Such a further subsequence exists on compact [0,1], and

    0<=nu<=dy, nu([0,1])=sigma.                                (16)

This follows because nu_T is dominated by the all-zero counting measure, whose
limit is dy. No equidistribution of nu is inferred. Put

    W_theta(g)=integral_0^1 g(theta y)dy, t=integral_I dr.

Summing the finitely many lags in (15), and using weak convergence for S, gives

    tr(C_q T^2)/N -> B_theta(dr,r) W_theta(g),
    tr(C_q T)/N -> t W_theta(g),
    tr(C_q S)/N -> t integral_0^1 g(theta y)dnu(y).              (17)

These are source-evaluable non-diagonal tests, with the last observable
explicitly left as a simple-height measure. With
Delta_r=sigma+B_theta(r,r)-2, equation (4) implies Delta_r>=0 and

    W_theta(g)[B_theta(dr,r)-2t]+t integral g(theta y)dnu(y)
      >= -sqrt([4(integral d^2)(integral_0^1 g^2)
             +2sigma ||d||infinity^2||g||infinity^2]Delta_r).   (18)

The Frobenius limit in (3) and q/N->1 were used; replacing the operator norm by
its upper bound only weakens the inequality. Parameters theta,r,d,g and H are
fixed before the height limit. The SAME weak-limit measure nu enters every
such constraint; it must not be separately optimized for each test.

## 6. A simultaneous consistency witness at the classical benchmark

Let lambda_1=1/2+cot(1/sqrt(2))/sqrt(2), sigma_MT=2-lambda_1. These are the
classical Montgomery-Taylor constants attributed in [L], not new results.
The following theorem concerns only the scalar necessary conditions (16),(18).

**Consistency theorem.** One witness,

    sigma=sigma_MT, nu=sigma_MT dy,

simultaneously satisfies every constraint (18) for

    9/10<=theta<=1, r>0 even, integral r=1, ||r||infinity<=3/2,
    d>=0 as above, and every fixed nonnegative trigonometric symbol g. (19)

At theta=1 the constraints mean the limit theta->1 AFTER fixed-theta source
limits. They do not assert the source asymptotic at theta=1 itself.

For completeness, L_theta=theta^-1 I+theta K, Kf(x)=integral |x-y|f(y)dy,
is positive on real L2(I): ||K||op<=1/2. Its normalized positive minimizer is

    r_theta(x)=theta cos(sqrt(2)theta x)/(sqrt(2)sin(theta/sqrt(2))),
    L_theta r_theta=lambda_theta=theta/2+cot(theta/sqrt(2))/sqrt(2).

The ODE r_theta''=-2theta^2 r_theta, symmetry, and evaluation at x=1/2 prove
the constant-potential identity. For integral r=1, k=r-r_theta has zero mean,
so B_theta(r,r)=lambda_theta+B_theta(k,k). Also lambda_theta>=lambda_1 for
0<theta<=1. These give Delta_r=B_theta(r,r)-lambda_1>=B_theta(k,k)>=0.

Cauchy-Schwarz in B_theta and ||K||op<=1/2 imply

    B_theta(dr,r)-lambda_1 t
       >=-sqrt((theta^-1+theta/2)||r||infinity^2 integral d^2 Delta_r).

Because g>=0 and has period one,

    0<=W_theta(g)<=theta^(-1/2)(integral_0^1 g^2)^(1/2).

For (19) the combined coefficient has the EXACT rational majorant

    ||r||infinity^2(theta^-2+1/2)
           <=(9/4)(100/81+1/2)=281/72<4.                     (20)

Multiplying the preceding two bounds proves a stronger lower bound than (18)
for the uniform witness; the extra 2sigma term in (18) is nonnegative. The
witness satisfies (16), too. This is a simultaneous proof, not a finite scan.
It covers the classical optimizers: with x=theta/sqrt(2),
||r_theta||infinity=x/sin x<=1/(1-x^2/6)<=12/11<3/2.
At theta=1, r=r_1, both Delta_r and the entire left side of (18) vanish for
EVERY d and g under this witness. There is exact stationarity cancellation.

Thus these fixed-band SEPARABLE tests supply genuine height observables but
the displayed scalar constraints alone do not force an improvement over
sigma_MT. The witness is a measure satisfying necessary inequalities, NOT an
actual extremizing zeta configuration or a construction of a full matrix
moment state. The result does not cover growing H, changing profiles with T,
general nonseparable PSD matrices, sharper joint inequalities obtained by
reapplying (4) to sums with better norm bounds, or additional arithmetic data.
Nonnegative combinations of the inequalities already in (18) preserve the
witness; that statement is narrower than a new optimized test on their sum.

## 7. Finite guards against unjustified extensions

**Difference data are not enough at finite size.** Take q=2, r=d=1, the two
simple real points {0,1/2}, and g(y)=1+cos(2pi y). Then C has diagonal one and
off-diagonal 1/2. Translating BOTH points by one preserves every difference,
all difference-only profile moments, and ||T||F^2=3. Nevertheless

    tr(CT): 5/2 -> 3/2,   tr(CT^2): 4 -> 2.                   (21)

This is exactly the phase in (6). It is not a counterexample to the source
theorem: that theorem also uses the global counting law and the uniform
interface estimate. A height-blind application of PC alone is invalid.

**Fixed lag cannot be turned into arbitrary lag.** One real simple point at
zero, r=d=1, has T_ij=1/q. For every even q and h=q/2,

    sum_(j=0)^(q-h-1) T_(j,j+h)=(q-h)/q=1/2,                 (22)

whereas the fixed-h limiting replacement is one. The endpoint loss persists.
This guard does not rule out smaller growing lags; those require uniform
bounds and height-weighted PC beyond the fixed-test limit established here.

**Simple fraction is not its height measure.** Measures (1/4)dy and
1_[0,1/4]dy have the same total mass and are both dominated by dy, but their
integrals against 1+cos(2pi y) are respectively 1/4 and 1/4+1/(2pi).
Only the explicitly chosen consistency witness in section 6 is uniform.
These are measure-level guards, not claims about actual simple-zero locations.

## 8. Handoff and evidence boundary

The finite identities, kernel/counting estimates and consistency theorem are
solver candidates. Source limits additionally depend on PC and the stated
classical counting/strip facts. The prior isolated audit #124 is not performed
by this inherited-context run. No mathematical authority, new best proportion,
actual-zero computation, moving-endpoint theorem, or RH proof is asserted.

The checker compares finite traces with the complex product formula, tests
positive matrices and norm bounds, executes rational interface/Gram/Stieltjes
identities and consistency regressions, and preserves both scope guards.
No finite experiment verifies a PC remainder or the height-asymptotic theorem.

A-RH-JOINT-0021 is the proposed next task: retain the JOINT operator defect
rather than its separate square-root scalar allowances. Either construct a
common positive-matrix moment witness for the complete test collection, or
find incompatible coupled tests with a source-evaluable main term. Growing
matrix lags are another distinct frontier, not licensed by (15). The present
result identifies exactly why merely adding more fixed separable bands is
insufficient for these particular inequalities.
