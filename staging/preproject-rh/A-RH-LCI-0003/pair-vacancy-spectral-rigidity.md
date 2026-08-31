# A-RH-LCI-0003 — fixed-depth pair/vacancy spectral rigidity and scale-invariant pair phase

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

The preceding checkpoints refuted a period-independent global principal-angle
bound. This note records the positive structure that remains. In the ideal
long-scale box model, a fixed-depth pair/vacancy subsystem has an exact
nonnegative Fourier defect symbol. Its only zero is the constant mode.
Consequently, zero defect forces every stationary local limit of that subsystem
to be a mixture of two homogeneous phases: all pair or all vacancy.

The second result is equally important: a homogeneous lattice of off-line
reflection pairs is exactly the same signed frame operator as a tangent
load-two lattice, for every taper and every scale. Thus a macroscopic pair
phase does not corrupt the short-scale occupancy certificate; it becomes an
effective mark two.

This is a rigorous ideal-model bridge toward the collapsed-orbit compactness
program. It does not yet cover arbitrary simple sites, varying pair depths, or
the actual smooth finite Zeta23 compression.

---

## 1. Finite periodic pair/vacancy model

Fix a period `P >= 2` and the normalized Fourier basis of `C^P`,

\[
f_p(j)=P^{-1/2}\exp(2\pi i p j/P),
\qquad 0\le p,j<P.
\tag{1.1}
\]

Let

\[
\mathcal A\subset\mathbb Z/P\mathbb Z
\]

be the residues occupied by multiplicity-one off-line reflection pairs. Every
residue outside `A` is vacant in this subsection. Put

\[
m_p=\mathbf 1_{\mathcal A}(p),
\qquad
k=|\mathcal A|,
\tag{1.2}
\]

and let `Pi_A` be the Fourier projection onto
`span{f_p:p in A}`.

Choose a fiber phase

\[
x\in[-1/2,-1/2+1/P),
\qquad s_j=x+j/P,
\tag{1.3}
\]

and a fixed normalized horizontal depth `a >= 0`. Define diagonal
multiplication operators

\[
C_a=\operatorname{diag}(\cosh(a s_j)),
\qquad
S_a=\operatorname{diag}(\sinh(a s_j)).
\tag{1.4}
\]

The signed matrix of all pair orbits is

\[
\boxed{
G_{\mathcal A,a}
=2(C_a\Pi_{\mathcal A}C_a-S_a\Pi_{\mathcal A}S_a).
}
\tag{1.5}
\]

Each pair has count budget four and signed trace two. Hence

\[
\operatorname{tr}G_{\mathcal A,a}=2k
\tag{1.6}
\]

and its `c=2` count defect is

\[
\boxed{
\Delta_{P,a}(\mathcal A)
=4k-
\left(4\operatorname{tr}G_{\mathcal A,a}
      -\|G_{\mathcal A,a}\|_F^2\right)
=\|G_{\mathcal A,a}\|_F^2-4k.
}
\tag{1.7}
\]

The expression is independent of the fiber phase `x`.

---

## 2. Exact defect symbol

Use the normalized discrete Fourier coefficients

\[
\widehat m(\ell)
=\frac1P\sum_{p=0}^{P-1}
 m_p e^{-2\pi i\ell p/P}.
\tag{2.1}
\]

For `0 <= theta <= 1`, define

\[
\boxed{
H_a(\theta)
=2\left[
\theta\cosh(2a(1-\theta))
+(1-\theta)\cosh(2a\theta)-1
\right].
}
\tag{2.2}
\]

### Theorem A — exact periodic spectral formula

A direct Fourier calculation gives

\[
\boxed{
\frac{\Delta_{P,a}(\mathcal A)}P
=
\sum_{\ell=0}^{P-1}
H_a(\ell/P)|\widehat m(\ell)|^2.
}
\tag{2.3}
\]

One convenient derivation starts from the pair-orbit autocorrelation. If

\[
K_b(r)=\int_{-1/2}^{1/2}e^{bs}e^{2\pi i r s}\,ds,
\tag{2.4}
\]

then two equal-depth pair orbits separated by `r` have Frobenius interaction

\[
2K_0(r)^2+K_{2a}(r)^2+K_{-2a}(r)^2.
\tag{2.5}
\]

The circular convolution of `s -> e^{2as}` has value

\[
\theta e^{2a(\theta-1)}+(1-\theta)e^{2a\theta},
\tag{2.6}
\]

and adding the reflected exponential produces (2.2). Subtracting the tangent
value four yields the defect symbol.

At `a=0`,

\[
H_0\equiv0,
\tag{2.7}
\]

which recovers the fact that every tangent `0/2` occupancy pattern saturates
the long-scale scalar certificate.

---

## 3. Positivity and its unique zero

Let

\[
d(\theta)=\min(\theta,1-\theta).
\]

The symbol is symmetric under `theta -> 1-theta`. For
`0 <= theta <= 1/2`,

\[
\begin{aligned}
\frac12H_a(\theta)
&=
\theta\cosh(2a(1-\theta))
+(1-\theta)\cosh(2a\theta)-1\\
&\ge
\theta\cosh(a)+(1-\theta)-1.
\end{aligned}
\]

Therefore

\[
\boxed{
H_a(\theta)
\ge2(\cosh a-1)d(\theta).
}
\tag{3.1}
\]

For `a>0`, this implies

\[
H_a(\theta)>0
\qquad(0<\theta<1),
\tag{3.2}
\]

while

\[
H_a(0)=H_a(1)=0.
\tag{3.3}
\]

Thus exact finite nondegeneracy has a stronger stationary interpretation: the
only zero-energy Fourier mode is the constant mode. Slowly varying large
blocks may still have vanishing defect density because their spectrum
concentrates near zero; this is precisely the phase-separation phenomenon seen
in the earlier countermodels.

---

## 4. Quantitative boundary control

Define the cyclic nearest-neighbor boundary density

\[
b_P(\mathcal A)
=
\frac1P\sum_{p=0}^{P-1}|m_{p+1}-m_p|^2,
\qquad m_P=m_0.
\tag{4.1}
\]

Parseval gives

\[
b_P(\mathcal A)
=
\sum_{\ell=0}^{P-1}
4\sin^2(\pi\ell/P)|\widehat m(\ell)|^2.
\tag{4.2}
\]

Since

\[
4\sin^2(\pi\theta)
\le4\pi d(\theta),
\tag{4.3}
\]

(2.3) and (3.1) imply

\[
\boxed{
 b_P(\mathcal A)
\le
\frac{2\pi}{\cosh a-1}
\frac{\Delta_{P,a}(\mathcal A)}P
\qquad(a>0).
}
\tag{4.4}
\]

Hence positive-density pair/vacancy interfaces necessarily pay
positive-density long-scale defect. Conversely, a single number of
macroscopic interfaces may have total defect growing sublinearly and therefore
vanishing defect density, in agreement with local phase separation.

---

## 5. Stationary rigidity theorem

Let `(M_n)_{n in Z}` be a stationary `{0,1}`-valued process representing a
fixed-depth pair indicator. Let `sigma` be the spectral measure of the centered
process `M_n-E M_0` on the circle. Define the ideal defect density by

\[
\boxed{
\mathcal D_a(M)
=
\int_{\mathbb T}H_a(\theta)\,d\sigma(\theta).
}
\tag{5.1}
\]

Finite periodic laws satisfy this formula by (2.3), and it extends to
stationary limits by the usual covariance/Herglotz passage.

The nearest-neighbor disagreement probability is

\[
\mathbb P(M_1\ne M_0)
=
\int_{\mathbb T}|e^{2\pi i\theta}-1|^2\,d\sigma(\theta).
\tag{5.2}
\]

Therefore (4.4) becomes

\[
\boxed{
\mathbb P(M_1\ne M_0)
\le
\frac{2\pi}{\cosh a-1}\mathcal D_a(M).
}
\tag{5.3}
\]

### Theorem B — zero-defect phase classification

If `a>0` and

\[
\mathcal D_a(M)=0,
\]

then

\[
M_{n+1}=M_n
\quad\text{almost surely for every }n.
\tag{5.4}
\]

Thus every sample is spatially constant. Every stationary zero-defect law is a
mixture of

\[
\text{all vacancy}
\qquad\text{and}\qquad
\text{all pair at depth }a.
\tag{5.5}
\]

In an ergodic component, exactly one of these two phases occurs.

This is the desired local-compactness mechanism for the fixed-depth pure
pair/vacancy sector: macroscopic phase drift is allowed, but a typical rooted
zero-defect limit cannot contain a genuine pair/vacancy interface.

---

## 6. Homogeneous pair phase is scale-invariant

Let `H=L^2(T)` on a unit circle, let `(e_p)_{p in Z}` be its Fourier basis, and
let `psi` be any real bounded taper. Put

\[
X_p=\psi(s)\cosh(as)e_p(s),
\qquad
Y_p=-i\psi(s)\sinh(as)e_p(s).
\tag{6.1}
\]

In weak operator topology, Fourier completeness gives

\[
\sum_p |X_p\rangle\langle X_p|
=M_{\psi^2\cosh^2(as)},
\tag{6.2}
\]

\[
\sum_p |Y_p\rangle\langle Y_p|
=M_{\psi^2\sinh^2(as)}.
\tag{6.3}
\]

Consequently the signed operator of a homogeneous reflection-pair lattice is

\[
\boxed{
2\sum_p
\left(
|X_p\rangle\langle X_p|
-|Y_p\rangle\langle Y_p|
\right)
=2M_{\psi^2}.
}
\tag{6.4}
\]

The right side is exactly the frame operator of a tangent load-two lattice:

\[
2\sum_p|\psi e_p\rangle\langle\psi e_p|
=2M_{\psi^2}.
\tag{6.5}
\]

### Corollary — depth disappears inside a homogeneous phase

For every depth `a`, every taper, and every scale,

\[
\boxed{
\text{homogeneous off-line pair lattice}
\equiv
\text{tangent load-two lattice}
}
\tag{6.6}
\]

at the signed operator level.

For the normalized short box taper

\[
\psi_\alpha=\alpha^{-1/2}\mathbf1_{[-\alpha/2,\alpha/2]},
\]

the common operator is

\[
2\alpha^{-1}M_{\mathbf1_{[-\alpha/2,\alpha/2]}}.
\tag{6.7}
\]

Thus the short-scale energy of the all-pair phase is exactly the same as the
energy assigned to mark two in the tangent occupancy model. No separate depth
penalty or correction is required inside that homogeneous phase.

---

## 7. Consequence for the two-scale program

The global principal-angle route failed because long pair blocks can become
nearly parallel to the positive span. The spectral theorem explains why this
does not automatically destroy the two-scale route.

A long fixed-depth pair block has defect concentrated at its interfaces. After
uniform random rooting, the block interior converges to the homogeneous
all-pair phase, while the complement converges to homogeneous vacancy or other
tangent phases. Equation (6.6) then turns the pair phase into an effective
load-two mark at the shorter scale.

This suggests the following ideal collapsed-orbit compactness architecture:

1. fixed-depth pair/vacancy interfaces are charged by (4.4);
2. vanishing long-scale defect produces homogeneous pair phases in local weak
   limits;
3. homogeneous pair phases are replaced exactly by tangent mark two through
   (6.6);
4. the existing `lambda=3/4` stationary-lattice Fourier inequality charges the
   resulting `0/1/2` mark variance by the same `5/108` margin.

The centered weighted trace remains relevant for varying or unbounded depths,
but it is no longer needed merely to understand a homogeneous fixed-depth pair
phase.

---

## 8. Deterministic checker

Run

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_pair_vacancy_spectrum.py
```

The checker verifies:

- (2.3) against direct finite matrix construction for random periods, subsets,
  phases, and depths;
- positivity, symmetry, and the lower bound (3.1);
- the boundary inequality (4.4);
- exact zero defect for all-vacancy and all-pair states;
- the homogeneous operator identity (6.4) on finite Fourier grids;
- macroscopic block examples whose boundary and defect densities vanish.

The computation is a regression harness, not an independent proof.

---

## 9. Authority boundary

Proof candidates/exact identities in this checkpoint:

- the finite defect symbol (2.2)--(2.3);
- symbol positivity and the quantitative lower bound (3.1);
- nearest-neighbor boundary control (4.4);
- stationary zero-defect phase classification (5.3)--(5.5);
- homogeneous pair/load-two operator identity (6.4)--(6.6).

Still open:

- mixed simple, tangent-double, pair, and vacancy states in one stationary law;
- pair depths that vary with the lattice site or diverge with `T`;
- smooth-taper and finite-section error transfer from actual Zeta23 matrices;
- a full collapsed-orbit compactness theorem with exceptional mass;
- closure of the `5/108` source-level error budget.

This note proves no statement about the actual location of zeta zeros and does
not improve an unconditional critical-line proportion or prove RH.
