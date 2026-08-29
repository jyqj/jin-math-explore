# A-RH-RTD-0002 — process ledger

Status: active pre-genesis solver notebook. Nothing in this file has Project or verification authority.

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-window-collapse-02`

Base: `A-RH-RTD-0001@2f2ecdac7aec73d3996d3484e7a56b051a718f11`

Pinned source: `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`

This ledger is append-only in substance: later corrections must name the earlier error rather than silently replacing the historical conclusion.

---

## 2026-08-29 — milestone 0: hypotheses opened

The second attempt tests:

- **H1** — changing the scalar rank–trace threshold might beat the `c=2` simple-zero certificate;
- **H2** — changing only the sampling-grid phase might create macroscopic two-window separation;
- **H3** — finitely many fixed-width tapers might rule out simultaneous near-saturation using zero-side geometry alone.

The parent defect decomposition remains frozen and unpromoted while #25 is open.

---

## 2026-08-29 — milestone 1: H1 refuted by an exact scalar envelope

### Setup

Let `s1` be the number of simple on-line atoms, let `p` be the number of off-line reflection pairs, and let `N` be total multiplicity. The Zeta23 leak-free rank–trace inequality at an arbitrary threshold `c>0` has the abstract form

\[
2c\,t-f\le \sum_{j\in\mathrm{on}} k_c(m_j)+c^2p,
\qquad
k_c(m)=c^2-(c-m)_+^2,
\]

where `t=tr(P+Q)`, `f=||P+Q||_F^2`, every non-simple on-line atom has integer multiplicity `m>=2`, and every off-line pair contributes at least two units to `N`.

For every integer `m>=2`,

\[
k_c(m)\le \frac{c^2}{2}m.
\tag{1}
\]

Proof:

- if `m>=c`, then `k_c(m)=c^2 <= (c^2/2)m` because `m>=2`;
- if `2<=m<c`, then `k_c(m)=2cm-m^2`, and after division by `m`,
  \[
  2c-m\le 2c-2\le c^2/2
  \]
  by `(c-2)^2>=0`.

The off-line term also satisfies `c^2 p <= (c^2/2)(2p)`. Hence

\[
2c\,t-f
\le
\frac{c^2}{2}N+\beta_c s_1,
\tag{2}
\]

with

\[
\beta_c=k_c(1)-\frac{c^2}{2}
=
\begin{cases}
 c^2/2,&0<c\le1,\\
 2c-1-c^2/2,&c\ge1.
\end{cases}
\tag{3}
\]

Assume the same moment information used by the Zeta23 certificate,

\[
t\ge(1-o(1))N,
\qquad
f\le(\kappa+o(1))N,
\qquad 1\le\kappa<2.
\]

Whenever `beta_c>0`, (2) gives the scalar lower-bound candidate

\[
R_c(\kappa)
=
\frac{2c-c^2/2-\kappa}{\beta_c}.
\tag{4}
\]

For every `c>0`, including values with `beta_c<=0`, the numerator `n_c=2c-c^2/2-kappa` satisfies

\[
n_c\le(2-\kappa)\beta_c.
\tag{5}
\]

- For `c>=1`, `n_c=beta_c+1-kappa`, while
  \[
  \beta_c=1-(c-2)^2/2\le1.
  \]
  Therefore `n_c-(2-kappa)beta_c=(1-kappa)(1-beta_c)<=0`.
- For `0<c<=1`, the difference equals
  \[
  2c-\kappa-\frac{3-\kappa}{2}c^2.
  \]
  For `1<=kappa<2` this is increasing on `[0,1]` and its value at `c=1` is `(1-kappa)/2<=0`.

Consequences:

1. If `beta_c>0`, then
   \[
   R_c(\kappa)\le2-\kappa.
   \]
2. Equality is attained at `c=2`, where `beta_2=1`.
3. Any nonnegative linear combination of arbitrary-threshold inequalities whose total simple coefficient is positive also cannot beat `2-kappa`, because (5) adds term by term.
4. At the Zeta23 flat-window value `kappa=4/3`, the best possible scalar threshold bound is exactly
   \[
   s_1/N\ge2/3-o(1).
   \]

### H1 verdict

`REFUTED` under the existing first-moment, second-moment, integer-multiplicity and positive-inertia information model. Threshold optimization or nonnegative mixing of threshold certificates cannot improve the simple-zero constant. A new observable is necessary.

### Side observation, not yet promoted to a theorem

The same `c=2` inequality can be bookkept as

\[
4t-f\le N+2N_d,
\]

which already yields `N_d/N >= (3-kappa)/2`; at `kappa=4/3` this is `5/6`. This suggests that the choice `c=3` is not uniquely responsible for the `5/6` numerical constant, although its multiplicity bookkeeping is structurally cleaner. This observation still needs an independent source-alignment check.

---

## 2026-08-29 — milestone 2: H2 refuted at the complete-frame level

For a real taper `phi` supported in `[-L/2,L/2]`, set `h=2*pi/L` and define the complete analysis vector

\[
v_{T,\phi}(\gamma)_k=\widehat\phi(\gamma-T-kh),\qquad k\in\mathbb Z.
\]

The Poisson identity used in Zeta23 generalizes bilinearly: for two real tapers `phi,psi` with the same support length and grid,

\[
\sum_{k\in\mathbb Z}
\widehat\phi(\gamma-T-kh)
\overline{\widehat\psi(\gamma'-T-kh)}
=
L\,\widehat{\phi\psi}(\gamma-\gamma').
\tag{6}
\]

The right side is independent of the grid phase `T`. In particular, changing only `T` preserves every atom inner product. The correspondence

\[
v_{T,\phi}(\gamma_j)\mapsto v_{T+\delta,\phi}(\gamma_j)
\]

is therefore an isometry on the span of any finite atom family and extends to a partial unitary between the two spans. Their complete-frame Gram matrices, nonzero spectra, thresholded spectral data and rank–trace defects agree after that canonical identification.

### H2 verdict

`REFUTED` for the complete Poisson frame. Grid-phase translation alone cannot create a macroscopic two-window separation. Any finite-truncation effect comes only from boundary/tail terms and must be shown to be macroscopic before it can matter; Zeta23's architecture is designed to make those tails negligible, so phase translation is not a promising primary route.

---

## 2026-08-29 — milestone 3: same-scale finite-taper H3 refuted by a clock-multiplicity model

### 3.1 Linear and direct-sum collapse

For tapers `phi_r` on the same complete grid:

- a linear combination of analysis vectors is exactly the analysis vector of the linear-combination taper;
- for nonnegative weights `alpha_r`, the direct-sum vector
  \[
  V(\gamma)=\bigoplus_r\sqrt{\alpha_r}\,v_{\phi_r}(\gamma)
  \]
  has Gram kernel
  \[
  \langle V(\gamma),V(\gamma')\rangle
  =L\,\widehat{\sum_r\alpha_r\phi_r^2}(\gamma-\gamma').
  \]
  If `chi=(sum_r alpha_r phi_r^2)^(1/2)`, this is the single-window Gram kernel `L (chi^2)^hat`.

Therefore, at complete-frame Gram level, linear combinations and direct sums do not create a new scalar rank–trace information channel. They are Gram-equivalent to one effective taper. To escape this collapse one must retain genuinely joint nonlinear data: mixed products, commutators, thresholded differences, higher moments, or arithmetic constraints linking different scales.

### 3.2 Fixed-width plateau tapers are asymptotically orthogonal on the natural clock

Let `phi` satisfy

\[
0\le\phi\le1,
\qquad
\operatorname{supp}\phi\subset[-L/2,L/2],
\qquad
\phi=1\text{ on }[-L/2+w,L/2-w].
\]

Put `q=phi^2`,

\[
A=\int q,\qquad B=\int q^2.
\]

For natural clock ordinates

\[
\gamma_n=\gamma_0+n\frac{2\pi}{L},
\]

the normalized complete-frame Gram coefficient is

\[
r_n=\frac{\widehat q(2\pi n/L)}{A},
\qquad r_0=1.
\]

Fourier-series Parseval gives the exact identity

\[
\sum_{n\ne0}|r_n|^2
=
\frac{LB}{A^2}-1.
\tag{7}
\]

Since `0<=q<=1`, `B<=A`, while the plateau gives `A>=L-2w`. Hence

\[
0\le E_\phi(L):=\sum_{n\ne0}|r_n|^2
\le
\frac{L-A}{A}
\le
\frac{2w}{L-2w}.
\tag{8}
\]

Thus every fixed-width (`w=O(1)`) admissible taper becomes asymptotically orthogonal on the same natural clock.

### 3.3 Multiplicity pattern matching all flat-window scalar data

On six consecutive natural grid sites use the repeating occupancy/multiplicity pattern

\[
(1,1,1,1,2,0).
\tag{9}
\]

Per six sites this has:

\[
N=6,\qquad s_1=4,\qquad N_d=5,\qquad
\sum m_n^2=8.
\]

Therefore

\[
\frac{s_1}{N}=\frac23,\qquad
\frac{N_d}{N}=\frac56,\qquad
\frac{\sum m_n^2}{N}=\frac43.
\]

The extra zero site makes total multiplicity equal to the sampling dimension, so this model also matches the flat-window first-moment density at leading order.

For a block of `M` occupied atoms with `m_j in {1,2}`, let `G_phi` be the atom Gram matrix. For every threshold `c>=2`, and in particular `c=2,3`, the exact scalar defect is

\[
\Delta_c(\phi)
=
\sum_{i\ne j}m_im_j|r_{i-j}|^2.
\tag{10}
\]

Consequently,

\[
\Delta_c(\phi)
\le4M E_\phi(L),
\]

and for the six-site pattern, `M/N=5/6`,

\[
\frac{\Delta_c(\phi)}{N}
\le
\frac{10}{3}E_\phi(L)
\le
\frac{20w}{3(L-2w)}
=o(1).
\tag{11}
\]

Hence any fixed finite collection of fixed-width tapers has total scalar defect `o(N)` on the same clock-multiplicity model.

### 3.4 Failure of the proposed same-scale threshold-separation lemma

In the common atom-index representation, let `D=diag(m_j)`. Then

\[
\|G_\phi-D\|_F^2=\Delta_2(\phi)=o(N).
\]

The positive-part map on Hermitian matrices is the metric projection onto the positive semidefinite cone and is nonexpansive in Frobenius norm. Thus for two fixed-width tapers,

\[
\begin{aligned}
\|(G_\phi-2I)_+-(G_\psi-2I)_+\|_F
&\le\|G_\phi-G_\psi\|_F\\
&\le\sqrt{\Delta_2(\phi)}+\sqrt{\Delta_2(\psi)}\\
&=o(\sqrt N).
\end{aligned}
\tag{12}
\]

With `Q=0`, this contradicts any universal same-scale lower bound of the form `eta sqrt(N)` with fixed `eta>0`.

### H3 verdict

`REFUTED` in the complete-frame, same-scale, zero-side information model for every fixed finite family of fixed-width plateau tapers. Taper variation at one asymptotic scale cannot by itself force a macroscopic aggregate defect.

This does not rule out:

- tapers whose shape changes on a macroscopic fraction of `L`;
- genuinely mixed nonlinear observables;
- different compression scales;
- prime-side arithmetic constraints excluding the clock model;
- finite-truncation effects, unless they are independently shown to remain submacroscopic.

---

## 2026-08-29 — milestone 4: a surviving two-scale mechanism and an ideal `23/32` bound

H3 fails because every fixed-width taper approaches the same box window at scale `L`. Changing the *scale* is different: a set orthogonal at the Nyquist scale `L` becomes correlated after restriction to `lambda L`.

### 4.1 Sampled-sinc symbol

Use the ideal box taper. On the natural `L`-clock, the normalized inner product at the shorter scale `lambda L` is

\[
r_\lambda(n)=\operatorname{sinc}(\lambda n)
:=\frac{\sin(\pi\lambda n)}{\pi\lambda n}.
\]

Let

\[
s_\lambda(n)=r_\lambda(n)^2.
\]

For `1/2<=lambda<=1`, the discrete Fourier symbol is

\[
S_\lambda(\xi)
=
\sum_{n\in\mathbb Z}s_\lambda(n)e^{-2\pi i n\xi}
=
\frac1\lambda
\sum_{k\in\mathbb Z}
\left(1-\frac{|\xi+k|}{\lambda}\right)_+.
\tag{13}
\]

On `xi in [-1/2,1/2]`, its exact minimum is

\[
\omega_\lambda
:=\min S_\lambda
=
\frac{2\lambda-1}{\lambda^2}.
\tag{14}
\]

Therefore every finitely supported real sequence `x` satisfies

\[
\sum_{j,k}x_jx_k s_\lambda(j-k)
\ge
\omega_\lambda\sum_jx_j^2.
\tag{15}
\]

### 4.2 Integer occupancy and the shorter-scale second moment

Consider a periodic/circulant idealization with `d` natural grid sites and integer occupancies `m_j>=0` satisfying

\[
\sum_jm_j=d=N.
\]

Write `x_j=m_j-1`, so `sum x_j=0`. Let the shorter-scale normalized second moment be

\[
F_\lambda
=
\sum_{j,k}m_jm_k s_\lambda(j-k).
\]

The constant mode has eigenvalue `1/lambda`, while (15) controls the mean-zero part. Hence

\[
F_\lambda
\ge
\frac{N}{\lambda}
+
\omega_\lambda\sum_j(m_j-1)^2.
\tag{16}
\]

For every integer `m>=0`,

\[
\mathbf1_{m=1}\ge1-(m-1)^2.
\]

Thus

\[
s_1\ge N-\sum_j(m_j-1)^2.
\tag{17}
\]

The Zeta23 prime-side second-moment constant at scale `lambda` is asymptotically

\[
\kappa_\lambda
=
\frac1\lambda+rac\lambda3.
\]

If the ideal shorter-scale model satisfies

\[
F_\lambda\le\kappa_\lambda N+o(N),
\]

then (16)–(17) imply

\[
\boxed{
\frac{s_1}{N}
\ge
1-rac{\lambda^3}{3(2\lambda-1)}-o(1).}
\tag{18}
\]

The right side is maximized at

\[
\lambda=\frac34,
\]

because `lambda^3/(2lambda-1)` has derivative proportional to `4lambda-3`. At this scale,

\[
\omega_{3/4}=\frac89,
\qquad
\kappa_{3/4}=\frac{19}{12},
\qquad
\sum_j(m_j-1)^2\le\frac9{32}N,
\]

and therefore

\[
\boxed{
\frac{s_1}{N}\ge\frac{23}{32}-o(1)=0.71875-o(1).}
\tag{19}
\]

### 4.3 Exact exclusion margin for the `2/3` clock extremizer

The pattern `(1,1,1,1,2,0)` has

\[
\frac1N\sum_j(m_j-1)^2=\frac13.
\]

At `lambda=3/4`, (16) forces

\[
\frac{F_{3/4}}N
\ge
\frac43+rac8{27}
=
\frac{44}{27}.
\]

But the prime-side upper constant is `19/12`. The exact gap is

\[
\frac{44}{27}-\frac{19}{12}
=
\frac5{108}>0.
\tag{20}
\]

This lower bound is arrangement-free: it excludes every permutation of the `0/1/2` extremal occupancy distribution, not only the six-periodic ordering.

### Emerging H4 verdict

`SUPPORTED IN THE IDEAL CRITICAL-LATTICE MODEL.` A second scale, unlike a second fixed-width taper at the same scale, detects the variance hidden by the `2/3` Nyquist extremizer. The elementary aliasing calculation has enough margin to suggest a genuine stability route.

It is **not yet a theorem about zeta zeros**. The unresolved bridge is now sharply localized:

1. derive an equality/near-equality normal form for the `lambda=1` Zeta23 certificate, including tight off-line pairs;
2. prove a quantitative critical-density sampling theorem that converts small `lambda=1` defect into an approximate natural-lattice occupancy model;
3. transfer the box-window inequality to the smooth fixed-width tapers and finite grids used by Zeta23 with `o(N)` loss;
4. control off-line complex ordinates under the `lambda=3/4` restriction;
5. propagate the resulting positive second-moment gap through the source's tail and prime-side seams.

The next decisive mathematical target is no longer a vague two-window separation statement. It is:

> **Critical-lattice extraction plus sub-Nyquist aliasing.** Show that any configuration whose `lambda=1`, `c=2` certificate is within `delta N` of equality is, after deleting/charging `O(delta N)` exceptional mass, close enough to an integer occupancy model that (16) survives at `lambda=3/4` with an error smaller than the exact margin `5N/108`.

---

## Current hypothesis table

| Hypothesis | Status | Scope |
|---|---|---|
| H1: scalar threshold optimization beats `c=2` | REFUTED | existing first/second moments and inertia |
| H2: grid-phase shift creates separation | REFUTED | complete Poisson frame |
| H3: finitely many same-scale fixed-width tapers force macro defect | REFUTED | complete-frame zero-side model |
| H4: a shorter scale detects the Nyquist extremizer | SUPPORTED | ideal box-window critical lattice; not yet ζ |

## Immediate next work

- commit the deterministic checker for (5), (13)–(20), the clock pattern and fixed-width Parseval scaling;
- write the exact equality normal form implied jointly by the parent defect decomposition and the count-bookkeeping equalities;
- test robust perturbations of the lattice model and estimate how much of the `5/108` margin is available for extraction and tail errors;
- search for the closest existing nonharmonic-Fourier stability theorem, while treating applicability as unverified until quantifiers match.