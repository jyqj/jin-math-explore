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

### Remaining work

- write a self-contained derivation/check of the bilinear identity (6);
- quantify the fixed-width multi-taper clock model for H3;
- determine whether direct sums or linear combinations contain genuinely new information or collapse to one effective taper;
- isolate the first surviving arithmetic observable after the zero-side no-go results.