# A-RH-CTP-0005: centered transfer, sharp Toeplitz contraction, and perturbation ledger

Status: `solver_proof_candidate`; not independently verified.
Issue: #45. Parent: #40; parent verification queue: #43 (no receipt at startup).
Actor/run: `openai-gpt-6-pro / run-20260905-rh-centered-transfer-05`.
Date: 2026-09-05. Read-only parent commit: `340d6c4a3f2101d2cd08834ee3fe9cc9aed8f202`.

This is an additive successor, not a replacement of the frozen parent. The
mathematical claims below concern explicit finite Fourier models. They do not
establish a new bound for actual zeta zeros. Novelty outside this project has
not been established.

## 1. Model and the parent inequality

Let P>=2, s_j=(j-(P-1)/2)/P, and f_p(j)=P^(-1/2) exp(2 pi i p s_j).
The columns f_p are an orthonormal Fourier basis (column phases are harmless).
Every residue carries a mass m_p in {0,1,2}, with sum m_p=P. If a_p>0 it is a
multiplicity-one reflection pair and m_p=2. Otherwise the site is tangent.
A depth-zero pair is counted as a tangent load two, not as two simple points.
Define U_p=f_p f_p*, C_a=diag(cosh(a s_j)), S_a=diag(sinh(a s_j)), and

\[
G=\sum_p m_p(C_{a_p}U_pC_{a_p}-S_{a_p}U_pS_{a_p}),\qquad
G_0=\sum_p m_pU_p,\qquad K=G-G_0.
\]

Both G and G0 are Hermitian Toeplitz matrices with physical-row diagonal one;
K is Hermitian Toeplitz with zero diagonal. This follows entrywise from
cosh(x)cosh(y)-sinh(x)sinh(y)=cosh(x-y). Let

\[
s=P^{-1}\#\{p:m_p=1\},\quad x=s-2/3,\quad
\Delta=\sum_p(4m_p-m_p^2)-4\operatorname{tr}G+\|G\|_F^2.
\]

Since sum m_p^2/P=2-s, exact expansion gives

\[
\Delta/P=\|G-I_P\|_F^2/P-1/3+x,
\qquad
\Delta=\|K\|_F^2-2\operatorname{tr}((2I-G_0)K).                 \tag{1}
\]

Here and below a star denotes adjoint. For a pair at p and q!=p, its
interaction with U_q is

\[
J_{P,a}(p-q)=\frac{4\sinh^2(a/2)}{P^2}
\frac{\cosh(a/P)\cos(2\pi(p-q)/P)-1}
{[\cosh(a/P)-\cos(2\pi(p-q)/P)]^2}.                         \tag{2}
\]

This is obtained by summing the two geometric progressions for exp(+-a s_j).
For 0<a<=2pi it is negative: with the shorter circular angle t in (0,pi],
nonpositive cos(t) is immediate; otherwise 0<a/P<=t<pi/2 and
cosh(a/P)cos(t)<=cosh(t)cos(t)<1. The last inequality follows from
tanh(t)-tan(t)<0. At a=0 the pair difference is zero.
Since the coefficients of 2I-G0 are zero on pair sites and nonnegative
elsewhere, (1) yields the parent estimate, now re-derived in this notation:

\[
0\le\|K\|_F^2\le\Delta\quad\text{if all }a_p\in[0,2\pi].       \tag{3}
\]

For arbitrary finite depths retain the explicit charge

\[
B=\sum_{p:a_p>2\pi}\sum_{q\text{ non-pair}}
       (2-m_q)(J_{P,a_p}(p-q))_+,
\qquad \|K\|_F^2\le\Delta+2B.                              \tag{4}
\]

No estimate that B is small for actual zeta zeros is assumed. The finite
mean-one grid, mass bound two, and multiplicity-one pair assumptions matter.

## 2. Sharp zero-diagonal Toeplitz subcompression

Let T be any zero-diagonal Hermitian P-by-P Toeplitz matrix with entries
T_jk=t_(j-k), and let R select d consecutive rows, 1<=d<=P. Then

\[
\|T\|_F^2=2\sum_{n=1}^{P-1}(P-n)|t_n|^2,\qquad
\|RTR^*\|_F^2=2\sum_{n=1}^{d-1}(d-n)|t_n|^2.
\]

For n>=1, (d-n)/(P-n) is nonincreasing in n. Consequently

\[
\boxed{\|RTR^*\|_F^2\le\sigma_{P,d}\|T\|_F^2,
\quad\sigma_{P,d}=\frac{d-1}{P-1}\le\alpha=\frac dP.}          \tag{5}
\]

For d>=2 equality is attained by a matrix supported on the first upper and
lower diagonals. Thus this bound is sharp in the stated Toeplitz class.
For d=1 both sides of the compressed zero-diagonal problem are zero.
A putative factor alpha^2 is false: P=100,d=75 gives 74/99>9/16.
The constant need not be sharp in the narrower class of realizable pair
corrections; no optimality in that class is asserted.

Unit-atom short normalization remains G_alpha=RGR*/alpha and similarly for
G0. Applying (5) to K improves the parent general-contraction estimate to

\[
\boxed{\frac{\|G_\alpha-G_{0,\alpha}\|_F}{\sqrt P}
\le\frac{\sqrt{\sigma_{P,d}}}{\alpha}
       \sqrt{(\Delta+2B)/P}
\le\frac1{\sqrt\alpha}\sqrt{(\Delta+2B)/P}.}                 \tag{6}
\]

This is not a claim about resampling between actual zeta compressions. It is
an exact consecutive-row statement on one explicit master Fourier model.

## 3. Center first, then compare: a larger explicit ideal gain

The common physical-row diagonal of G_alpha and G0_alpha is I_d/alpha.
Removing it before applying the triangle inequality avoids spending the
operator error on a component which is exactly equal on the two sides.
In particular

\[
\|G_\alpha-I_d/\alpha\|_F^2/P
=\|G_\alpha\|_F^2/P-1/\alpha.                              \tag{7}
\]

For the tangent comparison, with mhat(n)=P^(-1) sum_p m_p exp(2pi i pn/P),

\[
\frac{\|G_{0,\alpha}\|_F^2}{P}
=\frac1\alpha+\sum_{n=1}^{P-1}F_\alpha(n/P)|\widehat m(n)|^2,
\quad
F_\alpha(t)=\frac{(\alpha-t)_++(\alpha-1+t)_+}{\alpha^2}.     \tag{8}
\]

The identity follows by counting ordinary row differences n and their
conjugates P-n in the partial Fourier section. For 1/2<alpha<1,
F_alpha>=f_alpha=(2alpha-1)/alpha^2. Parseval and the mass assumptions give
sum_(n!=0)|mhat(n)|^2=1-s=1/3-x. Therefore

\[
\|G_{0,\alpha}-I_d/\alpha\|_F^2/P
\ge f_\alpha(1/3-x).                                      \tag{9}
\]

Assume now all depths are <=2pi and the two ideal moment budgets

\[
\|G\|_F^2/P\le4/3,\qquad
\|G_\alpha\|_F^2/P\le1/\alpha+\alpha/3.                   \tag{10}
\]

Equations (1),(3) imply 0<=Delta/P<=x. Combining (6)--(10) gives

\[
\sqrt{f_\alpha(1/3-x)}
\le\sqrt{\alpha/3}+\sqrt{x/\alpha}.                        \tag{11}
\]

At alpha=3/4, with P divisible by four, squaring nonnegative sides yields

\[
\frac{20}{9}x+\frac2{\sqrt3}\sqrt x\ge\frac5{108}.
\]

**Theorem (conditional finite-model gain).** Under exactly the assumptions
above at alpha=3/4,

\[
\boxed{s\ge\frac23+\epsilon_1,\qquad
\epsilon_1=\frac{(\sqrt{106}-9)^2}{1200}
=0.001398881218528328596\ldots.}                            \tag{12}
\]

The resulting floor is 0.668065547885194995... . The parent gain was
0.000186299466336929...; the gain increment is about 7.5088 times larger.
This is an improvement of a sufficient inequality *inside this model*, not
an improved zeta-zero record, and it remains below the source-reported
optimized 0.6725007... proportion. No sharpness claim is made for (12).
For intermediate bookkeeping, centering alone without (5) gives the weaker
gain (sqrt(23/72)-1/2)^2/4=0.001062569796... .

For general alpha the sufficient scalar inequality is

\[
(f_\alpha+1/\alpha)x+\frac2{\sqrt3}\sqrt x
\ge(f_\alpha-\alpha)/3.
\]

We retain the rational support 3/4 rather than claiming an optimized support
or a source-level gain. Nonintegral row counts require their own rounding
ledger or the exact ratio alpha=d/P.

## 4. Dimension-independent stability of a supplied near-lattice matching

This section does not derive a lattice matching from a scalar defect.
Assume such a matching has been supplied with one orbit per residue. Replace
the real lattice position p by p+e_p; keep its mass and depth fixed. Suppose
|e_p|<=h, 0<=a_p<=A and m_p<=2. Define

\[
\mathcal G(e)_{jk}=P^{-1}\sum_p m_p
 e^{2\pi i(p+e_p)(s_j-s_k)}\cosh(a_p(s_j-s_k)).
\]

It is Hermitian Toeplitz with diagonal one when sum m_p=P. Let
E=sum_p m_p e_p^2/P. Then

\[
\boxed{\|\mathcal G(e)-\mathcal G(0)\|_F/\sqrt P
\le C(A,h)\sqrt E,\quad
C(A,h)=\sqrt2\pi e^A(e^{\pi h}+1).}                        \tag{13}
\]

Proof: let T_+(e),T_-(e) have columns
f_p exp((+-a_p+2pi i e_p)s). Expanding the exponential as
sum_k diag(s^k) F diag((+-a+2pi i e)^k)/k!, with ||F||=1 and |s_j|<=1/2,
gives ||T_+(e)||,||T_-(e)||<=exp(A/2+pi h). After multiplying columns by
sqrt(m_p), the bounds are sqrt(2)exp(A/2+pi h), and at e=0 they are
sqrt(2)exp(A/2). Meanwhile |exp(2pi i e_p s)-1|<=pi|e_p| gives the
Hilbert--Schmidt difference of either synthesis family at most
pi exp(A/2)(sum m_p e_p^2)^(1/2). Finally write

\[
\mathcal G(e)=\tfrac12[T_+(e)MT_-(e)^*+T_-(e)MT_+(e)^*]
\]

and expand the two product differences, placing the difference factor in
Hilbert--Schmidt norm and the other factor in operator norm. This gives (13).
There is no factor growing with P. However C grows exponentially in A. This
estimate alone is not uniform for growing normalized depths or mass collisions.
Nor does it contradict the parent's slow-strain obstruction to one global
matching; its hypothesis is a given matching, possibly to be used locally.

## 5. Taper loss: when edge size really does control energy

Let X be zero-diagonal Hermitian Toeplitz, R select d<P consecutive rows, and
D=diag(psi_j), 0<=psi_j<=1. Suppose psi differs from one at no more than r
rows. Counting entries on each ordinary diagonal gives

\[
\boxed{\|RXR^*-DRXR^*D\|_F^2
\le\frac{2r}{P-d+1}\|X\|_F^2.}                            \tag{14}
\]

Indeed, for any offset 1<=n<d, at most 2r of its d-n pairs meet changed rows.
Their factors satisfy (1-psi_j psi_k)^2<=1; and P-n>=P-d+1. Sum over both
diagonal directions and compare with the full Toeplitz norm formula.

With kappa=P^(-1)sum_j psi_j^2>0, unit-atom taper normalization is kappa^(-1).
Equations (5),(14) imply

\[
\frac{\|\kappa^{-1}DRXR^*D-\alpha^{-1}RXR^*\|_F}{\sqrt P}
\le\left[\frac1\kappa\sqrt{\frac{2r}{P-d+1}}
 +(\kappa^{-1}-\alpha^{-1})\sqrt{\sigma_{P,d}}\right]
 \frac{\|X\|_F}{\sqrt P}.                                  \tag{15}
\]

At fixed alpha<1, if r/P tends to zero and ||X||_F/sqrt(P) is bounded, the
right side tends to zero. This is a rigorous finite-model ramp estimate.
It uses Toeplitz structure, not edge measure alone. Without that structure,
a Hermitian matrix with its only entries at (0,1),(1,0) can lose all energy
when one edge row is deleted. The checker retains this counterexample.
The estimate is also not uniform in the endpoint regime d/P->1.

For a tapered full matrix with original diagonal one, the common diagonal is
D^2/kappa, not I_d/alpha. Its squared Frobenius norm divided by P is

\[
 c_\psi=\frac{\sum_j\psi_j^4}{P\kappa^2}.                  \tag{16}
\]

Centering subtracts c_psi from the normalized total second moment exactly.
A claimed tapered source budget must use this value and the same kappa.

## 6. Perturbed budget with a place for every error

Let the displaced matrix \(\mathcal G(e)\) satisfy the centered upper budgets

\[
\|\mathcal G(e)-I\|_F^2/P\le1/3+u_1,\qquad
\|\mathcal G(e)_\alpha-I_d/\alpha\|_F^2/P\le\alpha/3+u_2,
\quad u_1,u_2\ge0.
\]

Let r0 be any proved upper bound for
||mathcal G(e)-mathcal G(0)||_F/sqrt(P), and b=B/P the high-depth charge of the
snapped matrix. Define U1=u1+2r0 sqrt(1/3+u1)+r0^2. Apply (1),(4) to the
snapped matrix and (5) to both Toeplitz differences. Then

\[
\boxed{\sqrt{f_\alpha(1/3-x)}
\le\sqrt{\alpha/3+u_2}
 +\frac{r_0+\sqrt{x+U_1+2b}}{\sqrt\alpha}.}                 \tag{17}
\]

The square-root domains follow from s<=1 and (4). For nonzero errors x may
be negative; we do not assume x>=0 in (17). If the actually observed short
matrix differs from the centered box model by at most tau sqrt(P) in
Hilbert--Schmidt norm, add tau to the right side. Equation (15) supplies one
conditional finite-model source of such a tau, not the complete zeta error.

This closes a quantitative *given-matching* stability implication. Still
missing are extraction of the matching for actual zeros, treatment of large
local multiplicities/collisions, and an arithmetic bound for b. None is
inferred from the displayed estimate.

## 7. A lattice-free projection remainder suggested by the new source

This is a separate finite Hilbert-space statement. It is not substituted for
the tangent G0 in the preceding theorems. Let H=U direct-sum E direct-sum F
be an orthogonal finite-dimensional decomposition; write u=dim(U), e=dim(E).
For a self-adjoint A and an integer n>=e assume

\[
\operatorname{tr}(P_U A)\ge2u,\qquad
\operatorname{tr}(P_F A)\le0.
\]

Define Q=2P_U+P_E and D=n+||A||_HS^2-2 tr(A). Directly expanding the square,
using tr(Q^2)=4u+e, gives the exact identity

\[
\boxed{D=\|A-Q\|_{HS}^2
 +2[\operatorname{tr}(P_UA)-2u]
 -2\operatorname{tr}(P_FA)+(n-e)\ge\|A-Q\|_{HS}^2.}          \tag{18}
\]

There is no lattice or depth bound in (18). The hypotheses can be checked
for a finite signed atom family: simple real atoms f_i have norm one;
non-simple real atoms also have norm one and weights at least two; each
conjugate pair contributes 2m(gg*-hh*) with ||g||^2-||h||^2=1. Take U to
span the non-simple real atoms and the g vectors, and U+E to additionally
span the simple atoms. Projection of h can only increase the lower bound
for tr(P_U A); on F only the negative h contribution remains; adding n
simple vectors increases dimension by at most n. Thus the three displayed
hypotheses follow, and tr(A) equals the total atom mass.

Lamzouri's September 2 preprint uses these subspaces in Proposition 2.1.
Equation (18) retains the discarded squares as a basis-independent remainder.
It is an elementary solver derivation, not an asserted new literature theorem
or an independent validation of that paper. The source uses its own Fourier
normalization; identifying its quadratic kernel sum with ||A||_HS^2 is a
separate source dictionary and is not silently imported into our grid model.

In particular, (18) offers a possible all-depth *projection* comparison, but
Q has data-dependent spectral subspaces, not integer lattice locations.
No bound for compressions of Q analogous to the occupancy floor (9) has
been proved here. This is the precise remaining obligation for that route.

## 8. Reproduction and handoff

Run in this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_centered_transfer.py --samples 160 --output validation.json
```

The record includes rational subchecks, a 70-decimal evaluation of the radical,
160 seeded finite configurations, contraction sharpness, displacement/taper
checks, normalization, the projection identity (18), and two explicit scope guards. The analytic arguments
in this file are not proved by those sampled tests. No Lean build or isolated
mathematical verifier was run. Full repository CI and the bundled computation
inventory/record scripts were not run: the container has no direct GitHub DNS
access, so this is a connector-based package rather than a full checkout.
Selected local Python/NumPy/mpmath versions were live checked. Package-local
hashes and the computation handoff structure were validated separately.

The new source note is context only; see source-update.md. Existing frozen
files, main, Project heads and shared results are untouched. The next useful
source task is a local near-lattice extraction with a weighted displacement
bound and an explicit exceptional-operator ledger, rather than another
unqualified global depth-classification assertion.
