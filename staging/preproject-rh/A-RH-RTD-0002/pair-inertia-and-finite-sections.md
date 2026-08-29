# Complete-frame pair inertia and the finite-section frontier

Status: `proof_candidate` — exact Hilbert-space argument, not independently verified

Parent attempt: `A-RH-RTD-0002`

This note resolves an ambiguity exposed by the abstract two-pair cancellation model. Abstract hyperbolic blocks can cancel their negative directions, but the blocks coming from a **complete Fourier/Poisson analysis frame** carry additional linear-independence structure.

## 1. Complete analysis vectors

Let `phi` be a real taper supported in `[-L/2,L/2]` and nonzero almost everywhere on some nonempty open subinterval `J`. Use the paper Fourier convention

\[
\widehat\phi(z)=\int_{-L/2}^{L/2}\phi(u)e^{izu}\,du.
\]

For a complex frequency `z` and a complete grid

\[
\tau_k=T+\frac{2\pi k}{L},
\qquad k\in\mathbb Z,
\]

define

\[
V(z)_k=\widehat\phi(z-\tau_k).
\]

Up to the harmless normalization `L^(1/2)`, `V(z)` is the full Fourier-coefficient sequence of

\[
f_z(u)=\phi(u)e^{i(z-T)u}
\]

in the orthonormal Fourier basis of `L^2[-L/2,L/2]`.

## 2. Linear independence theorem

### Theorem 2.1

For pairwise distinct complex numbers `z_1,...,z_r`, the vectors

\[
V(z_1),\ldots,V(z_r)\in\ell^2(\mathbb Z)
\]

are linearly independent.

### Proof

Suppose

\[
\sum_{j=1}^r c_jV(z_j)=0.
\]

Every Fourier coefficient of

\[
F(u)=\phi(u)\sum_{j=1}^r c_je^{i(z_j-T)u}
\]

vanishes. Completeness of the Fourier basis gives `F=0` in `L^2[-L/2,L/2]`. On `J`, where `phi` is nonzero almost everywhere,

\[
\sum_{j=1}^r c_je^{iz_ju}=0
\]

almost everywhere. The left side is an exponential polynomial, hence real-analytic on the real interval and entire in `u`; it therefore vanishes identically. Evaluating its first `r` derivatives at any point produces a Vandermonde system in the distinct numbers `z_j`, so every `c_j=0`.

## 3. Exact inertia of complete off-line pair forms

Let `z_1,...,z_p` lie off the real axis, and assume that the `2p` frequencies

\[
z_1,\overline z_1,\ldots,z_p,\overline z_p
\]

are pairwise distinct. Let `m_r>0` be the pair multiplicities. Form the synthesis map

\[
U:\mathbb C^{2p}\to\ell^2(\mathbb Z)
\]

whose columns are

\[
V(z_1),V(\overline z_1),\ldots,V(z_p),V(\overline z_p).
\]

For real `phi`,

\[
V(\overline z)=\overline{V(z)}.
\]

Put

\[
H=\bigoplus_{r=1}^p
m_r\begin{pmatrix}0&1\\1&0\end{pmatrix}.
\]

Then the complete pair form is

\[
Q_\infty=UHU^*.
\tag{3.1}
\]

Indeed, one block contributes

\[
m_r\bigl(
V(z_r)V(\overline z_r)^*
+V(\overline z_r)V(z_r)^*
\bigr),
\]

which is the Hermitian representation of the source's
`v v^T + conjugate(v) conjugate(v)^T` pair term.

### Theorem 3.1

The finite-rank Hermitian operator `Q_infty` has

\[
n_+(Q_\infty)=p,
\qquad
n_-(Q_\infty)=p.
\tag{3.2}
\]

### Proof

Theorem 2.1 makes `U` injective, so its Gram matrix

\[
G=U^*U
\]

is positive definite. The nonzero part of `Q_infty` is unitarily equivalent to

\[
G^{1/2}HG^{1/2}.
\]

This matrix is congruent to `H`. Sylvester inertia therefore gives the same positive and negative indices as `H`, namely `(p,p)`.

### Consequence

The abstract cancellation model

\[
Q_1+Q_2=2I
\]

with two individually nontrivial hyperbolic blocks cannot be realized by a finite family of distinct frequencies in the **complete** analysis frame. Its cancellation exploits a rank collapse forbidden by Theorem 2.1.

This does not invalidate the abstract countermodel. It identifies exactly where additional structure enters: finite coordinate compression may destroy injectivity or make the synthesis map arbitrarily ill-conditioned.

## 4. Finite sections

Let `Pi_d` project onto a chosen finite set of grid coordinates and define

\[
U_d=\Pi_dU,
\qquad
Q_d=U_dHU_d^*.
\]

If `U_d` has full column rank, the same congruence proof gives

\[
n_+(Q_d)=n_-(Q_d)=p.
\tag{4.1}
\]

Thus the source's bound `n_+(Q_d)<=p` is exact whenever the selected finite section retains all pair columns independently.

The issue is quantitative and uniform: in the Zeta23 regime both `d` and `p` grow with height, and the relevant lower singular value may tend to zero.

## 5. A quantitative singular-value implication

Assume

\[
G_d=U_d^*U_d\succeq A I
\tag{5.1}
\]

for some `A>0`, and let

\[
m_{\min}=\min_r m_r.
\]

The nonzero eigenvalues of `Q_d` are those of

\[
B_d=G_d^{1/2}HG_d^{1/2}.
\]

Since

\[
B_d^{-1}=G_d^{-1/2}H^{-1}G_d^{-1/2},
\]

we have

\[
\|B_d^{-1}\|
\le\frac1{A m_{\min}}.
\]

Therefore every nonzero eigenvalue of `Q_d` has magnitude at least `A m_min`, and in particular

\[
\|Q_{d,-}\|_F^2
\ge
pA^2m_{\min}^2.
\tag{5.2}
\]

Consequently, an aggregate near-equality condition forcing `||Q_{d,-}||_F^2=o(N)` can coexist with a positive density of genuinely off-line pairs only if the pair synthesis lower bound `A` degenerates.

## 6. Coalescing pairs and divided differences

When

\[
z_r=x_r-ia_r,
\qquad
\overline z_r=x_r+ia_r,
\]

the two raw columns coalesce as `a_r->0`. Introduce instead

\[
C_r=\frac{V(z_r)+V(\overline z_r)}2,
\]

\[
D_r=\frac{V(z_r)-V(\overline z_r)}{2ia_r}.
\]

The second vector has a finite limit proportional to the Fourier coefficients of

\[
u\phi(u)e^{i(x_r-T)u}.
\]

In the `(C_r,D_r)` coordinates, the pair signature is

\[
2\begin{pmatrix}1&0\\0&-a_r^2\end{pmatrix}.
\tag{6.1}
\]

This separates geometric degeneracy from horizontal depth. If the combined family of exponentials and normalized divided differences has a lower Riesz bound `A`, then pairs with `|a_r|>=a_0` contribute negative eigenvalues of magnitude at least a constant multiple of `A a_0^2`.

A dyadic depth decomposition would then convert small aggregate negative part into concentration of the pairs near the critical line.

## 7. Relation to existing nonharmonic Fourier theory

Kadets-type perturbation theorems control exponential bases when frequencies are uniformly close to the integer lattice. Avdonin-type theorems permit averaged perturbations. Work on exponential divided differences treats clusters of nearby frequencies and is structurally aligned with the normalized vectors `D_r` above.

However, these are primarily forward results: they assume an integer labelling, separation, or average perturbation condition and then prove a Riesz bound. The present route still needs an inverse step extracting such a labelling from the near-equality/near-orthogonality information supplied by the full-scale Zeta23 certificate.

## 8. Refined pair-disentanglement target

The pair problem can now be stated precisely.

> **Finite-section pair stability target.** Prove that, after deleting or charging `o(N)` exceptional pair mass, the growing finite synthesis matrices made from the Zeta23 vectors
> \[
> V_d(x_r-ia_r),\quad V_d(x_r+ia_r)
> \]
> or their normalized divided differences have a lower Riesz bound strong enough that
> \[
> \|Q_{d,-}\|_F^2=o(N)
> \]
> forces
> \[
> \sum_r \min(a_r^4,1)=o(N)
> \]
> and preferably
> \[
> \sum_r \min(a_r^2,1)=o(N).
> \]

A qualitative version may be sufficient for the stationary-limit contradiction: every finite marked cluster in a local weak limit with a nonzero-depth pair retains a negative direction by Theorem 3.1.

## 9. What this establishes and what it does not

Established as a proof candidate:

- complete analysis vectors at finitely many distinct complex frequencies are linearly independent;
- the complete off-line pair form has exact inertia `(p,p)`;
- a full-rank finite section also has inertia `(p,p)`;
- a finite-section lower singular value gives the explicit negative-part bound (5.2);
- normalized divided differences isolate the quadratic depth coefficient.

Not established:

- a uniform lower Riesz bound for the actual growing zeta-zero family;
- that the consecutive finite grid used by Zeta23 has full pair-column rank at every height;
- that the smooth taper and boundary truncation preserve a sufficient quantitative bound;
- any unconditional restriction on the number or depth of off-line zeta zeros;
- any improvement of the known simple-zero proportion or proof of RH.
