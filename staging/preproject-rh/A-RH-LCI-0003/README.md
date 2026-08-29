# A-RH-LCI-0003 — local compactness inverse and strain obstruction

Status: `solver_proof_candidate` (not independently verified)

Issue: `#32`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-local-compactness-03`

Frozen parent: `A-RH-XSR-0002 @ 325f67106496248915a0647d4eae4b15ff10b42f`

This successor package does not modify the frozen parent. It works in the
ideal rectangular, all-on-line marked-configuration model unless explicitly
stated otherwise. It is not an unconditional theorem about zeta zeros and does
not prove RH.

## 0. Main outcome

The parent attempt isolated a missing implication of the form

\[
\text{small first-scale defect}
\quad\Longrightarrow\quad
\text{critical-lattice structure}.
\]

This attempt makes two corrections.

First, the natural global version is false:

\[
D_{1,N}=o(N)
\not\Longrightarrow
\min_s\sum_n\operatorname{dist}(x_n,s+\mathbb Z)^2=o(N).
\]

A slowly strained lattice has total first-scale defect `O(1)` but global
fixed-phase squared displacement `Theta(N)`.

Second, a global phase is unnecessary. After uniform spatial re-rooting, small
first-scale defect forces every local weak limit into a **random** translate of
the integer lattice. The phase is allowed to drift on macroscopic scales.
Within the precise ideal periodic model below, this gives a proof candidate for
the qualitative two-scale exclusion

\[
\boxed{
\frac{D_{1,N}}N\to0,\quad
\limsup\frac{S_N}{N}\le\frac23
\quad\Longrightarrow\quad
\liminf\mathcal E_{3/4,N}\ge\frac{44}{27}
=\frac{19}{12}+\frac5{108}.
}
\]

Thus the ideal `5/108` margin from `A-RH-XSR-0002` survives arbitrary slow
macroscopic phase drift. What remains open is the transfer from actual Zeta23
matrices—smooth tapers, finite sections, tails and interacting off-line
reflection blocks—to this all-on-line rectangular point-process model.

---

## 1. Exact slow-strain obstruction

Fix `0 < alpha < 1/4` and put

\[
x_{n,N}=n+\frac{\alpha n}{N},
\qquad 0\le n<N,
\tag{1.1}
\]

with unit marks. Let

\[
q_\lambda(t)=
\left(\frac{\sin(\pi\lambda t)}{\pi\lambda t}\right)^2,
\qquad q_\lambda(0)=1.
\tag{1.2}
\]

For the first scale, the all-on-line `c=2` rectangular defect is

\[
D_{1,N}(\alpha)
=\sum_{m\ne n}q_1(x_{m,N}-x_{n,N}).
\]

Grouping ordered pairs by `r=|m-n|` and using

\[
\sin\bigl(\pi r(1+\alpha/N)\bigr)
=(-1)^r\sin(\pi\alpha r/N)
\]

gives the exact finite formula

\[
\boxed{
D_{1,N}(\alpha)
=
2\sum_{r=1}^{N-1}(N-r)
\left[
\frac{\sin(\pi\alpha r/N)}
     {\pi r(1+\alpha/N)}
\right]^2.
}
\tag{1.3}
\]

It is a Riemann sum:

\[
\boxed{
D_{1,N}(\alpha)\longrightarrow
\mathcal D(\alpha)
=
\frac{2}{\pi^2}
\int_0^1(1-t)\frac{\sin^2(\pi\alpha t)}{t^2}\,dt.
}
\tag{1.4}
\]

Hence `D_{1,N}/N -> 0`. For small `alpha`,

\[
\mathcal D(\alpha)=\alpha^2+O(\alpha^4).
\tag{1.5}
\]

On the other hand, all fractional displacements lie in an interval of length
less than `1/4`, so there is no wrapping at the minimizing phase. The exact
least-squares calculation is

\[
\begin{aligned}
\min_s\sum_{n=0}^{N-1}
\operatorname{dist}(x_{n,N},s+\mathbb Z)^2
&=
\frac{\alpha^2}{N^2}
\sum_{n=0}^{N-1}
\left(n-\frac{N-1}{2}\right)^2\\
&=
\boxed{\frac{\alpha^2(N^2-1)}{12N}}
\sim\frac{\alpha^2}{12}N.
\end{aligned}
\tag{1.6}
\]

This exactly refutes global mean-square matching to one fixed lattice phase.

For each fixed offset `r`, however,

\[
x_{n+r,N}-x_{n,N}=r+\frac{\alpha r}{N}\longrightarrow r.
\tag{1.7}
\]

Every fixed-radius randomly rooted window therefore converges to an exact
integer-lattice window. This is why local weak convergence is the right
topology.

---

## 2. Precise finite periodic model

Let `L` be a positive integer and let

\[
\mathbb T_L=\mathbb R/L\mathbb Z.
\]

A marked configuration is

\[
\mu=\sum_{a=1}^{A}m_a\delta_{x_a},
\qquad
x_a\in\mathbb T_L\ \text{distinct},\quad
m_a\in\mathbb Z_{>0},
\tag{2.1}
\]

with critical mean mass

\[
\sum_a m_a=L.
\tag{2.2}
\]

Periodize the kernel by

\[
Q_{\lambda,L}(t)=
\sum_{k\in\mathbb Z}q_\lambda(t+kL).
\tag{2.3}
\]

For integer `L`, `Q_{1,L}` vanishes exactly at the nonzero integer residues and
is positive at every noninteger residue.

Define the first-scale tangent defect

\[
\boxed{
D_{1,L}(\mu)=
\sum_{a\ne b}m_am_bQ_{1,L}(x_a-x_b)
+\sum_a(m_a-2)_+^2.
}
\tag{2.4}
\]

The first sum is ordered. In the all-on-line rectangular model, it is the
off-diagonal atom-Gram energy; the second sum is the exact load-excess term
from the corrected `Q=0` defect identity of `A-RH-XSR-0002`.

Define the normalized full second-scale Gram energy

\[
\boxed{
\mathcal E_{\lambda,L}(\mu)
=
\frac1L\sum_{a,b}m_am_bQ_{\lambda,L}(x_a-x_b).
}
\tag{2.5}
\]

The diagonal `a=b` is included. Let

\[
S_L(\mu)=\#\{a:m_a=1\}.
\tag{2.6}
\]

The theorem candidate concerns sequences `L_j -> infinity` satisfying

\[
\frac{D_{1,L_j}(\mu_j)}{L_j}\to0.
\tag{2.7}
\]

---

## 3. Rooted tightness and intensity preservation

Extend each `mu_j` periodically to `R`. Choose `U_j` uniformly on
`[0,L_j)` and define the random rooted measure

\[
\Xi_j=\theta_{-U_j}\mu_j.
\tag{3.1}
\]

Its law is stationary and, for every bounded interval `I`,

\[
\mathbb E\,\Xi_j(I)=|I|.
\tag{3.2}
\]

The first moment gives vague tightness. To prevent loss of intensity in the
limit, one needs uniform integrability. It follows from the defect.

Fix an interval `I` of length `h<1/2` and put

\[
c_h=\min_{|t|\le h}q_1(t)>0.
\]

For `M_I=Xi_j(I)`, write `R_I` for the ordered distinct-pair part of the
defect inside `I`, and `A_I` for the load-excess part. The integer inequality

\[
m^2\le4m+(m-2)_+^2
\tag{3.3}
\]

gives

\[
M_I^2
\le
4M_I+A_I+c_h^{-1}R_I.
\tag{3.4}
\]

Averaging over the root, an atom or ordered pair can remain inside `I` for a
set of shifts of measure at most `h`. Therefore

\[
\mathbb E M_I^2
\le
4h+
h(1+c_h^{-1})\frac{D_{1,L_j}(\mu_j)}{L_j}.
\tag{3.5}
\]

For a general compact interval, partition into finitely many intervals of
length below `1/2` and use Cauchy–Schwarz. Thus local masses have uniformly
bounded second moments. Consequences:

1. the laws of `Xi_j` are tight in the vague topology;
2. every subsequential stationary limit `Xi` has intensity exactly one, not
   merely at most one;
3. compactly supported linear statistics are uniformly integrable.

This derives the previous checkpoint's H1 and H2 from the finite defect.

---

## 4. Random-coset collapse

### Theorem A — local support collapse (proof candidate)

Under (2.2) and (2.7), every subsequential local weak limit `Xi` of the rooted
laws satisfies, almost surely,

\[
\operatorname{supp}\Xi\subset S+\mathbb Z
\tag{4.1}
\]

for a random phase `S mod 1`.

### Proof route

Take two compact neighborhoods `A,B` whose difference set stays a positive
distance from `Z`. Then

\[
\inf_{x\in A,y\in B}q_1(x-y)>0.
\]

The expectation of `Xi_j(A)Xi_j(B)` is bounded by a constant times
`D_{1,L_j}/L_j`, hence tends to zero. Product-measure functionals with compact
support pass to a vague subsequential limit using the local second-moment bound
(3.5). Therefore

\[
\Xi(A)\Xi(B)=0
\quad\text{almost surely}.
\]

A countable rational basis of such pairs implies that any two distinct support
points of `Xi` differ by an integer. Every nonempty locally finite set with
that property lies in one coset of `Z`. Intensity one excludes the empty
process.

Real-translation stationarity makes `S mod 1` Haar-uniform. Conditional on the
phase, define

\[
M_k=\Xi(\{S+k\}),\qquad k\in\mathbb Z.
\tag{4.2}
\]

Then `(M_k)` is a stationary nonnegative-integer process under integer shifts,
and

\[
\mathbb E M_0=1.
\tag{4.3}
\]

The load term in (2.4) also shows that marks above two have zero intensity in a
zero-defect limit, although the later Fourier inequality does not require this
extra conclusion.

### Collision boundary

The first pair-energy functional is not globally lower semicontinuous at a
collision: two nearby simple atoms may merge into one double atom and lose
their mutual off-diagonal term. The support proof avoids this problem by using
test neighborhoods separated from the diagonal. Positive-density collisions
would themselves cost order `L` because `q_1(t)->1` as `t->0`, so they cannot
appear at a typical root under (2.7).

---

## 5. Passing the simple intensity

Root jointly the simple-point measure

\[
\Sigma_j=\sum_{a:m_{j,a}=1}\delta_{x_{j,a}}.
\tag{5.1}
\]

Since `Sigma_j <= Xi_j`, it inherits tightness and uniform integrability.
Extract a joint limit `(Xi,Sigma)`. If `Xi` has an atom of mass one at `x`,
integer-valued vague convergence in a sufficiently small isolating
neighborhood forces the approximating total mass there eventually to equal
one. The approximating atom is then simple, so `Sigma` also has an atom at
`x`.

Consequently the simple-point measure of `Xi` is dominated by `Sigma`. If

\[
\limsup_j\frac{S_{L_j}(\mu_j)}{L_j}\le\frac23,
\tag{5.2}
\]

then the stationary lattice mark process satisfies

\[
x:=\mathbb P(M_0=1)\le\frac23.
\tag{5.3}
\]

Mergers can decrease simple intensity but cannot create a new mark-one atom
from higher integer mass. This is the precise semicontinuity direction needed
for the contradiction.

---

## 6. Passing the second-scale energy

For a compactly supported nonnegative cutoff of `q_lambda`, the rooted full
quadratic functional

\[
\nu\longmapsto
\iint \chi(u)\,q_{\lambda,R}(v-u)\,d\nu(u)d\nu(v)
\tag{6.1}
\]

is local. Product-measure convergence together with (3.5) allows passage to
the rooted limit. Monotone removal of the cutoff gives

\[
\mathcal E_\lambda(\Xi)
\le
\liminf_j\mathcal E_{\lambda,L_j}(\mu_j).
\tag{6.2}
\]

The diagonal is included, so collisions are compatible with the limit:
two unit atoms merging contribute `1+1+2q_lambda(epsilon)->4`, equal to the
square of the limiting double mark.

This derives the previous checkpoint's H5 in the finite periodic model.
The only remaining measure-theoretic work for a fully formal proof is to write
the standard vague-product and uniform-integrability lemmas at theorem-level
precision.

---

## 7. Stationary lattice Fourier bound

For the lattice mark process, write

\[
E_k=M_k-1.
\]

If the second-scale energy is finite, then `E M_0^2<infinity`. The covariance
sequence

\[
C_r=\mathbb E(E_0E_r)
\]

is positive definite, so Herglotz gives a positive measure `sigma` on the unit
circle with total mass

\[
\sigma(\mathbb T)=\operatorname{Var}(M_0).
\tag{7.1}
\]

For `1/2<=lambda<=1`, the sampled squared-sinc symbol is

\[
F_\lambda(t)=
\frac{(\lambda-t)_++(\lambda-(1-t))_+}{\lambda^2},
\qquad0\le t\le1,
\tag{7.2}

with

\[
\sum_{r\in\mathbb Z}q_\lambda(r)=\frac1\lambda,
\qquad
F_\lambda(t)\ge f_\lambda
=\frac{2\lambda-1}{\lambda^2}.
\tag{7.3}
\]

Therefore

\[
\boxed{
\mathcal E_\lambda(\Xi)
=
\frac1\lambda+\int F_\lambda\,d\sigma
\ge
\frac1\lambda+
\frac{2\lambda-1}{\lambda^2}\operatorname{Var}(M_0).
}
\tag{7.4}
\]

For every nonnegative integer `m`,

\[
m^2\ge2m-\mathbf1_{\{m=1\}}.
\tag{7.5}
\]

Using `E M_0=1` and `x=P(M_0=1)`,

\[
\operatorname{Var}(M_0)
=\mathbb E M_0^2-1
\ge1-x.
\tag{7.6}
\]

---

## 8. Qualitative two-scale exclusion

At

\[
\lambda=\frac34,
\]

the constants are

\[
\frac1\lambda=\frac43,
\qquad
f_\lambda=\frac89,
\qquad
\kappa(\lambda)=\frac1\lambda+\frac\lambda3=\frac{19}{12}.
\tag{8.1}
\]

If `x<=2/3`, then `Var(M_0)>=1/3`, and (7.4) gives

\[
\mathcal E_{3/4}(\Xi)
\ge
\frac43+\frac89\frac13
=
\frac{44}{27}.
\tag{8.2}
\]

The exact excess above the ideal Zeta23 budget is

\[
\boxed{
\frac{44}{27}-\frac{19}{12}=\frac5{108}.
}
\tag{8.3}
\]

### Theorem B — ideal local-compactness gap (proof candidate)

There is no sequence of finite periodic all-on-line rectangular
configurations satisfying simultaneously

\[
\frac{D_{1,L_j}}{L_j}\to0,
\qquad
\limsup_j\frac{S_{L_j}}{L_j}\le\frac23,
\qquad
\limsup_j\mathcal E_{3/4,L_j}\le\frac{19}{12}.
\tag{8.4}
\]

The proof is: root, extract a stationary intensity-one local limit, apply
Theorem A, pass the simple intensity and second energy, then use (8.2).

By contradiction compactness, this is equivalent to a nonconstructive
finite-size dichotomy: there exist `eta>0` and `L_0` such that for every
`L>=L_0` in this model with `S_L/L<=2/3`,

\[
\boxed{
\frac{D_{1,L}}L\ge\eta
\quad\text{or}\quad
\mathcal E_{3/4,L}\ge\frac{19}{12}+\eta.
}
\tag{8.5}
\]

The theorem does not provide an explicit `eta`. Slow strain shows why an
explicit proof cannot proceed through one global lattice phase.

---

## 9. Deterministic stress tests

The standard-library script

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_compactness_models.py
```

checks:

1. the exact slow-strain finite formula and limiting integral;
2. the exact global displacement identity;
3. fixed-window collapse under slow strain;
4. a phase-separated mark process with exact simple density `2/3`.

For the default `alpha=0.2`:

```text
limiting total first-scale defect       0.039140897460
N=7680: first-scale defect / N          5.096e-06
N=7680: best fixed-coset L2 error / N   0.003333333277

N=960 phase-separated model:
first-scale defect / N                  0.000205561
second-scale excess over 19/12          0.046140544
limiting target                         5/108 = 0.046296296296
```

The computation supports the topology choice and detects algebraic
regressions. It is not a proof of the compactness theorem.

---

## 10. Alternative collapsed-orbit defect and an exact off-line obstruction

The off-line pair contribution has additional structure. Write one reflection
pair vector as

\[
v_p=x_p+i y_p
\]

with real vectors `x_p,y_p` and multiplicity `n_p`. Its real symmetric
contribution is

\[
n_p(v_pv_p^T+\bar v_p\bar v_p^T)
=
2n_p(x_px_p^T-y_py_p^T).
\tag{10.1}
\]

Define the collapsed positive and negative matrices

\[
P^\sharp
=
P_{\rm on}+\sum_p2n_px_px_p^T,
\qquad
R^\sharp
=
\sum_p2n_py_py_p^T,
\qquad
A=P^\sharp-R^\sharp.
\tag{10.2}
\]

Treat the real parts of the pairs as additional positive atoms of weight
`2n_p`, and take `Q=-Rsharp`, whose positive inertia is zero. Let

\[
a_i=m_i\|u_i\|^2,
\qquad
b_p=2n_p\|x_p\|^2,
\]

and define

\[
\begin{aligned}
\mathcal L_2^\sharp
={}&
\sum_{i\ {\rm on}}
[k_2(m_i)-k_2(a_i)]\\
&+\sum_p[4-k_2(b_p)].
\end{aligned}
\tag{10.3}
\]

The first sum is nonnegative from `||u_i||<=1`; the second is nonnegative
because `k_2<=4`. If

\[
J_2^\sharp
=
\operatorname{tr}g_2(P^\sharp)
-\sum_{i\ {\rm on}}g_2(a_i)
-\sum_pg_2(b_p),
\tag{10.4}
\]

then applying the exact defect identity of `A-RH-RTD-0001` to
`(Psharp,-Rsharp)` gives the alternative exact decomposition

\[
\boxed{
\begin{aligned}
\Delta_2^{\rm count}
={}&
\mathcal L_2^\sharp+J_2^\sharp\\
&+\|R^\sharp-(P^\sharp-2I)_+\|_F^2\\
&+2\operatorname{tr}((2I-P^\sharp)_+R^\sharp).
\end{aligned}
}
\tag{10.5}
\]

This is useful because it identifies the precise cancellation mode that an
off-line extension must exclude: the negative imaginary-part energy can match
the supra-threshold spectrum of the collapsed positive frame.

### Exact hyperbolic-swap countermodel

The isolated-pair depth penalty from the parent attempt does **not** add over
interacting pairs. Fix `r>0` in a real two-dimensional space and set

\[
\begin{array}{ll}
x_1=\sqrt{1+r}\,e_1,&y_1=\sqrt r\,e_2,\\
x_2=\sqrt{1+r}\,e_2,&y_2=\sqrt r\,e_1.
\end{array}
\tag{10.6}
\]

Each pair separately satisfies

\[
\langle x_i,y_i\rangle=0,
\qquad
\|x_i\|^2-\|y_i\|^2=1,
\tag{10.7}
\]

the elementary hyperbolic normalization of a rectangular reflection pair.
But together,

\[
2(x_1x_1^T-y_1y_1^T)
+
2(x_2x_2^T-y_2y_2^T)
=
2I_2.
\tag{10.8}
\]

There are two pair budgets, so

\[
\boxed{
8-
\left[
4\operatorname{tr}(2I_2)-\|2I_2\|_F^2
\right]
=8-(16-8)=0.
}
\tag{10.9}
\]

By contrast, the parent isolated-pair formula assigns each pair the strictly
positive depth cost

\[
2[(1+2r)^2-1]=8r+8r^2.
\tag{10.10}
\]

In (10.5),

\[
P^\sharp=2(1+r)I_2,
\qquad
R^\sharp=2rI_2=(P^\sharp-2I)_+,
\]

and every term vanishes. Thus the cancellation is not a bookkeeping artifact.

### Consequence

No proof using only

- scalar rank–trace data,
- positive inertia,
- per-pair norm difference,
- and an additive isolated-pair depth estimate

can extend the `5/108` compactness gap to arbitrary interacting off-line
pairs. The next source-specific target must exclude positive-density
**hyperbolic swap cycles** for genuine Weil/Gabor evaluation vectors.

A useful candidate theorem is:

> If genuine off-line pair vectors produce
> `Rsharp approximately (Psharp-2I)_+` and simultaneously make the collapsed
> Schur gap small, then their normalized depths tend to zero in density, except
> for mass that collapses into tangent load-two lattice cells.

Potential observables that are absent from the scalar certificate include
cross-Gram matrices between real and imaginary pair components, commutators
with the sampling/translation operator, and asymmetric or derivative-weighted
test windows. These are now higher-priority than attempting to sum the
isolated depth formula.

---

## 11. Open bridge to Zeta23

The ideal theorem still omits five source-level effects:

1. smooth rather than rectangular tapers;
2. finite grid sections and the tail matrix;
3. off-line reflection pairs represented by an indefinite `Q`;
4. the normalization leakage `k_c(m)-k_c(m||v||^2)`;
5. `lambda_1=L/ell_1` rather than an exact fixed ratio.

The parent attempt gives a positive depth penalty for one isolated off-line
reflection pair. It does not yet prove that an interacting collection of
near-tangent pairs compactifies into independent load-two lattice cells.
This is now the main mathematical obstruction.

A viable successor theorem should be a **collapsed-orbit compactness theorem**:
small first-scale six-term defect implies that, at a typical root,

- on-line simple zeros become load-one lattice cells;
- on-line doubles and shallow simple off-line pairs become tangent load-two
  cells;
- deeper or multiple off-line pairs pay positive density-level defect;
- the smooth/finite/tail errors vanish before the `5/108` margin is consumed.

---

## 12. Quantitative route

For `|t|<=R`,

\[
q_1(t)
\ge
\frac{4}{\pi^2R^2}
\operatorname{dist}(t,\mathbb Z)^2.
\tag{12.1}
\]

This can assign a local phase on blocks of length `R`. The next constructive
task is to balance:

- local phase-dispersion error;
- block-boundary pairs;
- the `1/t^2` tail of `q_{3/4}`;
- cell-mass rounding and collisions.

A preliminary target is an estimate of the form

\[
\mathcal E_{3/4}
\ge
\frac43+\frac89\operatorname{Var}(M)
-
C\left(
R^{3/2}\sqrt{D_1/L}+\frac{\log R}{R}
\right).
\tag{12.2}
\]

The exponent and constants in (12.2) have not been closed. It is recorded as a
research target, not a theorem.

---

## 13. Authority and non-implication boundary

Exact in this package:

- the slow-strain formulas (1.3)--(1.6);
- the refutation of global fixed-phase `l^2` matching;
- the stationary lattice Fourier calculation (7.4)--(8.3);
- the exact collapsed-orbit decomposition (10.5);
- the hyperbolic-swap countermodel (10.6)--(10.10);
- deterministic finite-model checks.

Proof candidate requiring independent audit:

- the complete rooted compactness passage in Sections 3--8;
- the nonconstructive ideal dichotomy (8.5).

Open:

- an explicit quantitative modulus;
- interacting off-line reflection pairs;
- transfer through the actual Zeta23 smooth taper, finite section and tail;
- any unconditional improvement of a zeta-zero proportion.

No Project authority, shared-result authority, independent-verifier receipt or
claim about RH is created by this package.
