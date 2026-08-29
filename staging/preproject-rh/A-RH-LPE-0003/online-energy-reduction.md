# On-line Gram-energy reduction to the off-line negative spectrum

Status: `proof_candidate` — finite algebra conditional on the parent defect identity; not independently verified

Attempt: `A-RH-LPE-0003`

Parent inputs:

- `A-RH-RTD-0001@2f2ecdac7aec73d3996d3484e7a56b051a718f11`
- `A-RH-RTD-0002@698d28d4e074f09fdb7dfdaffc65df1cdc94727b`

This note identifies a direct route from the parent rank--trace defect to the long-scale on-line off-diagonal Gram energy required by the phase-extraction theorem. It removes the earlier auxiliary assumption that every atom load is at most two.

Nothing here proves that the relevant defect or off-line negative spectrum is small for the actual Zeta23 matrices.

## 1. Setup

Let

\[
P=\sum_{j=1}^s m_jv_jv_j^*\succeq0,
\qquad
m_j\in\mathbb Z_{>0},
\]

and define the atom loads

\[
a_j=m_j\|v_j\|^2.
\]

The weighted off-diagonal atom Gram energy is

\[
E_{\rm off}
:=
\sum_{i\ne j}m_im_j|\langle v_i,v_j\rangle|^2.
\tag{1.1}
\]

Since

\[
\operatorname{tr}(P^2)
=
\sum_{i,j}m_im_j|\langle v_i,v_j\rangle|^2,
\]

we have the exact identity

\[
E_{\rm off}
=
\operatorname{tr}(P^2)-\sum_ja_j^2.
\tag{1.2}
\]

For the simple-zero threshold `c=2`, put

\[
A=(P-2I)_+,
\qquad
L_{\rm load}=\sum_j(a_j-2)_+^2.
\tag{1.3}
\]

Let

\[
g_2(x)=x^2-2x-(x-2)_+^2
\]

and let the parent Schur-transfer defect be

\[
J_2=\operatorname{tr}g_2(P)-\sum_jg_2(a_j)\ge0.
\tag{1.4}
\]

## 2. Exact on-line energy identity

### Proposition 2.1

For arbitrary positive atom loads `a_j`, with no assumption `a_j<=2`,

\[
\boxed{
J_2
=E_{\rm off}-\|A\|_F^2+L_{\rm load}.}
\tag{2.1}
\]

Equivalently,

\[
\boxed{
E_{\rm off}
=J_2+\|A\|_F^2-L_{\rm load}.}
\tag{2.2}
\]

### Proof

By functional calculus,

\[
\operatorname{tr}g_2(P)
=
\operatorname{tr}(P^2)-2\operatorname{tr}P-\|A\|_F^2.
\]

On the atom side,

\[
\sum_jg_2(a_j)
=
\sum_ja_j^2-2\sum_ja_j-L_{\rm load}.
\]

Because

\[
\sum_ja_j=\operatorname{tr}P,
\]

subtracting the two expressions and using (1.2) proves (2.1).

### Consequence

The load leakage `L_load` has the favorable sign. Hence

\[
\boxed{
E_{\rm off}
\le J_2+\|A\|_F^2.}
\tag{2.3}
\]

Thus large individual loads do not obstruct the reduction; they can only lower the off-diagonal energy compatible with fixed `J_2` and `A`.

## 3. Reduction using the exact rank--trace defect

Let `Q=Q_+-Q_-` be the Jordan decomposition of the off-line pair form, and let `Delta_2` be the parent exact rank--trace defect. The candidate decomposition in `A-RH-RTD-0001` contains the nonnegative terms

\[
J_2
\quad\text{and}\quad
\|Q_--A\|_F^2.
\]

Therefore

\[
J_2\le\Delta_2,
\qquad
\|Q_--A\|_F\le\sqrt{\Delta_2}.
\tag{3.1}
\]

Combining (2.3) and (3.1) yields the sharp intermediate bound

\[
\boxed{
E_{\rm off}
\le
\Delta_2+
\left(\|Q_-\|_F+\sqrt{\Delta_2}\right)^2.}
\tag{3.2}
\]

Using `2xy<=x^2+y^2`, we obtain the simpler linear-energy estimate:

### Theorem 3.1

\[
\boxed{
E_{\rm off}
\le
2\|Q_-\|_F^2+3\Delta_2.}
\tag{3.3}
\]

Equivalently,

\[
\boxed{
\|Q_-\|_F^2
\ge
\frac12\left(E_{\rm off}-3\Delta_2\right)_+.}
\tag{3.4}
\]

Equation (3.4) is a precise dichotomy: after the rank--trace defect is small, failure of small on-line Gram energy forces macroscopic negative spectral energy in the off-line pair form.

## 4. Normalized asymptotic form

Let `N` denote the total zero multiplicity in the height window and define

\[
e_{\rm off}=\frac{E_{\rm off}}N,
\qquad
q_- =\frac{\|Q_-\|_F^2}{N},
\qquad
\delta=\frac{\Delta_2}{N}.
\]

Then

\[
\boxed{
e_{\rm off}\le2q_-+3\delta.}
\tag{4.1}
\]

In particular,

\[
\delta=o(1),
\qquad q_-=o(1)
\quad\Longrightarrow\quad
E_{\rm off}=o(N).
\tag{4.2}
\]

Under the ideal sinc-kernel identification required by `phase-synchronization.md`, the random-partition theorem may then be applied with

\[
e=2q_-+3\delta.
\]

For every fixed local observation radius `r`, the balanced choices

\[
R=e^{-1/5},
\qquad
\eta=e^{1/5}
\]

give a deleted mass fraction at most

\[
\boxed{
\left(\frac{\pi^2}{2}+2r\right)
(2q_-+3\delta)^{1/5},}
\tag{4.3}
\]

and the same order of local lattice-position error.

Thus the long-scale extraction bridge is reduced to controlling two normalized quantities, not to proving an independent inverse theorem from scratch:

```text
rank--trace defect delta -> 0
and off-line negative energy q_- -> 0
  => on-line off-diagonal Gram energy -> 0
  => quantitative local critical-lattice extraction.
```

## 5. What near saturation supplies and what it does not

Approaching the one-scale simple-zero lower bound is expected to force `delta->0` only after all count slack, prime-side error, trace normalization, atom-load leakage and seam/tail terms have been reconciled. That implication remains part of the parent verification and analytic ledger.

Even if `delta->0`, equation (3.3) does **not** make `q_-` small. The parent defect merely forces

\[
Q_-\approx(P-2I)_+.
\]

Both matrices may retain macroscopic Frobenius energy. Therefore the decisive remaining obstruction is now explicit:

> Can a positive density of off-line reflection pairs generate macroscopic `Q_-` while simultaneously satisfying the complete-frame pair geometry, the growing finite-section constraints, and both long- and short-scale prime-side moment bounds?

## 6. Relation to complete-frame pair inertia

The companion note `pair-inertia-and-finite-sections.md` proves, as a separate candidate, that `p` distinct off-line reflection pairs have complete-frame inertia exactly `(p,p)`. If a finite synthesis matrix satisfies

\[
U_d^*U_d\succeq A I
\]

and the minimum pair multiplicity is `m_min`, then

\[
\|Q_{d,-}\|_F^2
\ge pA^2m_{\min}^2.
\tag{6.1}
\]

This is a **lower** bound on negative energy. It does not close (4.2). Its value is diagnostic:

- if `q_-=o(1)` and a nondegenerate lower Riesz bound survives, then only `o(N)` off-line pair mass can remain away from the coalescing/degenerate regime;
- if a positive density of pairs remains, their finite-section lower Riesz constants or divided-difference depth weights must degenerate;
- such degeneration becomes the next object for the short-scale compression to detect.

For divided-difference coordinates, a depth decomposition can aim for a bound of the form

\[
\|Q_{d,-}\|_F^2
\gtrsim
A^2\sum_r m_r^2\min(a_r^4,1),
\tag{6.2}
\]

where `a_r` is normalized horizontal depth. Establishing (6.2) uniformly for the actual growing family remains open.

## 7. Refined research dichotomy

The combined parent and current machinery suggests the following exact decision tree.

### Branch A: small off-line negative energy

If

\[
\Delta_2=o(N),
\qquad
\|Q_-\|_F^2=o(N),
\]

then Theorem 3.1 gives `E_off=o(N)`. The random-partition theorem produces blockwise critical-lattice occupancies after deleting `o(N)` mass. The remaining work is the smooth-kernel, finite-Toeplitz, deleted-mass and short-scale error budget.

### Branch B: macroscopic off-line negative energy

If local lattice extraction fails while `Delta_2=o(N)`, then (3.4) forces

\[
\|Q_-\|_F^2\gg N.
\]

The route must then prove that such a macroscopic negative part creates one of:

1. a long/short-scale incompatibility in `Q_-`;
2. a positive finite-section/divided-difference depth cost;
3. a contradiction with the short-scale prime-side second moment;
4. a zero-density consequence that confines essentially all pair mass to an increasingly thin critical-line neighborhood.

This is a narrower and testable frontier than the earlier generic request for “two-window separation.”

## 8. Exact next lemma

A sufficient next theorem is:

> **Negative-pair-energy transfer lemma.** For a fixed reference scale `theta` sufficiently close to one and relative scale `3/4`, prove either
> \[
> \|Q_{-,\theta}\|_F^2=o(N),
> \]
> or a quantitative inequality showing that macroscopic `\|Q_{-,\theta}\|_F^2` forces a normalized short-scale excess larger than all extraction, taper, finite-section and seam losses.

A weaker dyadic-depth statement may suffice:

\[
\sum_r m_r^2\min(a_r^4,1)=o(N)
\quad\Longrightarrow\quad
q_-=o(1),
\]

combined with a separate contradiction for any depth bin carrying positive density.

## 9. Authority and non-implication boundary

Established only as a solver proof candidate, conditional on the parent exact defect decomposition:

- the general identity (2.1)--(2.2);
- the reduction (3.2)--(3.4);
- the normalized extraction implication (4.1)--(4.3).

Not established:

- that actual near saturation implies `Delta_2=o(N)` after all source errors;
- that the actual off-line negative energy is `o(N)`;
- a uniform finite-section Riesz or divided-difference estimate;
- transfer from the smooth Zeta23 taper to the ideal sinc energy within the parent budget;
- any unconditional improvement in the zeta-zero proportion;
- a proof or refutation of the Riemann hypothesis.
