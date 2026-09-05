# A-RH-AOC-0008 — anchor observability and a genuine hole-phase obstruction

Status: `solver_proof_candidate`; not independently verified.
Issue: #58. Actor/run: `openai-gpt-6-pro / run-20260905-rh-anchor-coverage-08`.
Date: 2026-09-05. Read-only parent: #54 / A-RH-SRE-0007, mathematical
commit `9715ec125e7dd357a464b5e2156e799017c75e8d`, with additive rendering
erratum at `ddb7b51cfbcc805110c35dcaf03f2c2bc65b0ec7`.

## 0. Result and route change

We connect separated retained simple-real anchors to a selected family of
non-real pairs by a positive **two-channel cross energy**. The real and
imaginary parts of a pair must be retained together. Their combined kernel
is a modulus square with no non-real zeros. Under explicit selected-center
separation, multiplicity and depth bounds, the signed defect controls this
cross energy by `Lambda*D/2`. Every selected pair lying within a fixed radius
of an anchor then pays a squared-depth cost. This bounds pair **mass**, not
merely the number of affected anchors as in the parent.

We also construct genuine finite, distinct exponential families with simple
fraction `2/3`, fixed-depth non-real mass fraction `1/3`, mean total mass one,
and `D/N -> 0`, for which all pairs lie far from every simple anchor. This
refutes automatic coverage from the single-scale hypotheses even with bounded
depths and separated pair centers. Unlike the parent's abstract clustered
example, it uses actual box exponentials. It is not a zeta-zero multiset.

The same example has short moment tending to `4/(3*alpha)`; at `alpha=3/4`
this exceeds the proposed ideal budget by `7/36`. Thus it does not refute the
two-scale strategy. It isolates its next obligation: quantify hole-phase
energy or prove coverage from **additional** source/two-scale information.
No unconditional zero proportion or RH statement follows.

## 1. Setup and exact multiplicity charge

Work in `L^2([-1/2,1/2])`, with `f_x(u)=exp(2*pi*i*x*u)` for real x.
A finite conjugation-invariant multiset has n simple real elements, distinct
non-simple real elements t_j with multiplicities m_j>=2, and distinct pairs
`t_p +/- i*a_p/(2*pi)` with a_p>0 and equal multiplicities b_p>=1. Put

\[
g_p=f_{t_p}\cosh(a_pu),\qquad h_p=-i f_{t_p}\sinh(a_pu),
\quad \|g_p\|^2-\|h_p\|^2=1.
\]

Define

\[
S=\sum_{i=1}^n f_{x_i}f_{x_i}^*,\quad
P=\sum_jm_j f_{t_j}f_{t_j}^*+2\sum_pb_pg_pg_p^*,\quad
N_-=2\sum_pb_ph_ph_p^*,\quad \mathsf A=S+P-N_-.
\]

Let nu=sum_j m_j+2 sum_p b_p, N=n+nu=tr(A), and

\[
D=n+\|\mathsf A\|_{HS}^2-2N.
\]

All traces take place on the finite span of the atoms. Let U=ran(P), let E
be the span of `(I-P_U)f_xi`, and let F=(U+E)^perp. Set

\[
\xi=\operatorname{tr}(P_US),\quad
\zeta=\operatorname{tr}((I-P_U)N_-),\quad
\zeta_F=\operatorname{tr}(P_FN_-),\quad Q=2P_U+P_E.
\]

Expanding the square, as in the parent (re-derived here), gives

\[
\boxed{D=\|\mathsf A-Q\|_{HS}^2+2(\nu-2\dim U)
 +2\xi+2\zeta+2\zeta_F+(n-\dim E).}                     \tag{1}
\]

Indeed tr(P_U A)=nu+xi+zeta, tr(P_F A)=-zeta_F, and
tr(Q^2)=4 dim U+dim E. Every displayed summand is nonnegative:
U is spanned by at most one vector per non-simple orbit, so nu>=2 dim U,
and dim E<=n. In particular `xi+zeta<=D/2`.

For distinct genuine exponentials, the non-simple real vectors and all g_p
are linearly independent. Expand each g_p into its two distinct exponentials;
a vanishing exponential polynomial on an interval has all coefficients zero
(by derivatives and the Vandermonde determinant). Thus dim U equals the
number of these orbits and

\[
\nu-2\dim U=\sum_j(m_j-2)+2\sum_p(b_p-1).
\]

Consequently the total mass of real elements with m_j>=3 and non-real pairs
with b_p>=2 is bounded by

\[
\boxed{M_{\rm high\ multiplicity}\le\tfrac32D,
\qquad M_{\rm repeated\ pairs}\le D.}                    \tag{2}
\]

Use `m<=3(m-2)` for integers m>=3 and `2b<=4(b-1)` for integers b>=2.
This is a mass/deletion statement, **not** a bound on the deleted operator
HS energy. The original defect and subspaces are retained after selecting
subfamilies; no claim that deletion decreases a signed defect is used.

## 2. Hyperbolic synthesis bounds with site-dependent depths

Let I be any 1/2-separated subfamily of simple real elements. Its synthesis
operator V has

\[
\|V\|_{op}^2\le B_s=14/3.
\]

Let J be a selected q-separated family of pair centers, with
`0<a_p<=A0`, `1<=b_p<=M`, q>0, and finite A0,M. Other pairs need not satisfy
these selected-family restrictions. Define synthesis columns

\[
G_J(:,p)=\sqrt{2b_p}\,g_p,\qquad
H_J(:,p)=\sqrt{2b_p}\,h_p.
\]

With `B_q=2+2/(3q^2)`, we have

\[
\boxed{\|G_J\|_{op}^2\le C_g=2M B_q\cosh^2(A_0/2),
\quad \|H_J\|_{op}^2\le C_h=2M B_q\sinh^2(A_0/2).}        \tag{3}
\]

For completeness, the real q-separated exponential bound B_q follows by
majorizing the indicator of [-1/2,1/2] with `2(1-|u|)_+`. Its Fourier kernel
is `2 sinc(t)^2`; the nonnegative row sum is at most
`2+(2/pi^2)*2 sum_{k>=1}(kq)^(-2)=B_q`.
For varying depths, expand cosh(a_p u) and sinh(a_p u) in power series.
The l-th term is multiplication by u^l followed by the real synthesis map
and a diagonal coefficient matrix. Since |u|<=1/2 and |a_p|<=A0, the
operator-norm series sums to cosh(A0/2) or sinh(A0/2), respectively. The
weight matrix has norm at most sqrt(2M). This proves (3), without requiring
a common depth or a finite alphabet.

A supplied local-center-count bound can replace explicit separation: if
there are at most K selected centers in every half-open interval of length
q, greedy coloring splits them into K q-separated classes. The same proof
then uses `K*B_q` in (3). Neither separation nor this local-count hypothesis
is inferred from D here.

## 3. Positive cross energy from the signed slack

Set

\[
\mathcal E_{I,J}=\|V^*G_J\|_{HS}^2+\|V^*H_J\|_{HS}^2.
\]

All columns of G_J lie in U. By (1),

\[
\|V^*G_J\|_{HS}^2\le C_g\xi,
\quad
\|V^*H_J\|_{HS}\le\sqrt{C_h\xi}+\sqrt{B_s\zeta}.
\]

The second inequality splits H_J into its U and U-perpendicular components;
`||(I-P_U)H_J||_HS^2<=zeta`. Hence

\[
\mathcal E_{I,J}\le(C_g+C_h)\xi+B_s\zeta
 +2\sqrt{C_hB_s\xi\zeta}.
\]

Let

\[
\boxed{\Lambda=\frac{C_g+C_h+B_s+
\sqrt{(C_g+C_h-B_s)^2+4C_h B_s}}2.}                       \tag{4}
\]

This is the top eigenvalue of the corresponding two-by-two real matrix.
Since xi+zeta<=D/2,

\[
\boxed{\mathcal E_{I,J}\le\tfrac12\Lambda D.}             \tag{5}
\]

It is a bound on a positive sum, despite the signed origin of D. No pointwise
positivity of the original complex squared-kernel sum is assumed.

At q=1/2, M=1, A0=log(2), a concrete value is

\[
\Lambda=\frac76(7+\sqrt{13})=12.3731431547\ldots.
\]

This is illustrative, not an optimized constant. Bounded selected depth and
Bessel constants remain essential in the proof.

## 4. What an anchor detects: both channels remove the real-part zeros

Let d=t_p-x_i be real. Evenness of the box gives the exact identity

\[
\boxed{|\langle f_{x_i},g_p\rangle|^2+
 |\langle f_{x_i},h_p\rangle|^2
=\left|\operatorname{sinc}\!\left(d+\frac{ia_p}{2\pi}\right)\right|^2
=\frac{\sin^2(\pi d)+\sinh^2(a_p/2)}{\pi^2d^2+a_p^2/4}.} \tag{6}
\]

At d=a_p=0 take the continuous value one. One way to see the first equality
is to write g,h as the even and odd combinations of the two complex
exponentials; their scalar correlations are conjugates. The parallelogram
identity then gives the modulus square. The second equality follows from
`|sin(x+iy)|^2=sin^2(x)+sinh^2(y)`.
For a_p>0, this kernel has no zero, even at a zero of the g-channel alone.

Let J_R consist of selected pair centers within distance R of at least one
anchor in I. One may choose a different anchor for each pair, and an anchor
may witness many pairs: (5) bounds the sum over **all** i,p. Thus

\[
2\sum_{p\in J_R}b_p
 \frac{\sinh^2(a_p/2)}{\pi^2R^2+a_p^2/4}\le\frac{\Lambda D}2,
\]

and, using sinh(a/2)>=a/2,

\[
\boxed{\sum_{p\in J_R}b_pa_p^2
\le\frac{\Lambda(4\pi^2R^2+A_0^2)}4D.}                  \tag{7}
\]

For 0<a0<=A0, let H_R be the mass of selected pairs in [a0,A0] with no anchor
within distance R. The total mass of the selected pairs in this depth range
obeys

\[
\boxed{M_{J,[a_0,A_0]}\le H_R+
\frac{\Lambda(4\pi^2R^2+A_0^2)}{2a_0^2}D.}              \tag{8}
\]

This counts both members with multiplicity. It improves the parent's
"number of affected anchors" to **covered pair mass**, under the explicitly
proved/supplied Bessel hypotheses. It does not assert H_R is small.
After deleting repeated pairs using (2), M=1 can be used for the remaining
selected family; any separation exceptions and all uncovered mass still
need their own ledger. Constants grow with the depth cap and radius.

## 5. Genuine hole-phase family: the coverage hypothesis is not automatic

Fix a=log(2) and k>=1. Take simple real elements

\[
0,1,\ldots,4k-1,
\]

and pairs

\[
p\pm\frac{ia}{2\pi},\qquad p=5k,\ldots,6k-1,
\]

each of multiplicity one. These are distinct genuine exponentials, not
abstract repeated unit vectors. There are N=6k elements, n=4k simple real
ones, and non-real mass 2k. All centers are integer spaced, all pair depths
are the fixed positive a, and the real-center window [0,6k) has mean total
mass one. Every pair center is at distance at least k+1 from every simple
anchor. For fixed R, eventually H_R/N=1/3.

Let `D_k(v)=sum_{p=0}^{k-1}exp(2*pi*i*p*v)`. For the pair block alone,

\[
D_{\rm pair}=\|\mathsf A_{\rm pair}\|_{HS}^2-4k
=4\int_{-1}^1(1-|v|)\sinh^2(av)|D_k(v)|^2\,dv.          \tag{9}
\]

The identity follows from its kernel `2 cosh(a(u-v))*D_k(u-v)` and
`integral (1-|v|)|D_k(v)|^2 dv=k`, the orthogonality of integer exponentials.
A translation of the pair block changes only a unimodular kernel factor.

For 0<=v<=1/2, use sinh(av)<=v sinh(a) and |D_k(v)|<=1/(2v).
For v=1-u with 0<=u<=1/2, use sinh(av)<=sinh(a) and
`|D_k(v)|<=min(k,1/(2u))`. Splitting the last integral at 1/(2k) yields

\[
\int_0^{1/2}\min(k^2u,1/(4u))\,du=\frac18+\frac14\log k.
\]

Accounting for the symmetric half gives

\[
D_{\rm pair}\le2\sinh^2(a)(1+\log k).
\]

The cross contribution of a simple integer site and a disjoint pair center
at integer distance h is `4 Re sinc(h+i*a/(2*pi))^2`. Since

\[
\operatorname{Re}\operatorname{sinc}(h+ic)^2
=\frac{\sinh^2(\pi c)(c^2-h^2)}{\pi^2(h^2+c^2)^2},
\]

it is negative here. The simple block by itself has zero defect. From the
signed inequality D>=0, we therefore obtain the all-k bound

\[
\boxed{0\le D_k^{\rm total}\le D_{\rm pair}
\le\frac98(1+\log k),\qquad \frac{D_k^{\rm total}}{6k}\to0.} \tag{10}
\]

The factor 9/8 uses sinh(log 2)=3/4 exactly. Thus one cannot infer from
D/N->0 and n/N=2/3 alone either coverage by simple anchors or vanishing
fixed-depth non-real mass. This remains false even after adding bounded
depth, separated centers and mean total mass one. The parent exact D=0
classification is not contradicted: D here is positive and need not tend
to zero without normalization. This is not a zero multiset of zeta.

## 6. The short-scale test sees this obstruction

Use the **actual continuous nested box space** `L^2([-alpha/2,alpha/2])`,
0<alpha<1 fixed, with normalized atoms `alpha^(-1/2) exp(2*pi*i*z*u)`.
No independent artificial depth-response channel is introduced. Its moment is

\[
\|\mathsf A_{\alpha}\|_{HS}^2
=\sum_{z,w}\operatorname{sinc}(\alpha(z-w))^2.
\]

For a real integer block of length m its moment divided by m tends to
1/alpha. For a homogeneous depth-a pair block of length k the moment is

\[
\frac4{\alpha^2}\int_{-\alpha}^{\alpha}
 (\alpha-|v|)\cosh^2(av)|D_k(v)|^2\,dv,
\]

whose quotient by k tends to 4/alpha. To justify both limits, the periodic
Fejer kernel |D_k|^2/k has integral one and its mass away from integers tends
to zero (bounded by `1/(k sin^2(pi*v))` there). Periodize the compactly
supported continuous weight. At the only contributing integer, zero, its
value is alpha; the other integers are outside the support for alpha<1.
This proves the stated limits, not just a numerical extrapolation.

The two blocks are separated by at least k+1. Their cross term is O_{a,alpha}(1):

\[
|\operatorname{sinc}(\alpha(h+ia/(2\pi)))|^2
\le\frac{\cosh^2(\alpha a/2)}{\pi^2\alpha^2 h^2},
\]

and there are 4k^2 simple/pair choices. Its normalization by N therefore
vanishes. Adding the two blocks gives

\[
\boxed{\frac{\|\mathsf A_{\alpha}\|_{HS}^2}{6k}
\longrightarrow\frac4{3\alpha}.}                        \tag{11}
\]

The difference from the previously targeted ideal moment budget is

\[
\frac4{3\alpha}-\left(\frac1\alpha+\frac\alpha3\right)
=\frac{1-\alpha^2}{3\alpha}>0.
\]

In particular at alpha=3/4 the limit is 16/9, the budget is 19/12, and the
excess is exactly **7/36**. The countermodel meets the long-scale budget only
asymptotically (4/3+o(1)), and violates the shorter fixed-scale budget by a
positive limiting margin. It is therefore an obstruction to single-scale
coverage, not to the entire two-scale strategy.

## 7. Source-facing next step and non-implications

The cross-energy theorem gives a rigorous conditional bridge from the
simple sector to **covered** pairs. Its hole term is indispensable under
the current single-scale information. A productive successor should estimate
short-scale energy of general hole phases, or obtain a source-specific
coverage/local-density statement with exceptional-energy control. It should
not simply reassert H_R=o(N) from D=o(N), which (10) disproves.

This note does not prove a decomposition of every near-extremizer into the
example's three phases. Different local depths, overlapping phases, moving
local lattice phases, arbitrary center clusters and genuine source weights
remain unclassified. Nor does it prove pair separation for zeta zeros,
uniformity as A0 or R grows, weighted-to-unweighted transfer, actual
arithmetic near saturation, a completed two-scale budget, a new zeta-zero
proportion or RH. High-multiplicity mass control is not discarded HS-energy
control. No literature-wide novelty or independent verification is claimed.

## 8. Reproduction

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_anchor_coverage.py --samples 120 --output validation.json
```

The code is self-contained and uses Python, NumPy and mpmath. It checks the
cross identity, Bessel/slack/coverage inequalities in 120 finite exponential
families, including 40 with an unselected deeper pair; exact integer
multiplicity costs; 60-digit finite phase sums for k=1,...,256 on a powers-of-two
grid; independent small direct double sums; and the pair-block integral.
Gauss-Legendre and mpmath integration are not interval certificates. Exact
integer checks, approximate arithmetic and analytic candidate proofs are
kept distinct. Actual output is in validation.json.

All parent hash pointers were checked. Direct git access failed DNS; GitHub
persistence is via the connected API. No complete repository checkout/CI,
bundled backend inventory/record runner, upstream Lean build, or independent
verifier was executed. Local Python/backend availability was checked
explicitly; package-local JSON, path and hash validation is separate.
