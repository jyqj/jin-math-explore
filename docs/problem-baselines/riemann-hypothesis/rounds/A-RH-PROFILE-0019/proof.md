# A-RH-PROFILE-0019: weighted sampling and a diagonal-test saturation boundary

Date: 2026-09-08. Issue #120. Status: **proof_candidate**, no independent receipt.
Historical parent: A-RH-CONGEST-0018 at
`92863a42864927d2a3a7a3c93aa87941d5c3150b`, proof blob
`c27af2a5abe5a87c0f35e417fce35d8f147e169c`.
This solver has inherited context. The separate parent audit #117 remains
unperformed by this run. Sections 1-3 re-derive the finite input used here;
source claims additionally assume the external PC theorem identified in [L].
The Montgomery–Taylor optimum in section 6 is classical, not a new record.

## 1. A finite profile-weighted signed operator

Let a finite conjugation-invariant multiset have total multiplicity N>0 and n
simple real elements. Combine repeated complex points before counting n. A real
nonsimple orbit has integer mass m>=2; a nonreal orbit has even total mass m>=2
and members t +/- i a/(2 pi), each of multiplicity m/2. A simple real orbit has
m=1,a=0. Keep every original multiplicity and every finite depth a. Centers need
not occupy different cells or have a minimum gap.

Choose an independent matrix dimension q>=1 and the centered grid
u_j=(j-(q-1)/2)/q, j=0,...,q-1. Let r be nonnegative on I=[-1/2,1/2], with

    Z_q=(1/q)sum_j r(u_j)>0, p_j=r(u_j)/(q Z_q), sum_j p_j=1.

Use v_t(j)=sqrt(p_j)exp(2 pi i t u_j). Let V consist of simple columns v_t;
let G,H consist of nonsimple columns sqrt(m)v_t cosh(a u), sqrt(m)v_t sinh(a u).
Put

    S=VV*, B=HH*, T=S+GG*-B,
    sigma=n/N, D=n+||T||_F^2-2N, d_r=D/N.                     (1)

Then diag(T)_j=N p_j and diag(S)_j=n p_j, NOT N/q and n/q unless r is constant.
The real columns have norm one and every pair has the required signed norm
identity, since cosh^2-sinh^2=1 pointwise. No evenness is needed for this finite
statement. Evenness will be imposed for the explicit Fourier/source dictionary.

Write U=range(G), E=range((I-P_U)V), F=(U+E)^perp, Q0=2P_U+P_E, R=T-Q0,
J=Q0-I, nu=N-n, xi=tr(P_U S), zeta=tr((I-P_U)B), zeta_F=tr(P_F B).
The trace expansion, on these finite-dimensional subspaces, gives

    D=||R||_F^2+2(nu-2dim U)+2xi+2zeta+2zeta_F+n-dim E >=0.   (2)

Indeed tr(P_U T)=nu+xi+zeta, tr(P_E T)=n-xi-zeta+zeta_F, and
||Q0||_F^2=4dim U+dim E. Substitution proves the equality. There are at most
nu/2 positive nonsimple columns and dim E<=n, so each displayed term is
nonnegative. In particular ||R||_F^2+2xi<=D. This is a re-derivation of the
parent's signed slack, not a claim that its independent review has passed.

## 2. General positive-weight row inequality

For EVERY Hermitian positive semidefinite q-by-q C,

    tr C(T^2-2T+S)
        >= -sqrt((4||C||_F^2+2n||C||_op^2)D).                 (3)

This extends the parent's coordinate-projection test; C need not be diagonal,
a projection or a contraction. The assertion does require C>=0.

Proof. Put V_U=P_U V, V_E=P_E V. All V columns lie in U+E. Compression to E
and Q0^2-2Q0=-P_E give

    tr C(T^2-2T+S)
      =tr(K_C R)+tr C(R^2+P_U S P_U+P_E B P_E)
                         +2 Re tr(C V_U V_E*),
    K_C=CJ+JC+P_E C P_E.

The middle trace is nonnegative. In the U,E,F blocks, J has scalars 1,0,-1.
The block multipliers defining K_C have magnitude at most two (the E,E block
has multiplier one). Thus ||K_C||_F<=2||C||_F; this is a Frobenius calculation,
not an operator-norm assertion about arbitrary Schur multipliers. The cross term
is bounded in modulus by 2||C||_op sqrt(n xi). Apply Cauchy-Schwarz to these two
errors and then (2), obtaining (3). Zero-dimensional sectors cause no exception.

For C=diag(c(u_j)), with c>=0, let Z_{cr,q}=q^(-1)sum c(u_j)r(u_j). Formula (3)
becomes the exact normalized inequality

    tr(CT^2)/N >= (2-sigma) Z_{cr,q}/Z_q
       -sqrt([4 sum_j c(u_j)^2/N+2sigma max_j c(u_j)^2]d_r).    (4)

This normalization keeps the profile in both the diagonal and the simple count.
Replacing Z_{cr,q}/Z_q by a coordinate fraction is generally incorrect.

## 3. Central blocks need reflection, not Toeplitz after weighting

If a Hermitian matrix A satisfies |A_{ij}|=|A_{q-1-i,q-1-j}|, then for
ceil(q/2)<=d<=q, h=q-d and the central coordinate projection P_C on [h,d),

    ||A_d||_F^2-||A_h||_F^2=tr(P_C A^2).                     (5)

Partition the coordinates into L,C,R of sizes h,2d-q,h. The left side equals
||A_CC||_F^2+2||A_LC||_F^2; the right side equals
||A_CC||_F^2+||A_CL||_F^2+||A_CR||_F^2. Hermitian symmetry and reflection make
the last two terms equal. This proves (5), including empty central/end blocks.
For an even r, the T in section 1 obeys T_{q-1-i,q-1-j}=conj(T_{ij}), so (5)
still applies even though T is not Toeplitz. Any subsequent energy estimate
must use its NONCONSTANT diagonal Np_j.

Reflection cannot simply be discarded. For one real atom, q=3 and probability
vector (1/2,1/3,1/6), T=vv*, v_j=sqrt(p_j). At d=2, the two sides of (5) are
4/9 and 1/3, respectively; the exact error is 1/9. This is a finite scope guard,
not an example about zeta zeros. General profiles without reflection need a
separate boundary term. This guard does not invalidate (3).

## 4. Explicit trigonometric-product sampling error

A profile f is represented on I by a finite real even exponential polynomial

    f(u)=sum_nu A_nu exp(2 pi i nu u), A_-nu=A_nu real.

Frequencies are fixed real numbers, not necessarily integers. Signed expansion
coefficients are allowed; profile nonnegativity, when used, is a separate
hypothesis. Define F_f(z)=integral_I f(u)exp(2 pi i z u)du and
F_{f,q}(z)=q^(-1)sum_j f(u_j)exp(2 pi i z u_j). Then

    F_f(z)=sum_nu A_nu sinc(z+nu),
    F_{f,q}(z)=sum_nu A_nu D_q(z+nu),
    D_q(w)=sin(pi w)/(q sin(pi w/q)).

D_q is its entire finite geometric sum; removable values are retained. Let
f,g have frequency radii at most Lambda and coefficient sums A_f=sum|A_nu|,
A_g. Suppose |Re z|+Lambda<=vartheta q for 0<=vartheta<1. Put
c_vartheta=sinc(vartheta)>0, Y=|Im z|. We prove

    |F_{f,q}(z)F_{g,q}(z)-F_f(z)F_g(z)|
     <= pi^2 cosh(pi Y/q)(1+2Lambda) A_f A_g
                          exp(2pi Y)/(3 c_vartheta^2 q^2).   (6)

Proof. If |Re v|<=pi vartheta, then
|sin v|^2=sin(Re v)^2+sinh(Im v)^2>=c_vartheta^2|v|^2.
This follows from the decreasing sinc on [0,pi) and |sinh y|>=|y|. Taylor's
integral remainder along the segment from 0 to v gives
|sin v-v|<=|v|^3 cosh(|Im v|)/6. Thus m(v)=v/sin v obeys

    |m(v)|<=1/c_vartheta,
    |m(v)-1|<=|v|^2 cosh(|Im v|)/(6c_vartheta).

For w=z+nu, w'=z+mu, apply these to m(pi w/q)m(pi w'/q)-1. Use
|sinc w|<=exp(pi Y)/max(1,|w|). The remaining ratio satisfies

    (|w|^2+|w'|^2)/(max(1,|w|)max(1,|w'|)) <=2(1+2Lambda),

because |w-w'|<=2Lambda and x -> max(1,|x|) is 1-Lipschitz. Summing the
coefficient products proves (6). This includes shifted kernels near zero and
does not hide a small-imaginary-part assumption; the explicit cosh factor is kept.

For a finite conjugation-symmetric list z_i with multiplicities and N members,
let a_i=2pi|Im z_i| and Y_max=max_{i,j}|Im(z_i-z_j)|. If its real diameter plus
Lambda is <=vartheta q, the raw pair moments obey

    |M_q(f,g)-M_cont(f,g)|
      <= pi^2 cosh(pi Y_max/q)(1+2Lambda) A_f A_g
             (sum_i exp(a_i))^2/(3 c_vartheta^2 N q^2),        (7)

where M_q=N^(-1)sum_{i,j}F_{f,q}(z_i-z_j)F_{g,q}(z_i-z_j), and M_cont uses
F_f,F_g instead. These are complex products, not termwise absolute squares.
Conjugation reindexing and evenness identify M_q(cr,r)/Z_q^2 with tr(CT^2)/N,
and M_q(r,r)/Z_q^2 with ||T||_F^2/N for section 1. Both complete sums have
positive integral/matrix interpretations when the profiles are nonnegative.

The raw and normalized expressions must not be confused. For integral r=1,

    |Z_q-1| <= pi^2 sum_nu |A_nu|nu^2/(6c_vartheta q^2)       (8)

whenever its frequency radius is <=vartheta q. Apply the preceding m-1 bound
to real nu, and use |sinc nu|<=1. The same argument controls Z_{cr,q} minus
integral cr. For a normalized finite comparison retain the factors Z_q^-2
explicitly; they are asymptotically one, not exactly one. Fixed nonzero profiles
have Z_q>0 for sufficiently large q. At a small q this must be checked.

The parent's alias guard is retained: the constant profile and two real points
0,q give sampled moment 2 and continuous moment 1. Their diameter violates the
fixed margin. Neither (6) nor (7) licenses a critical-diameter interchange.

## 5. Source-conditional profile limits

The external input PC is [L, Lemma 3.1]: for each FIXED real even test f supported
in [-1,1] and Lipschitz at zero, its weighted pair sum divided by
V_T=T log(T)/(2pi) tends to f(0)+integral |v| f(v)dv, with the weight
4/(4-(rho-rho')^2). Also use the classical zero-count asymptotic N(T)/V_T->1,
critical strip and conjugation symmetry. These are identified external inputs,
not an independent audit of their proofs.

For fixed nonnegative even profiles f,g on I, extend them by zero outside I and
fix 0<theta<1. For the actual zero coordinates x_rho=-i theta(rho-1/2)log(T)/(2pi),
the unweighted continuous pair moment has the candidate limit

    M_cont(f,g;T) -> B_theta(f,g),
    B_theta(f,g)=(1/theta) integral_I f g
                 +theta integral_I integral_I |u-v|f(u)g(v)du dv.  (9)

Here we need (9) for fixed nonnegative even exponential polynomials f,g,
including their products. Their zero extensions need not be smooth at the edges.
To justify (9), first replace them by compact C^2 inner and outer envelopes on
slightly smaller/larger intervals. They can be chosen nonnegative and converging
in L1 and L2: multiply the analytic profile by an inner cutoff, and for the outer
cutoff use its analytic extension plus O(e) sufficient to offset any negative
values immediately outside I. Bounded derivatives near I ensure this construction.
The scaled supports can be kept inside (-1/2,1/2) because theta is fixed below one.

For each smooth pair, the convolution Q=f_theta*g_theta and Q'' are admissible
FIXED tests, with f_theta(v)=f(v/theta)/theta. The exact identity

    sum F_{f_theta}(z-z')F_{g_theta}(z-z')
      = weighted_sum(Qhat) - weighted_sum((Q'')hat)/(4log(T)^2)

removes the extra weight, by Fourier differentiation. Q'' is Lipschitz since
Q'''=f_theta''*g_theta' is bounded. PC applies separately to Q and Q''. The
limiting main term is (9). Nonnegative convolution orders the inner/outer tests
against the positive complete density |sum_z exp(2pi i z v)|^2. Take T->infinity
with theta and both envelopes fixed, THEN shrink their transition widths.
No individual complex summand is asserted positive; no moving-test remainder
constant is used. This is the same fixed-test principle as [L] and round 16,
now stated for mixed profiles. Its use is source-conditional, not a novelty claim.

Take q(T)=4ceil(V_T/4). Its role is matrix dimension, not spatial cell assignment.
The actual list has real diameter <=theta q, depths a_i<=theta log(T)/2 and
N/q->1. Set vartheta=(1+theta)/2. For fixed profiles the shifted real margin in
(7) holds eventually. Its error is

    O_{theta,f,g}(N T^theta/q^2)
                       =O_{theta,f,g}(T^(theta-1)/log T)->0,

and cosh(pi Y_max/q)->1. All zeros and multiplicities are retained, including
growing normalized depths. Equations (8)-(9) give the same limits for the
normalized sampled forms; no actual large zero matrix is computed here.

Let sigma be a subsequential limit of the simple-critical-line fraction. For
every fixed admissible r,c, integral r=1, (2) and (4) therefore imply

    d_theta(r,sigma):=sigma+B_theta(r,r)-2 >=0,
    B_theta(cr,r) >= (2-sigma) integral cr
       -sqrt([4 integral c^2+2sigma ||c||_infinity^2]d_theta).  (10)

The replacement of the sampled max by the continuous supremum only weakens the
necessary inequality. Height tends to infinity at FIXED theta,r,c first. The
endpoint theta=1 in subsequent algebra denotes the limit theta increasing to
one AFTER that step. There is no endpoint source asymptotic or theta(T) theorem.

## 6. Recovering, not improving, the classical optimum

Write Kf(x)=integral_I |x-y|f(y)dy and L_theta=theta^-1 I+theta K. Since
integral_I |x-y|dy=x^2+1/4<=1/2, the Schur bound gives ||K||op<=1/2. Hence
B_theta is a positive definite real inner product for 0<theta<=1, with

    B_theta(f,f) <= (theta^-1+theta/2)||f||_2^2.                (11)

The normalized positive cosine profile and its constant potential are

    r_theta(x)=theta cos(sqrt(2)theta x)/(sqrt(2)sin(theta/sqrt(2))),
    L_theta r_theta = lambda_theta,
    lambda_theta=theta/2+(1/sqrt(2))cot(theta/sqrt(2)).           (12)

Indeed its integral is one, r_theta''=-2theta^2 r_theta, and (Kr_theta)''=2r_theta.
Evenness makes L_theta r_theta constant; evaluate at x=1/2, using
Kr_theta(1/2)=1/2, to get (12).

For every real r in L2(I) with integral one, put g=r-r_theta. Then

    B_theta(r,r)-lambda_theta=B_theta(g,g)
       >=(theta^-1-2theta/pi^2)||g||_2^2 >=0.                  (13)

For the sharper last bound put G(x)=integral_{-1/2}^x g. Integration by parts
shows integral g Kg=-2 integral G^2. Since G vanishes at both endpoints,
the one-dimensional Dirichlet Poincare inequality (or sine-series expansion)
gives ||G||_2^2<=||g||_2^2/pi^2. This proves (13) and uniqueness of the minimizer.
The minimizer is itself positive, so it also solves the nonnegative-profile
problem. This recovers the attributed Montgomery–Taylor variational result;
it is not presented as a new extremizer or a new optimality theorem.

As theta increases to one, lambda_theta decreases, since
lambda_theta'=-cot(theta/sqrt(2))^2/2<0. Put

    lambda_1=C_MT=1/2+(1/sqrt(2))cot(1/sqrt(2)),
    sigma_MT=2-lambda_1=0.6725007036794116457... .               (14)

The first inequality in (10) with r=r_theta recovers this existing bound via
the direct sampled route. It improves the PARENT ROUTE's rectangular coefficient,
not the already known literature benchmark. The 80-digit evaluation in the
checker is numerical, not an interval certificate or independent source proof.

## 7. A precise barrier for the present diagonal scalar constraints

**Theorem (saturation of this test family).** Set sigma=sigma_MT. Every scalar
constraint in (10) is simultaneously satisfied whenever

    9/10<=theta<=1, r>=0, integral r=1, ||r||_infinity<=8/5,
    c>=0 bounded on I.                                         (15)

The algebraic statement even allows non-even measurable r,c. Its application
to the proven source tests includes all the fixed even trigonometric profiles
in this class. It proves consistency of THESE INEQUALITIES at sigma_MT, not
existence of a zero configuration saturating them.

Proof. Let g=r-r_theta, t=integral cr>=0 and d=B_theta(r,r)-lambda_1.
Equations (12)-(13) give d=B_theta(g,g)+lambda_theta-lambda_1>=0 and

    B_theta(cr,r)=lambda_theta t+B_theta(cr,g)
      >=lambda_1 t-sqrt(B_theta(cr,cr) B_theta(g,g)).

By (11), ||cr||_2^2<=(64/25)||c||_2^2. The coefficient obeys the EXACT bound

    (theta^-1+theta/2)(64/25)
      <=(10/9+9/20)(64/25)=4496/1125 <4.                       (16)

The first function is decreasing throughout [9/10,1]. Thus, more strongly,

    B_theta(cr,r) >=lambda_1 t-2||c||_2 sqrt(d).                (17)

Since sigma_MT>0, (17) implies (10). It does so for all choices simultaneously,
therefore collecting any number of these valid scalar tests or taking their
nonnegative combinations cannot force sigma>sigma_MT.

At the exact endpoint optimizer r=r_1, d=0 and
B_1(cr_1,r_1)=lambda_1 integral cr_1 for EVERY c: stationarity cancels every
additional diagonal-row main term exactly. Equation (16) shows this is not merely
an isolated optimizer accident; a whole bounded-profile class remains compatible.
Every normalized positive cosine r(x)=omega cos(omega x)/(2sin(omega/2)),
0<=omega<=pi, lies in this class, because its supremum is <=pi/2<11/7<8/5.
The omega=0 convention is r=1. Convex mixtures remain inside the class.

This is NOT a barrier for off-diagonal positive-matrix tests whose source side
contains additional correlations, profiles outside the stated supremum range,
other bandwidths, sharper finite inequalities, higher moments, other arithmetic
inputs or RH. A large numerical profile search would not prove this no-go;
(12)-(17) do. The necessary constraints do not assert that sigma_MT is the true
simple-zero fraction. Source PC and the variational benchmark are independently
identified inputs, not silently upgraded by this algebraic consistency argument.

## 8. Evidence, review debt and next action

The finite positive-matrix proof and the scalar saturation theorem are standalone
candidates. The full-source limits separately assume PC and the standard strip/
zero-count facts. An independent review must distinguish these scopes, audit
all normalization factors, shifted real margins, fixed-test limits and (16),
and not treat same-run checks as a receipt. Parent #117 is still queued.

The checker executes finite matrix identities, 59,808 exact integer/rational/
polynomial cases, shifted complex-kernel comparisons, alternate continuous
integrals and bounded scalar profile tests. It checks 126 finite models, not
actual zeta zeros. Quadrature and mpmath are not interval arithmetic. The tests
do not prove the universal analytic quantifiers or independently verify PC.

Next proposed task A-RH-OFFDIAG-0020: identify a source-evaluable off-diagonal
positive-matrix test (3), or a strictly sharper slack inequality, that retains
information not reduced to multiplying a profile by c. State its additional
simple-sector/arithmetic observable before claiming an improvement. The present
result prevents spending further rounds treating diagonal profile search alone
as evidence of a new record. No RH proof, new best proportion, literature-wide
novelty claim, independent-verifier status or mathematical-authority promotion
is asserted by this archive.
