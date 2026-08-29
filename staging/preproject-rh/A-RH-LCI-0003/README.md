# A-RH-LCI-0003 — local compactness inverse and strain obstruction

Status: `solver_checkpoint` (not independently verified)

Issue: `#32`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-local-compactness-03`

Frozen parent: `A-RH-XSR-0002 @ 325f67106496248915a0647d4eae4b15ff10b42f`

This successor package does not modify the frozen parent. It works only in the
ideal rectangular, all-on-line marked-configuration model unless explicitly
stated otherwise. It is not an unconditional theorem about zeta zeros and does
not prove RH.

## 0. Main correction and new target

The parent attempt proposed a near-saturation-to-lattice bridge. A natural but
overly strong version would be

\[
D_{1,N}=o(N)
\quad\Longrightarrow\quad
\min_s\sum_n\operatorname{dist}(x_n,s+\mathbb Z)^2=o(N).
\tag{0.1}
\]

This implication is false. A slowly strained lattice has total first-scale
defect only `O(1)` while its best global fixed-coset squared displacement is
`Theta(N)`.

The correct inverse object is local rather than global:

> after a uniform random spatial re-rooting, every local weak limit of a
> first-scale near-extremizer should be supported on a random translate of the
> integer lattice; the phase may drift on macroscopic scales.

This distinction matters. Slow strain destroys a global Kadec-style fit but is
invisible in every fixed local window, and it does not erase the local
`lambda=3/4` Fourier-symbol obstruction.

## 1. Exact slow-strain counterexample

Fix `0 < alpha < 1/4` and put

\[
x_{n,N}=n+\frac{\alpha n}{N},
\qquad 0\le n<N,
\tag{1.1}
\]

with unit marks. For

\[
q_1(t)=\left(\frac{\sin\pi t}{\pi t}\right)^2,
\]

the all-on-line `c=2` load-level defect is the off-diagonal energy

\[
D_{1,N}(\alpha)
=2\sum_{r=1}^{N-1}(N-r)
\left[
\frac{\sin(\pi\alpha r/N)}
     {\pi r(1+\alpha/N)}
\right]^2.
\tag{1.2}
\]

Indeed

\[
\sin\bigl(\pi r(1+\alpha/N)\bigr)
=(-1)^r\sin(\pi\alpha r/N).
\]

The Riemann-sum limit is finite:

\[
\boxed{
D_{1,N}(\alpha)
\longrightarrow
\mathcal D(\alpha)
=
\frac{2}{\pi^2}
\int_0^1(1-t)
\frac{\sin^2(\pi\alpha t)}{t^2}\,dt.
}
\tag{1.3}
\]

Consequently `D_{1,N}/N -> 0`.

On the other hand, because `alpha<1/4`, for the minimizing phase every point is
matched to the integer with the same index, and

\[
\begin{aligned}
\min_s\sum_{n=0}^{N-1}
\operatorname{dist}(x_{n,N},s+\mathbb Z)^2
&=
\frac{\alpha^2}{N^2}
\sum_{n=0}^{N-1}
\left(n-\frac{N-1}{2}\right)^2\\
&=
\boxed{
\frac{\alpha^2(N^2-1)}{12N}
}
\sim\frac{\alpha^2}{12}N.
\end{aligned}
\tag{1.4}
\]

Thus (0.1) is refuted exactly.

For small `alpha`, expanding the sine in (1.3) gives

\[
\mathcal D(\alpha)=\alpha^2+O(\alpha^4),
\]

while the global displacement remains order `alpha^2 N`. No estimate depending
only on total first-scale defect can control a single global phase in squared
mean.

## 2. Why the cross-scale route survives slow strain

Let

\[
q_\lambda(t)=
\left(\frac{\sin(\pi\lambda t)}{\pi\lambda t}\right)^2.
\]

For every fixed integer offset `r`,

\[
x_{n+r,N}-x_{n,N}
=r+O(r/N).
\]

Hence a uniformly rooted fixed-radius window converges to an exact integer
lattice window. In particular, for bounded integer marks whose empirical local
law converges, the second-scale energy per unit length converges to the same
lattice convolution energy as in `A-RH-XSR-0002`.

So the correct topology must identify configurations that differ by a
macroscopic slowly varying phase field. Local weak convergence does this;
global `l^2` matching does not.

## 3. Configuration space for a local compactness theorem

Let `L_j -> infinity`. On the circle `R/L_j Z`, let

\[
\mu_j=\sum_a m_{j,a}\delta_{x_{j,a}},
\qquad m_{j,a}\in\mathbb Z_{>0},
\qquad \mu_j(\mathbb R/L_j\mathbb Z)=L_j.
\tag{3.1}
\]

Extend `mu_j` periodically to `R`, choose `U_j` uniformly on `[0,L_j)`, and
consider the random rooted measure

\[
\Xi_j=\theta_{-U_j}\mu_j.
\tag{3.2}
\]

Its law is stationary and has intensity one.

Define the first-scale nonnegative tangent defect

\[
\mathfrak D_{1,j}
=
\sum_{a\ne b}m_{j,a}m_{j,b}q_1(x_{j,a}-x_{j,b})
+
\sum_a(m_{j,a}-2)_+^2,
\tag{3.3}
\]

with the kernel periodized on the circle. The second term is the exact scalar
penalty that prevents a positive density of marks above two from hiding in a
zero off-diagonal energy configuration.

For a fully rigorous marked-point-process passage, the following convergence
package must be stated rather than silently assumed:

- **H1 — rooted tightness:** the laws of `Xi_j` are tight in the vague topology;
- **H2 — intensity preservation:** local mass is uniformly integrable, so every
  subsequential limit has intensity one;
- **H3 — factorial-energy convergence:** compactly truncated first pair-energy
  measures pass to the limit;
- **H4 — mark-law convergence:** the intensity of mark-one atoms passes to the
  limit; collisions may only decrease this intensity;
- **H5 — second-energy lower semicontinuity:** for every `lambda`, the
  nonnegative truncated `q_lambda` energies are lower semicontinuous and the
  full energy is obtained by monotone removal of the truncation.

H1 and much of H2 follow from stationarity, unit mean mass, and the local
positivity of `q_1`; H3--H5 are the technical core that must be checked in any
formal proof. This package is deliberately explicit because vague convergence
alone does not automatically imply convergence of factorial moment measures.

## 4. Local-collapse theorem under H1--H5

### Theorem A — random-coset collapse

Assume H1--H5 and

\[
\frac{\mathfrak D_{1,j}}{L_j}\longrightarrow0.
\tag{4.1}
\]

Then every stationary subsequential local weak limit `Xi` has, almost surely,
support contained in one random translate

\[
S+\mathbb Z.
\tag{4.2}
\]

Conditional on `S mod 1`, the cell masses

\[
M_k=\Xi(\{S+k\}),\qquad k\in\mathbb Z,
\tag{4.3}
\]

form a stationary nonnegative-integer process under integer shifts, with

\[
\mathbb E M_0=1.
\tag{4.4}
\]

### Proof

For each fixed radius `R`, H3 and (4.1) imply that the limiting expected
first-scale pair energy in a rooted window of radius `R` is zero. Since every
term is nonnegative, almost surely every two distinct limiting atoms in that
window satisfy

\[
q_1(x-y)=0.
\]

The zero set of `q_1` away from the origin is precisely
`Z\{0}`. Taking a countable union over integer radii gives

\[
x-y\in\mathbb Z
\]

for every pair of distinct atoms. Any nonempty locally finite set with this
property lies in one coset of `Z`. Intensity one excludes the empty process.
Real-translation stationarity makes the phase `S mod 1` uniform; after
conditioning on the phase, integer translations act stationarily on the mark
sequence. H2 gives (4.4).

The load penalty in (3.3) additionally implies that marks above two have zero
intensity in the zero-defect limit. The Fourier argument below does not need
this strengthening, because its integer inequalities hold for every
nonnegative integer mark.

## 5. Stationary lattice energy

Let

\[
E_k=M_k-1.
\]

If `E[M_0^2]` is finite, Herglotz positivity gives a finite positive spectral
measure `sigma` on the unit circle whose total mass is

\[
\sigma(\mathbb T)=\operatorname{Var}(M_0).
\tag{5.1}
\]

For the sampled squared-sinc convolution, the symbol at scale `lambda>=1/2`
is

\[
F_\lambda(t)
=
\frac{(\lambda-t)_++(\lambda-(1-t))_+}{\lambda^2},
\qquad0\le t\le1,
\tag{5.2}
\]

and

\[
F_\lambda(t)\ge f_\lambda
=\frac{2\lambda-1}{\lambda^2}.
\tag{5.3}
\]

Therefore the limiting second-scale energy per unit length satisfies

\[
\begin{aligned}
\mathcal E_\lambda
&=
\frac1\lambda+
\int_{\mathbb T}F_\lambda(t)\,d\sigma(t)\\
&\ge
\frac1\lambda+f_\lambda\operatorname{Var}(M_0).
\end{aligned}
\tag{5.4}
\]

If the second moment is infinite, the lower bound is automatic with infinite
left side.

For every integer `m>=0`,

\[
m^2\ge2m-\mathbf1_{\{m=1\}}.
\tag{5.5}
\]

With `E M_0=1`, if

\[
x=\mathbb P(M_0=1),
\]

then

\[
\operatorname{Var}(M_0)
=\mathbb E M_0^2-1
\ge1-x.
\tag{5.6}
\]

## 6. Qualitative two-scale exclusion

At

\[
\lambda=\frac34,
\]

we have

\[
\frac1\lambda=\frac43,
\qquad
f_\lambda=\frac89,
\qquad
\kappa(\lambda)=\frac1\lambda+\frac\lambda3=\frac{19}{12}.
\tag{6.1}
\]

If the limiting simple-mark intensity obeys `x<=2/3`, then (5.6) gives
`Var(M_0)>=1/3`, and hence

\[
\mathcal E_{3/4}
\ge
\frac43+\frac89\frac13
=
\frac{44}{27}.
\tag{6.2}
\]

The gap above the ideal Zeta23 budget is

\[
\boxed{
\frac{44}{27}-\frac{19}{12}
=
\frac5{108}.
}
\tag{6.3}
\]

### Theorem B — qualitative compactness gap

Within the all-on-line rectangular class satisfying H1--H5, there is no
sequence for which all three conditions hold:

\[
\frac{\mathfrak D_{1,j}}{L_j}\to0,
\qquad
\limsup\frac{S_j}{L_j}\le\frac23,
\qquad
\limsup\mathcal E_{3/4,j}\le\frac{19}{12}.
\tag{6.4}
\]

Indeed, Theorem A produces a stationary lattice limit; H4 gives `x<=2/3`, H5
passes the second energy from below, and (6.2)--(6.3) contradict the final
condition.

Equivalently, after fixing the precise compact class and convergence moduli,
a contradiction argument yields a nonconstructive number `eta>0` and a size
threshold such that every sufficiently large configuration with simple
intensity at most `2/3` satisfies

\[
\boxed{
\frac{\mathfrak D_1}{L}\ge\eta
\quad\text{or}\quad
\mathcal E_{3/4}\ge\frac{19}{12}+\eta.
}
\tag{6.5}
\]

This removes the need for one global lattice phase, but it does not provide an
explicit `eta`.

## 7. What is proved, conditional, and still open

### Exact in this attempt

- the slow-strain formula (1.2);
- the finite limit (1.3);
- the global-displacement identity (1.4);
- the logical refutation of global `l^2` lattice matching;
- the stationary-lattice Fourier implication (5.4)--(6.3), once a local limit
  satisfying H1--H5 is available.

### Proof candidate

- deriving the complete H1--H5 package from only the finite first-scale defect,
  total mass, and source-compatible local zero-count inputs;
- the resulting unconditional compactness dichotomy inside the ideal
  all-on-line rectangular class.

The note states every required convergence property explicitly rather than
hiding it in the phrase "by compactness".

### Open bridge to Zeta23

Actual Zeta23 compressions also contain:

1. smooth rather than rectangular tapers;
2. finite grid sections and tail matrices;
3. off-line reflection pairs represented by an indefinite `Q`;
4. a normalized load leakage `k_c(m)-k_c(m||v||^2)`;
5. parameters `lambda_1=L/ell_1` rather than an exact fixed `lambda`.

The parent attempt proves an isolated off-line pair has a positive depth defect,
but interacting pairs are not yet known to collapse additively to mark-two
lattice atoms. That is the principal mathematical obstruction after the
all-on-line compactness theorem.

## 8. Next quantitative route

A constructive version should localize into blocks of length `R`.
For `|x-y|<=R`,

\[
q_1(x-y)
\ge
\frac{4}{\pi^2R^2}
\operatorname{dist}(x-y,\mathbb Z)^2.
\tag{8.1}
\]

This controls phase dispersion inside each block. One can then assign a local
phase, transfer the block to lattice loads, apply the `lambda=3/4` symbol floor,
and optimize `R` against boundary and kernel-Lipschitz errors. A preliminary
scaling analysis suggests an error of the form

\[
C\left(R^{3/2}\sqrt{\mathfrak D_1/L}+\frac{\log R}{R}\right),
\tag{8.2}
\]

but the mass-balancing and finite-section terms have not yet been closed.
Equation (8.2) is a research target, not a proved estimate.

## 9. Non-implication boundary

This checkpoint does not prove that actual zeta zeros have more than `2/3`
simple zeros on the critical line. The local compactness theorem is presently
conditional on H1--H5, the quantitative modulus is open, the interacting
off-line extension is open, and no Project authority or independent verifier
receipt is claimed.
