# A-RH-LCI-0003 — source-compatible nested-scale collapse and correction of the aligned-channel surrogate

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint is a source-mapping correction to
`finite-alphabet-multiscale-rigidity.md`.

That earlier checkpoint is mathematically correct for an **aligned depth-channel
surrogate** in which every auxiliary channel keeps the same full Fourier basis
and replaces the normalized depth `a` by `alpha*a`. It proved that `M-1` such
independent channels classify an `M`-depth alphabet.

An actual shorter Zeta23 support does something different. On one master
critical lattice, shortening the support restricts the same Fourier frame to a
smaller row section. At a fixed master-lattice frequency it changes only a
nonnegative diagonal weight; it does **not** replace `cosh(theta*a)` by an
independent moment `cosh(alpha*theta*a)`.

The resulting correction is decisive:

> A bank of nested support lengths on one master critical lattice collapses to
> one hyperbolic depth-moment channel at each master frequency. One full support
> adds its conjugate high-frequency channel, but any fixed collection of proper
> shorter supports adds no new low-frequency depth moment.

Consequently the currently preferred support pair `{1,3/4}` cannot by itself
supply the two independent endpoint moments needed for a robust three-depth
interface theorem. The centered weighted trace, an asymmetric/derivative
window, or another genuinely independent observable is essential.

This correction is additive. It does not delete the aligned-channel theorem;
it narrows its source relevance.

---

## 1. One master lattice and a partial Fourier section

Fix a master period `P>=2`. For a row count

\[
1\le d\le P,
\qquad
\alpha=\frac dP,
\tag{1.1}
\]

put

\[
s_j=\frac{j-(d-1)/2}{P},
\qquad0\le j<d,
\tag{1.2}
\]

and define the `d x P` partial Fourier frame

\[
f_p^{(d)}(j)
=P^{-1/2}e^{2\pi i pj/P},
\qquad0\le p<P.
\tag{1.3}
\]

Its rank-one atoms are

\[
U_p^{(d)}
=|f_p^{(d)}\rangle\langle f_p^{(d)}|.
\tag{1.4}
\]

The rows are orthonormal, so

\[
\boxed{
\sum_{p=0}^{P-1}U_p^{(d)}=I_d.
}
\tag{1.5}
\]

For a master-normalized horizontal depth `a>=0`, define

\[
C_a^{(d)}=\operatorname{diag}(\cosh(a s_j)),
\qquad
S_a^{(d)}=\operatorname{diag}(\sinh(a s_j)),
\tag{1.6}
\]

and

\[
B_{p,a}^{(d)}
=2\left(
C_a^{(d)}U_p^{(d)}C_a^{(d)}
-
S_a^{(d)}U_p^{(d)}S_a^{(d)}
\right).
\tag{1.7}
\]

For every fixed depth `a`, completeness gives

\[
\boxed{
\sum_{p=0}^{P-1}B_{p,a}^{(d)}=2I_d.
}
\tag{1.8}
\]

This is the finite nested-section version of homogeneous pair/load-two scale
invariance.

Let every master residue `p` carry a depth `a_{ell_p}` from a finite alphabet.
Set

\[
G_d=\sum_{p=0}^{P-1}B_{p,a_{\ell_p}}^{(d)}
\tag{1.9}
\]

and define the depth-heterogeneity excess

\[
\boxed{
E_d=\|G_d-2I_d\|_F^2.
}
\tag{1.10}
\]

`E_d` is not by itself the entire short-scale Zeta23 count defect; normalization
leakage and the prime-side scalar budget remain separate. It is the exact
operator excess that a depth-rigidity argument would need to control.

---

## 2. Exact partial-section symbol

For matrix row difference `n=j-k`, the hyperbolic identity gives

\[
\boxed{
(G_d)_{jk}
=\frac2P\sum_{p=0}^{P-1}
 e^{2\pi i pn/P}
 \cosh\!\left(a_{\ell_p}\frac nP\right).
}
\tag{2.1}
\]

Let the class indicators and normalized master DFT be

\[
m_r(p)=\mathbf1_{\{\ell_p=r\}},
\qquad
z_r(n)=\frac1P\sum_{p=0}^{P-1}
 m_r(p)e^{2\pi i pn/P}.
\tag{2.2}
\]

Write

\[
A_n
=\sum_rz_r(n)\cosh(a_r n/P).
\tag{2.3}
\]

The diagonal entries of `G_d` are exactly two. There are `d-n` entries on each
of the two matrix diagonals with ordinary difference `+n` and `-n`. Therefore:

### Theorem A — exact nested partial-frame excess

\[
\boxed{
E_d
=8\sum_{n=1}^{d-1}(d-n)|A_n|^2.
}
\tag{2.4}
\]

Equivalently, with `theta_n=n/P`,

\[
\boxed{
\frac{E_d}{P}
=8\sum_{n=1}^{d-1}
(\alpha-\theta_n)
\left|
\sum_rz_r(n)\cosh(a_r\theta_n)
\right|^2.
}
\tag{2.5}
\]

The depth moment in (2.5) is independent of the support ratio `alpha`; only the
range `theta<alpha` and the scalar weight `alpha-theta` change.

This is the source-compatible distinction from the aligned-channel surrogate.

---

## 3. Any nested support bank collapses to one channel

Take row counts

\[
d_1,\ldots,d_q\le P
\]

and positive weights `w_j`. Combining (2.4),

\[
\boxed{
\sum_{j=1}^qw_jE_{d_j}
=8\sum_{n=1}^{d_{\max}-1}
W_n
\left|
\sum_rz_r(n)\cosh(a_r n/P)
\right|^2,
}
\tag{3.1}
\]

where

\[
\boxed{
W_n
=\sum_{j=1}^qw_j(d_j-n)_+.
}
\tag{3.2}
\]

Thus every proper nested support contributes a row proportional to the same
moment vector

\[
\bigl(\cosh(a_1\theta_n),\ldots,
      \cosh(a_M\theta_n)\bigr).
\tag{3.3}
\]

At a fixed master frequency, the channel rank remains one no matter how many
proper support lengths are stacked.

The full support `d=P` contains both a low frequency `n` and its conjugate
frequency `P-n`. Pairing them gives the two moments

\[
\cosh(a_r\theta),
\qquad
\cosh(a_r(1-\theta)),
\tag{3.4}
\]

which produced the binary two-depth symbol of the previous checkpoints.
Proper fixed-ratio supports do not add further moment functions to this pair.

---

## 4. Low-frequency rank of an actual fixed support bank

Assume the bank contains one full support and any finite collection of proper
fixed ratios

\[
\alpha_j<1.
\]

At a master frequency `theta downarrow 0`:

- every proper support contributes only
  \(\sum_rz_r\cosh(a_r\theta)\);
- the full support contributes that same low moment plus the conjugate moment
  \(\sum_rz_r\cosh(a_r(1-\theta))\).

Let there be at least three distinct depth classes. The `2 x M` endpoint matrix

\[
\begin{pmatrix}
1&\cdots&1\\
\cosh(a_1)&\cdots&\cosh(a_M)
\end{pmatrix}
\tag{4.1}
\]

has a nonzero null vector `z` satisfying

\[
\sum_rz_r=0,
\qquad
\sum_rz_r\cosh(a_r)=0.
\tag{4.2}
\]

For this vector,

\[
\sum_rz_r\cosh(a_r\theta)=O(\theta^2)
\tag{4.3}
\]

and

\[
\sum_rz_r\cosh(a_r(1-\theta))=O(\theta).
\tag{4.4}
\]

All proper-support contributions are therefore `O(theta^4)`, while the full
support's conjugate term is `theta O(theta^2)=O(theta^3)`. Hence:

### Theorem B — source-compatible three-depth endpoint obstruction

For every finite fixed-ratio nested support bank containing at most the usual
full-support conjugate channel, and every depth alphabet with `M>=3`, there is a
nonzero depth-class tangent direction such that

\[
\boxed{
Q_{\rm nested,\theta}(z)=O(\theta^3),
\qquad
\frac{Q_{\rm nested,\theta}(z)}\theta\longrightarrow0.
}
\tag{4.5}
\]

Thus no nearest-neighbor depth-interface estimate of the form

\[
Q_{\rm nested,\theta}(z)
\ge c\min(\theta,1-\theta)\|z\|^2
\tag{4.6}
\]

can hold for three arbitrary depth classes merely by adding proper nested
support lengths.

The obstruction is stronger than the aligned-surrogate scale count. In the
actual nested-section geometry, `{1,3/4}` does not behave like two independent
cosh-moment scales near zero; it behaves like one full two-channel system plus
a reweighting of its already existing low channel.

---

## 5. What remains valid from the preceding aligned theorem

`finite-alphabet-multiscale-rigidity.md` remains correct under its explicit
surrogate model:

\[
\cosh(a\theta)
\longmapsto
\cosh(\alpha_j a\theta)
\tag{5.1}
\]

while keeping a common full Fourier basis. Such genuinely independent depth
responses could arise from:

- a new family of operators, not merely nested support restriction;
- differentiated or asymmetric test windows;
- a controlled complex deformation of the test function;
- additional weighted traces;
- another source identity that changes the horizontal-depth response while
  preserving a common residue field.

What is withdrawn as a source inference is the claim that ordinary support
ratios `1` and `3/4` automatically instantiate those independent channels.
They do not in the master-lattice partial-frame model.

---

## 6. Consequence for the preferred RH route

The corrected architecture is now:

1. use the full `lambda=1` scalar defect for local random-coset collapse and
   binary pair/tangent phase classification;
2. use `lambda=3/4` for the occupancy/Fourier-variance `5/108` gap and for its
   favorable weighted-tail exponent;
3. do **not** count the shorter support as a second independent depth moment;
4. obtain the missing third depth channel from the centered frequency-square
   trace or another derivative/asymmetric observable;
5. only after that new channel is established, revisit a coarse finite-depth
   alphabet or continuum-depth compactness theorem.

The centered trace derived earlier has exactly the missing qualitative feature:
its zero-side contribution contains

\[
-2\sum_pn_p\delta_p^2
\]

linearly and additively, rather than another reweighting of
`cosh(theta*a)`.

This checkpoint therefore raises the priority of the source-side centered
weighted trace from a useful supplement to an essential independent channel.

---

## 7. A possible escape through almost-full supports

The endpoint obstruction assumes a fixed finite bank of proper ratios bounded
away from one. If a row count satisfies

\[
P-d=O(1)
\tag{7.1}
\]

or more generally `P-d=o(P)`, then the partial section may include the
conjugate frequency `P-n` for an increasing low-frequency range. Such
almost-full supports can change the endpoint channel count.

They are not the current `lambda=3/4` regime, and their prime-side gain over the
full scale is correspondingly small. A future attempt may optimize the tradeoff

\[
\text{new conjugate frequencies}
\quad\text{versus}\quad
\text{vanishing scale separation}.
\]

No positive result for this regime is asserted here.

---

## 8. Deterministic checks

Run

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_nested_scale_collapse.py
```

The checker verifies:

1. the direct partial-frame identity (2.4) on random finite configurations;
2. exact collapse of a random nested support bank to the scalar weights (3.2);
3. numerical rank one of all proper-support rows at one master frequency;
4. a three-depth endpoint-null vector for one full support plus several proper
   supports, with `Q_theta/theta -> 0`.

Recorded default regression:

```text
partial direct/spectral residual       2.274e-13
nested-bank direct/collapsed residual  1.819e-11
proper-support channel rank            1
combined Q/theta at theta=1e-4         2.965e-08
```

The checker validates the finite algebra and the explicit obstruction. It does
not establish smooth-taper or prime-side transfer.

---

## 9. Authority boundary

Exact identities/proof candidates recorded here:

- partial-frame completeness and homogeneous pair/load-two identity;
- the exact nested-section symbol (2.4)--(2.5);
- collapse of every finite nested support bank to the weights (3.1)--(3.2);
- the low-frequency three-depth endpoint obstruction (4.5);
- the correction separating aligned depth channels from actual nested support
  scales.

Open:

- smooth taper rather than the ideal row restriction;
- whether taper-profile variation supplies independent depth channels;
- almost-full support ratios tending to one;
- the centered weighted trace on the prime side;
- finite-section, tail, normalization, and random-root transfer;
- closure of all losses inside `5/108`.

No unconditional zeta-zero proportion is improved, and this checkpoint does
not prove or refute the Riemann hypothesis.
