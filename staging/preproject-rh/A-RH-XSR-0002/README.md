# A-RH-XSR-0002 — threshold optimality and cross-scale rigidity

Status: `working_draft`

Issue: `#28`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-cross-scale-rigidity-02`

Frozen parent: `A-RH-RTD-0001 @ 2f2ecdac7aec73d3996d3484e7a56b051a718f11`

Pinned source: `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`

This is pre-genesis solver staging. Nothing below is a Project theorem, an independently verified result, an unconditional improvement of the zeta-zero proportion, or a proof of the Riemann hypothesis.

## 1. Exact scalar no-go: the threshold `c=2` is optimal for the simple-zero certificate

Let the normalized zero-side matrix be decomposed as in Zeta23, and let the rank–trace parameter be `c`. For `1 <= c <= 2`, the scalar function

\[
k_c(m)=c^2-(c-m)_+^2
\]

satisfies

\[
k_c(1)=2c-1,
\qquad
k_c(m)=c^2\quad(m\ge2).
\]

Writing `s_1` for the number of simple on-line points, `s_2` for the number of multiple on-line points and `p` for the number of off-line reflection pairs, the rank–trace right side is bounded by

\[
(2c-1)s_1+c^2s_2+c^2p.
\]

The multiplicity count obeys

\[
N\ge s_1+2s_2+2p.
\]

Therefore

\[
2c\,\operatorname{tr}G-\|G\|_F^2-\frac{c^2}{2}N
\le
A(c)s_1,
\qquad
A(c):=2c-1-\frac{c^2}{2}.
\tag{1.1}
\]

Assume only the asymptotic moment information consumed by `Assembly/Certificate.lean`,

\[
\operatorname{tr}G\ge(1-o(1))N,
\qquad
\|G\|_F^2\le(\kappa+o(1))N.
\]

Then (1.1) gives

\[
\frac{s_1}{N}
\ge
B_c(\kappa)-o(1),
\qquad
B_c(\kappa)
:=
\frac{2c-c^2/2-\kappa}{2c-1-c^2/2}.
\tag{1.2}
\]

Since

\[
B_c(\kappa)=1-\frac{\kappa-1}{A(c)},
\qquad
A'(c)=2-c\ge0,
\qquad
A(c)\le A(2)=1,
\]

for every `kappa >= 1`,

\[
\boxed{B_c(\kappa)\le B_2(\kappa)=2-\kappa.}
\tag{1.3}
\]

Thus changing the scalar threshold inside `[1,2]` cannot improve the Zeta23 simple-zero coefficient when only the same first and second moments are used.

The conclusion is unchanged for every nonnegative linear combination of such threshold inequalities. Indeed, for weights `w_i >= 0`, the combined coefficient is

\[
1-(\kappa-1)
\frac{\sum_iw_i}{\sum_iw_iA(c_i)}
\le2-\kappa,
\]

because `A(c_i) <= 1`.

For `0<c<1`, all positive integer multiplicities satisfy `k_c(m)=c^2`, so the scalar function does not distinguish simple from multiple points. For `c>=2`, the frozen exact model

\[
P=\operatorname{diag}(1,1,1,1,2),\qquad Q=0
\]

remains feasible and already has simple proportion `2/3`. Hence the threshold continuum, by itself, cannot remove the first attempt's no-go model.

### Consequence

The next gain cannot come from one more scalar choice of `c`, nor from a positive mixture of the existing first/second-moment count certificates. It must consume joint geometry, cross-scale information, a higher moment, or a new analytic constraint.

## 2. Exact rowwise Jensen/Bregman decomposition

Let

\[
P=WW^*,\qquad M=W^*W,
\]

where the atom Gram matrix `M` has diagonal

\[
a_j=M_{jj}=m_j\|v_j\|^2.
\]

Let `lambda_r` be the eigenvalues of `M`, let `U` diagonalize `M`, and put

\[
w_{jr}=|U_{jr}|^2,
\qquad
\sum_rw_{jr}=1,
\qquad
 a_j=\sum_rw_{jr}\lambda_r.
\]

For

\[
g_c(x)=x^2-cx-(x-c)_+^2,
\]

the Schur-transfer defect is

\[
J_c=\operatorname{tr}g_c(M)-\sum_jg_c(a_j)
    =\sum_jJ_{c,j},
\]

where

\[
J_{c,j}=\sum_rw_{jr}D_c(\lambda_r\mid a_j)
\tag{2.1}
\]

and the exact Bregman gap is

\[
D_c(x\mid a)=
\begin{cases}
(x-a)^2,&a\le c,\ x\le c,\\
(c-a)^2+2(c-a)(x-c),&a\le c,\ x\ge c,\\
(c-x)^2,&a\ge c,\ x\le c,\\
0,&a\ge c,\ x\ge c.
\end{cases}
\tag{2.2}
\]

All four expressions are nonnegative. Formula (2.1) is an exact refinement of the Schur–Jensen step, not a numerical approximation.

### Equality classification

`J_c=0` if and only if every coordinate `e_j` obeys the following rule:

- if `a_j<c`, then `e_j` lies in the eigenspace of `M` with eigenvalue exactly `a_j`;
- if `a_j>=c`, then `e_j` lies entirely in the spectral subspace `[c,infinity)`.

In particular, every simple-zero atom in the `c=2` application has `a_j<=1<2`; exact Schur equality forces its Gram coordinate to be an eigenvector. Quantitatively, for `a_j<c`,

\[
\sum_{\substack{\lambda_r\le c\\|\lambda_r-a_j|\ge\delta}}w_{jr}
\le\frac{J_{c,j}}{\delta^2},
\qquad
\sum_{\lambda_r\ge c}w_{jr}
\le\frac{J_{c,j}}{(c-a_j)^2}.
\tag{2.3}
\]

For a simple atom at `c=2`, the second denominator is at least one.

### Equivalent Gram-energy formula

A second exact expression is

\[
J_c
=
\sum_{i\ne j}|M_{ij}|^2
-
\operatorname{tr}(M-cI)_+^2
+
\sum_j(a_j-c)_+^2.
\tag{2.4}
\]

Consequently, when `Q=0`, `b=0`, and every load `a_j<=c`, the *full* rank–trace defect from `A-RH-RTD-0001` is exactly

\[
\boxed{
\Delta_c=\sum_{i\ne j}|M_{ij}|^2.
}
\tag{2.5}
\]

No extra assumption `P<=cI` is needed for (2.5): the spectral-excess term in `J_c` is restored by the `||(P-cI)_+||_F^2` term in the full six-term defect decomposition.

## 3. Exact common-grid cross-Poisson kernel

Let `phi_1,phi_2` be real compactly supported functions on `[-L/2,L/2]`, with enough regularity for Poisson summation, and use the paper's Fourier convention

\[
\widehat\phi(z)=\int_{\mathbb R}\phi(u)e^{izu}\,du.
\]

For an arbitrary lattice origin `s`, put

\[
\tau_k=s+\frac{2\pi k}{L}.
\]

Then, first for real `x,y` and by holomorphic continuation wherever the series converges locally uniformly,

\[
\boxed{
\sum_{k\in\mathbb Z}
\widehat\phi_1(x-\tau_k)
\widehat\phi_2(y-\tau_k)
=
L\,\widehat{\phi_1(u)\phi_2(-u)}(x-y).
}
\tag{3.1}
\]

For even tapers this is `L * Fourier(phi_1 phi_2)(x-y)`.

The lattice origin `s` cancels exactly. This extends the same-taper identity proved in `Zeta23/Poisson.lean` and has three immediate implications for the full infinite grid.

### 3.1 Phase shifts do not change the bulk atom Gram matrix

For a fixed taper and scale, changing only the grid origin leaves all on-line atom inner products unchanged. Hence the nonzero spectrum of the corresponding on-line matrix `P` is unchanged. Any phase-shift gain must therefore come from finite truncation, tail/boundary effects, or genuinely different information on the off-line block; it cannot be a macroscopic bulk-Gram effect.

### 3.2 Linear combinations collapse to one taper

Coordinatewise,

\[
\alpha\widehat\phi_1+\beta\widehat\phi_2
=\widehat{\alpha\phi_1+\beta\phi_2}.
\]

Thus a linear combination of same-grid windows is exactly another single window.

### 3.3 Direct sums collapse at the Gram level

For a direct-sum atom vector

\[
v(\gamma)=\bigoplus_i\alpha_i v_{\phi_i}(\gamma),
\]

the Gram kernel is

\[
L\,\widehat{\sum_i\alpha_i^2\phi_i^2}(\gamma-\gamma').
\]

If `psi^2=sum_i alpha_i^2 phi_i^2`, the direct-sum atom Gram matrix is identical to the Gram matrix generated by the single effective taper `psi`. Therefore stacking or averaging finitely many same-scale scalar certificates does not automatically create joint information.

### Consequence

A viable multi-window argument must retain a genuinely joint observable, such as the cross-Gram operator or a mixed quantity like

\[
\operatorname{tr}(P_1P_2)=\|W_1^*W_2\|_F^2,
\]

rather than collapsing the windows into one scalar certificate.

## 4. Cross-scale branch under investigation

The same-scale no-go does not apply when the support lengths differ. The next calculation uses the ideal rectangular-taper limit and the first-attempt extremal multiplicity pattern on the critical lattice:

\[
(1,1,1,1,2,0)\quad\text{periodically}.
\]

The second scale `lambda<1` has normalized kernel

\[
K_\lambda(r)=\frac{\sin(\pi\lambda r)}{\pi\lambda r}.
\]

The exact periodic defect, its closed form, arrangement minimization and comparison with

\[
H(\lambda)=2-\lambda^{-1}-\lambda/3
\]

will be added with a deterministic checker. Current calculations are not yet frozen and must not be cited as a result.

## 5. Current route update

The research space has already contracted in three useful ways:

1. scalar threshold optimization is exhausted at `c=2`;
2. pure grid-phase shifts carry no new infinite-grid on-line Gram information;
3. simple linear combinations or direct sums of same-scale tapers collapse to a single effective taper.

The surviving target is a **cross-scale or genuinely mixed-operator rigidity estimate**, not another scalar window optimization.