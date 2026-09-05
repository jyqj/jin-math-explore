# A-RH-WTP-0004 — weighted-trace audit and variable-depth operator transfer

Status: solver proof candidate; this checkpoint is not independently verified.
Issue: #40 (sequential successor to #32).
Actor/run: `openai-gpt-6-pro / run-20260905-rh-weighted-trace-04`.
Date: 2026-09-05.
Read-only predecessor: `95e3e56329cc124166ed80cfd25628bedd845d35`.

## 0. Outcome and boundaries

This checkpoint both corrects and advances the preceding route.

* The finite weighted prime trace has an exact prime-power expression and a
  variation-based upper bound. It does not require a new prime-pair correlation
  theorem at this algebraic stage. The microscopic localized lower estimate
  sought by the predecessor is **not** proved here.
* A finite set of pairs has the previously recorded additive depth identity.
  It cannot be exchanged with an infinite pair sum without further control.
  A homogeneous pair lattice is invisible to every trace-class observable of
  its signed frame operator. An explicit example exhibits unequal cutoff-order
  limits. Weighted traces may still add constraints beyond the two scalar
  moments, but their purported universal depth identification is withdrawn.
* There is a more direct positive route: compare operators rather than recover
  the entire depth field. On an exact master lattice, arbitrary site-dependent
  depths in `[0,2*pi]` satisfy `||G-G0||_F^2 <= Delta`, even in a mixed tangent
  `0/1/2` background. No finite depth alphabet, minimum depth, or homogeneous
  depth conclusion is required.
* With critical mean load one and the ideal two moment budgets, this gives the
  explicit conditional model bound `simple proportion >= 0.666852966133...`.
  This is **not** an unconditional zeta-zero bound or a new published record.

All claims below are solver derivations. Numerical checks support the finite
identities but do not independently prove these statements. No predecessor
artifact is edited. The exact-grid, multiplicity, normalization, cutoff and
source-transfer limitations are part of the statements, not optional caveats.

## 1. Pinned source dictionary

Source: `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`.
The definitions used are `zeta23/Zeta23/PrimeSideA/Defs.lean` (blob
`33ddda1630f077a612cd639d28b7d43b183a53a4`) and `Zeta23/Taper.lean` (blob
`b7dd4ff5b00d71035db1d3311007d19148004f78`). Their contents, not a clean Lean
build, were checked in this run.

Use the paper Fourier convention

\[
\widehat\phi(z)=\int_{\mathbb R}\phi(u)e^{izu}\,du,
\qquad C_\phi(y)=\int\phi(u)\phi(u+y)\,du.
\]

Here `phi` is real, even, supported on `[-L/2,L/2]`; for the source-facing
formula take `phi in C_c^2`, `|phi|<=1`, and `X=exp(L)`. Write

\[
 A_0=\int\phi^2,\quad B_0=\int(\phi')^2,\quad
 \tau_k=T+\frac{2\pi k}{L},\quad 0\le k<d.
\]

The pinned prime-side matrix is

\[
G_{kl}=\int\widehat\phi(t-\tau_k)\widehat\phi(t-\tau_l)
        [\mu(t)+\Pi_X(t)+P_X(t)]\,dt,
\]

where

\[
P_X(t)=-\frac1\pi\sum_{2\le n\le X}
           \frac{\Lambda(n)}{\sqrt n}\cos(t\log n).
\]

`G` here is unnormalized. The source's `G/L` and `G/(A0*L)` must not be
interchanged. Sections 5–7 below introduce a **different**, explicitly
normalized finite Fourier model. No equality with actual zeta compressions is
silently asserted.

## 2. Exact finite weighted prime trace

For arbitrary real finite weights `w_k`, set

\[
H_w(z)=\sum_{k=0}^{d-1}w_k\widehat\phi(z-\tau_k)^2,
\qquad S_w(y)=\sum_{k=0}^{d-1}w_ke^{i\tau_k y}.
\]

Then the exact prime-side expression is

\[
\boxed{
\begin{aligned}
\mathcal T_w:=\sum_k w_kG_{kk}
={}&\int H_w(t)[\mu(t)+\Pi_X(t)]\,dt\\
 &-2\sum_{2\le n\le X}\frac{\Lambda(n)}{\sqrt n}
        C_\phi(\log n)\operatorname{Re}S_w(\log n).
\end{aligned}}
\tag{2.1}
\]

Proof: finite sums may be exchanged with the convergent integrals. Real
evenness and Parseval give

\[
\int\widehat\phi(r)^2\cos(ry)\,dr=2\pi C_\phi(y),
\qquad \int\widehat\phi(r)^2\sin(ry)\,dr=0.
\]

Translation by `tau_k` supplies `cos(tau_k*y)`; multiplication by the `-1/pi`
in `P_X` supplies the factor `-2`. This checks both the sign and normalization.
The gamma/pole contribution in (2.1) is retained exactly; no microscopic
asymptotic or positivity assertion about it is being made.

For `w_k=(tau_k-c)^2`, let `S_0(y)=sum exp(i*tau_k*y)`. Then

\[
\boxed{S_w(y)=(-i\partial_y-c)^2S_0(y)
=-S_0''(y)+2icS_0'(y)+c^2S_0(y).}
\tag{2.2}
\]

Thus a quadratic weight differentiates a *finite exponential sum*. One must
not replace it by a zero-selecting hard ordinate cutoff. Conditional on the
source explicit formula, the zero-side quantity is `sum_rho m_rho H_w(z_rho)`
over **all** zeros, where `z_rho=gamma-i(beta-1/2)`. It is not automatically a
sum only over the zeros closest to `c`.

### A usable, but deliberately coarse, prime-part bound

Put

\[
V_w=|w_{d-1}|+\sum_{k=0}^{d-2}|w_{k+1}-w_k|.
\]

Abel summation with geometric partial sums proves

\[
|S_w(y)|\le V_w\min\left(d,\frac1{|\sin(\pi y/L)|}\right).
\tag{2.3}
\]

At a grid resonance interpret the minimum by the finite bound `d`. Suppose
`L>=2 log 2` and a constant `C_psi` satisfies
`sum_(n<=u) Lambda(n) <= C_psi*u` for `1<=u<=X`. Since
`|C_phi(y)| <= (L-|y|)_+`, the absolute value of the prime term in (2.1) obeys

\[
\boxed{
|\mathcal P_w|\le
2C_\psi V_w\left[
\frac{L^2}{\log2}X^{1/4}+L\sqrt X\right].}
\tag{2.4}
\]

To prove this, split `y=log n` at `L/2`. On the lower half,
`(L-y)/sin(pi*y/L) <= L^2/(2 log 2)`; on the upper half it is at most `L/2`.
Partial summation gives `sum_(n<=Y) Lambda(n)/sqrt(n) <= 2 C_psi sqrt(Y)`.
The endpoint `y=L`, if present, contributes zero because `C_phi(L)=0`.
This proves (2.4), without replacing an oscillatory sum by a guessed main term.
For a centered quadratic weight over a grid of radius `H`, `V_w<=3H^2`.

The estimate need not be sharp. In the checker's small example the prime term
is about `14.89` and the coarse bound is about `5626`. It does **not** establish
the predecessor's desired localized lower trace bound. It identifies exactly
which finite prime sum and which weight variation that task must control.

## 3. Why an additive pair-depth identity does not give a universal observable

Let `phi` be real even in `H_0^1([-L/2,L/2])`, and set `D=-i d/du`. For one
pair with real ordinate `t` and physical depth `delta`, put

\[
x=\phi e^{itu}\cosh(\delta u),\qquad
 y=-i\phi e^{itu}\sinh(\delta u).
\]

The predecessor's identity is valid:

\[
\|(D-c)x\|_2^2-\|(D-c)y\|_2^2
 =A_0[(t-c)^2-\delta^2]+B_0.
\tag{3.1}
\]

The cross terms cancel pointwise by `cosh^2-sinh^2=1`. A finite collection may
be summed safely. This checkpoint does not retract (3.1).

Now take a complete orthonormal Fourier basis `(e_p)` of the support interval
and a fixed depth `delta`. Multiplication by `phi*cosh(delta*u)` and
`-i*phi*sinh(delta*u)` is bounded. Strong convergence of the Fourier projections
therefore gives

\[
\boxed{
2\sum_{p\in\mathbb Z}
(|\phi\cosh(\delta u)e_p\rangle\langle\phi\cosh(\delta u)e_p|
-|\phi\sinh(\delta u)e_p\rangle\langle\phi\sinh(\delta u)e_p|)
=2M_{\phi^2}.}
\tag{3.2}
\]

The same operator is obtained at `delta=0`. Consequently **every trace-class
observable** of this signed frame operator, including any finite diagonal
quadratic frequency weight, is identical for the two homogeneous phases.
This conclusion follows by approximation of a trace-class operator by finite
rank operators and uniform boundedness of the strong partial sums.

The full frequency-square operator `(D-c)^2` is unbounded and not trace class.
Equation (3.2) cannot be inserted into its trace by an unproved exchange of
limits. Likewise, derivative test functions which remain in the same support
space cannot distinguish two exactly equal forms on that space. A different
support or arithmetic input may change the question; it is not supplied by
renaming this observable.

### Explicit noncommuting cutoff orders

Take `L=2*pi`, `phi(u)=cos(u/2)` on `[-pi,pi]`, extended by zero. This taper is
in `H_0^1`, and is used only for the cutoff example, not as the source's flat
smooth taper. Its Fourier transform is

\[
 h(z)=-\frac{\cos(\pi z)}{z^2-1/4}
\]

with removable singularities. Fix `0<delta<1/2` and define

\[
Q_{M,K}=\frac1{2M+1}\sum_{p=-M}^{M}\sum_{k=-K}^{K}
\frac{k^2}{\pi}\left[\operatorname{Re}h(p-k-i\delta)^2-h(p-k)^2\right].
\tag{3.3}
\]

The divisor `2M+1` counts pairs, not individual zeros. For fixed `M`, weighted
Parseval and (3.1) give

\[
\lim_{K\to\infty}Q_{M,K}=-2\pi\delta^2.
\]

For fixed `K`, (3.2) gives `lim_(M->infinity) Q_(M,K)=0`. Hence

\[
\boxed{
\lim_{M\to\infty}\lim_{K\to\infty}Q_{M,K}=-2\pi\delta^2,
\qquad
\lim_{K\to\infty}\lim_{M\to\infty}Q_{M,K}=0.}
\tag{3.4}
\]

At `delta=0.2`, the first value is `-0.251327412287...`. The deterministic
checker illustrates both orders separately. The distinction is analytical,
not a floating-point artifact. These are artificial pair lattices, not zeta
zeros, and therefore do not contradict any theorem about zeta.

### Normalized depth and the missing localization step

For a **finite selected** zero block the old conditional bound was
`sum n_p delta_p^2 / N <= (H^2+epsilon)/2`. Its dimensionless form is

\[
\frac1N\sum_p n_p a_p^2\le
\frac{(LH)^2+L^2\epsilon}{2},\qquad a_p=L\delta_p.
\tag{3.5}
\]

Thus `epsilon=o(1)` does not suffice for dimensionless depth collapse; the
corresponding error must be `o(L^-2)` and, for this particular bound, the
block radius must be `o(1/L)`. Sharper subtraction of horizontal variance
might avoid the radius condition, but is an additional theorem.

The previous single-interior-vector weighted-tail estimate also does not
control the sum of **external zero contributions** to a localized trace.
Nor does small discarded zero count alone imply small weighted trace norm.
These are separate obligations. Weighted traces remain a possible tool; their
automatic identification of a new usable depth channel is not established.

## 4. Replace depth identification by operator comparison

We now work entirely in the finite ideal master-lattice model. Let `P>=2`,

\[
f_p(j)=P^{-1/2}e^{2\pi i pj/P},\quad U_p=|f_p\rangle\langle f_p|,
\quad s_j=(j-(P-1)/2)/P.
\]

At a set of residues `A`, place one multiplicity-one reflection pair with
arbitrary depth `a_p>=0`. At all other residues use a tangent load
`r_q in {0,1,2}`. Set `m_p=2` on `A` and `m_q=r_q` outside it. Define

\[
G_0=\sum_p m_pU_p,\qquad
K_p=2(C_{a_p}U_pC_{a_p}-S_{a_p}U_pS_{a_p})-2U_p,
\quad K=\sum_{p\in A}K_p,\quad G=G_0+K.
\]

Each `K_p` has zero trace and zero diagonal in the physical row coordinates.
Define the count defect using precisely the site budget of this model:

\[
\Delta=\sum_p(4m_p-m_p^2)-4\operatorname{tr}G+\|G\|_F^2.
\]

Since `G0` saturates that tangent budget, exact expansion gives

\[
\boxed{\Delta=\|K\|_F^2-2\operatorname{tr}((2I-G_0)K).}
\tag{4.1}
\]

This is valid for continuously varying depths and has no alphabet assumption.
It does not assert that the cross term has a favorable sign in all cases.

### Atomwise sign: variable moderate depths need no classification

For `q!=p`, put `n=p-q mod P`, `theta=2*pi*min(n,P-n)/P`, and `x=a/P`.
The geometric-sum calculation from the predecessor gives

\[
J_{P,a}(n):=\langle U_q,K_p\rangle_F
=\frac{4\sinh^2(a/2)}{P^2}
 \frac{\cosh(a/P)\cos\theta-1}{(\cosh(a/P)-\cos\theta)^2}.
\tag{4.2}
\]

For `0<a<=2*pi`, this is strictly negative. If `cos(theta)<=0`, this is
immediate. Otherwise `0<x<=theta<pi/2`, and
`cosh(x)cos(theta)<=cosh(theta)cos(theta)<1`; the last strict inequality
follows by differentiating `log(cosh(theta)cos(theta))`, whose derivative is
`tanh(theta)-tan(theta)<0`. At `a=0`, `K_p=0` and `J=0`.

Since `(2I-G0)` has coefficient zero on every pair site and nonnegative
coefficients outside it,

\[
\operatorname{tr}((2I-G_0)K)
=\sum_{q\notin A}(2-r_q)\sum_{p\in A}J_{P,a_p}(p-q)\le0.
\]

**Theorem 4.1 (finite mixed variable-depth operator coercivity).** If every
pair depth lies in `[0,2*pi]`, then

\[
\boxed{\|G-G_0\|_F^2\le\Delta.}
\tag{4.3}
\]

The constant is one, independent of `P`, the number of distinct depths, and
the minimum positive depth. This is stronger for the intended *operator
transfer* than first proving that a depth field is locally constant. It makes
no such classification claim and does not contradict the earlier relaxed
moment-channel rank obstruction.

If **every** residue is a pair site, `G0=2I`, so (4.1) is equality for arbitrary
finite depths, without the `2*pi` restriction. This pure-pair sector has mean
load two; it is not by itself a critical mean-load-one zeta model.

### Explicit high-depth leakage, rather than an unnamed exception

For unrestricted site-dependent depths define

\[
\mathcal B_{\rm high}=
\sum_{\substack{p\in A\\a_p>2\pi}}\sum_{q\notin A}
(2-r_q)(J_{P,a_p}(p-q))_+.
\]

The same exact identity yields

\[
\boxed{\|K\|_F^2\le\Delta+2\mathcal B_{\rm high}.}
\tag{4.4}
\]

Proving this positive leakage is small for genuine source configurations is a
precise remaining task. This checkpoint does not assume it. Common-depth
high-depth interface estimates in the predecessor are not silently promoted
to variable-depth bounds.

## 5. Correctly normalized transfer to shorter supports

Let `R:C^P -> C^d` be a contraction. The Hilbert--Schmidt ideal property gives

\[
\|RKR^*\|_F\le\|K\|_F.
\tag{5.1}
\]

For the source-compatible box model, `R` restricts to `d` consecutive physical
rows and `alpha=d/P`. Each restricted Fourier atom has norm squared `alpha`.
Consequently the **unit-atom** short-scale operators are

\[
G_\alpha=\alpha^{-1}RGR^*,\qquad
G_{0,\alpha}=\alpha^{-1}RG_0R^*.
\tag{5.2}
\]

Failing to include `alpha^-1` would miss `alpha^-2` in the second moment.
With `eta=(Delta+2 B_high)/P`, (4.4) implies

\[
\boxed{
\frac{\|G_\alpha-G_{0,\alpha}\|_F}{\sqrt P}
\le\frac{\sqrt\eta}{\alpha}.}
\tag{5.3}
\]

This estimate transfers an arbitrary continuous depth field at the operator
level, subject to the explicit high-depth charge. It does not require extra
zero-order depth channels.

For example, since `0<=G0<=2I`,

\[
\frac{|\|G_\alpha\|_F^2-\|G_{0,\alpha}\|_F^2|}{P}
\le\alpha^{-2}(4\sqrt{\alpha\eta}+\eta).
\tag{5.4}
\]

If `sum m_p=P`, one may replace `4 sqrt(alpha*eta)` by `2 sqrt(2 eta)`.
At `alpha=3/4`, reserving the *whole* `5/108` margin for (5.4) would require
`eta<0.00005627006969...`; with critical mean load, the improved sufficient
threshold is `0.00008422360628...`. These are illustrative model budgets,
not a source-level error ledger. Any other errors must be subtracted first.
The triangle inequality (5.3), rather than this absolute-error estimate,
gives a sharper conditional proportion result next.

## 6. An explicit two-scale ideal-model corollary

Assume `P` is divisible by four, `sum m_p=P`, each pair has multiplicity one
and depth in `[0,2*pi]`, and the other marks are tangent `0/1/2`. Let

\[
s=P^{-1}\#\{p:m_p=1\},\qquad \delta=\Delta/P.
\]

Only the tangent mark-one sites are simple points in this model. As
`sum m_p^2/P=2-s`, the first-scale identity reads

\[
\delta=\|G\|_F^2/P-2+s.
\tag{6.1}
\]

Suppose the two **ideal moment assumptions** are

\[
\|G\|_F^2/P\le4/3,\qquad
\|G_{3/4}\|_F^2/P\le19/12.
\tag{6.2}
\]

By (4.3), `0<=delta<=s-2/3`. Write `x=s-2/3>=0`.
The exact partial Fourier calculation for the tangent comparison gives

\[
\frac{\|G_{0,\alpha}\|_F^2}{P}
=\frac1\alpha+\sum_{\ell=1}^{P-1}
 F_\alpha(\ell/P)|\widehat m(\ell)|^2,
\quad
F_\alpha(t)=\frac{(\alpha-t)_++(\alpha-(1-t))_+}{\alpha^2}.
\tag{6.3}
\]

Here the Fourier coefficients are normalized by `1/P` and the mean is one.
At `alpha=3/4`, `F_alpha>=8/9`; Parseval gives
`sum_(ell!=0)|mhat(ell)|^2=1-s`. Thus

\[
\|G_{0,3/4}\|_F^2/P\ge44/27-(8/9)x.
\]

Combine this with (5.3) and (6.2):

\[
\sqrt{44/27-(8/9)x}\le\sqrt{19/12}+\frac43\sqrt x.
\]

Squaring nonnegative sides and rearranging yields

\[
x+\sqrt{19/12}\sqrt x\ge5/288.
\]

**Corollary 6.1 (conditional finite ideal bound).** Under exactly (6.2) and the
model assumptions above,

\[
\boxed{
s\ge\frac23+\epsilon_0,
\quad
\epsilon_0=\frac14\left(\sqrt{119/72}-\sqrt{19/12}\right)^2
=0.000186299466336929\ldots.}
\tag{6.4}
\]

Numerically the right side is `0.6668529661330036...`. It is a finite ideal
model theorem candidate, not a new unconditional zeta result and not a claim
to exceed the paper's optimized `0.6725` result. Its value is that it supplies
an explicit stable gain without classifying a continuum of moderate depths.

With arithmetic/model upper-budget errors `u1,u2>=0`, and unrestricted depths
with `b=B_high/P`, the precise surviving inequality is instead

\[
\boxed{
\sqrt{44/27-(8/9)x}
\le\sqrt{19/12+u_2}+\frac43\sqrt{x+u_1+2b}.}
\tag{6.5}
\]

The square-root argument on the right is nonnegative by (4.4) and (6.1).
This gives an explicit place to charge high-depth leakage and both moment
errors. It is not a proof that those errors are small for actual zeta zeros.

## 7. What remains, and what no longer needs to be proved first

The finite-alphabet classification is no longer a prerequisite for the
moderate-depth **operator transfer**. Likewise, the weighted trace is not
established as a necessary new channel: the direct operator comparison is an
alternative. This is an additive correction to the route selection in the
predecessor, not a deletion of its correctly scoped finite-alphabet results.

The next source-facing obligations are:

1. Obtain a valid master-lattice/operator approximation for actual reflection
   pairs, not only the all-on-line compactness theorem. Charge off-grid,
   collision and higher-multiplicity errors.
2. Bound the positive high-depth leakage or replace it by an arithmetic
   observable with an actually proved localized estimate. The exact finite
   prime term (2.1) is available; it is not itself that estimate.
3. Identify the short source compression with the correctly normalized
   contraction, including smooth taper, resampling, finite-section and tail
   losses. A small edge *measure* alone is not uniform control of arbitrary
   energy concentrated on that edge.
4. Insert all losses into an explicit analogue of (6.5), and independently
   verify the frozen finite package before promoting any authority.

No finite rank-null vector is claimed to be a realizable zeta counterexample.
No normalized-depth bound is inferred from an unscaled `o(1)` error. No claim
is made that the count of remaining bridge statements measures proximity to
an RH proof.

## 8. Reproduction and evidence

Run from this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_weighted_trace.py --samples 80
```

The checker performs exact symbolic finite identities, a finite prime-part
quadrature with an analytic omitted-integral bound, the two cutoff-order
signals, variable-depth finite matrix identities, high-depth charge checks,
and critical-density short-scale normalization. The cosine taper example is
not asserted to meet every source profile hypothesis. SciPy's error estimate
is not an interval certificate. Seeded tests are not exhaustive proofs.

`validation.txt` is actual captured output. `computation-record.json` records
versions, backend selection, input scopes and hashes. The bundled repository
backend inventory/record scripts and the full repository test suite were not
run in this connector-only checkout; local availability was checked directly,
and package hashes/structure are checked separately. No CI or Lean build is
claimed. See `checkpoint.json` for claim-level status and the computation
handoff. It declares no canonical Project objective.
