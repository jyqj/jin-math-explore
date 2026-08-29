# A-RH-RTD-0002 — threshold no-go, clock models, and a surviving two-scale obstruction

Status: `active_proof_candidate` — not independently verified

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-window-collapse-02`

Parent candidate: `A-RH-RTD-0001@2f2ecdac7aec73d3996d3484e7a56b051a718f11`

Pinned source:

- `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`
- `zeta23/Zeta23/Defs.lean`
- `zeta23/Zeta23/Poisson.lean`
- `zeta23/Zeta23/Taper.lean`
- `zeta23/Zeta23/ZeroSide/RankTraceMult.lean`
- `zeta23/Zeta23/Assembly/Certificate.lean`

This is pre-genesis solver research. It does not create or advance a governed Riemann-hypothesis Project, improve an unconditional zeta-zero proportion, or prove the Riemann hypothesis.

## Executive result

Three apparently natural continuations of the Zeta23 rank–trace method fail in their naive form:

1. changing or nonnegatively mixing the scalar rank–trace threshold cannot beat the `c=2` simple-zero certificate;
2. changing only the sampling-grid phase preserves the complete Poisson-frame Gram kernel;
3. finitely many fixed-width tapers at one scale admit the same asymptotic clock-multiplicity near-extremizer.

A genuinely different mechanism survives:

> Near saturation at the full critical scale should force a critical-lattice limit, while restriction to the shorter scale `lambda=3/4` detects the integer occupancy variance hidden by the full-scale certificate.

In the exact ideal lattice model this gives the bound

\[
\frac{s_1}{N}\ge\frac{23}{32}=0.71875
\]

and excludes the `2/3` extremal occupancy distribution by the exact second-moment margin

\[
\frac5{108}.
\]

The unresolved step is an inverse/stability theorem transferring near equality for the actual smooth finite Zeta23 compression into that ideal lattice model while controlling collective off-line pair cancellation.

---

# Part I. Exact no-go results

## 1. Arbitrary threshold envelope

Let

\[
k_c(m)=c^2-(c-m)_+^2,
\qquad c>0.
\]

Write `s1` for simple on-line atoms, `p` for off-line reflection pairs, and `N` for total multiplicity. The leak-free Zeta23 rank–trace inequality at threshold `c` has the abstract form

\[
2c\,t-f
\le
\sum_{j\in\mathrm{on}}k_c(m_j)+c^2p,
\tag{1.1}
\]

where `t` is the normalized trace and `f` the squared Frobenius norm.

For every integer `m>=2`,

\[
k_c(m)\le\frac{c^2}{2}m.
\tag{1.2}
\]

Indeed, if `m>=c` this is `c^2<=(c^2/2)m`; if `2<=m<c`, it is equivalent to

\[
2c-m\le\frac{c^2}{2},
\]

which follows from `m>=2` and `(c-2)^2>=0`.

Since an off-line pair contributes at least two units to `N`, (1.1) gives

\[
2c\,t-f
\le
\frac{c^2}{2}N+\beta_c s_1,
\tag{1.3}
\]

where

\[
\beta_c=k_c(1)-\frac{c^2}{2}
=
\begin{cases}
 c^2/2,&0<c\le1,\\
 2c-1-c^2/2,&c\ge1.
\end{cases}
\tag{1.4}
\]

Assume the same first- and second-moment information used by the Zeta23 certificate,

\[
t\ge(1-o(1))N,
\qquad
f\le(\kappa+o(1))N,
\qquad1\le\kappa<2.
\]

The candidate scalar lower bound is

\[
R_c(\kappa)
=
\frac{2c-c^2/2-\kappa}{\beta_c}
\]

when `beta_c>0`. For every `c>0`,

\[
2c-c^2/2-\kappa
\le
(2-\kappa)\beta_c.
\tag{1.5}
\]

Consequently,

\[
R_c(\kappa)\le2-\kappa,
\]

with equality at `c=2`. Because (1.5) adds termwise, no nonnegative mixture of arbitrary-threshold inequalities can do better.

At the flat-window value `kappa=4/3`, the optimal scalar threshold conclusion is exactly

\[
\frac{s_1}{N}\ge\frac23-o(1).
\]

**No-go A.** Threshold tuning is closed as a route to a better simple-zero constant unless a new observable is introduced.

### Distinct-zero side observation

The same `c=2` bookkeeping also gives

\[
4t-f\le N+2N_d,
\]

and hence

\[
\frac{N_d}{N}\ge\frac{3-\kappa}{2}-o(1).
\]

At `kappa=4/3` this is `5/6`. This observation is algebraically checked here but has not been separately reconciled with the source's choice to present the distinct-zero argument through `c=3`.

## 2. Complete-frame grid-phase invariance

Let real tapers `phi,psi` be supported in `[-L/2,L/2]`, and set `h=2*pi/L`. Define the complete analysis vectors

\[
v_{T,\phi}(\gamma)_k
=
\widehat\phi(\gamma-T-kh),
\qquad k\in\mathbb Z.
\]

The bilinear Poisson identity is

\[
\sum_{k\in\mathbb Z}
\widehat\phi(\gamma-T-kh)
\overline{\widehat\psi(\gamma'-T-kh)}
=
L\,\widehat{\phi\psi}(\gamma-\gamma').
\tag{2.1}
\]

The right side does not depend on the grid phase `T`. Therefore a pure phase shift of the complete sampling grid preserves every finite atom Gram matrix up to a canonical isometry of the atom spans.

**No-go B.** Grid-phase shifts alone cannot create a macroscopic two-window separation. Any difference in the finite Zeta23 matrices is a boundary/tail effect and must itself be shown to have macroscopic size; the source estimates those tails as negligible.

## 3. Same-scale taper collapse

For complete-frame vectors at one scale:

- a linear combination of analysis vectors is the analysis vector of the corresponding linear-combination taper;
- a weighted direct sum
  \[
  V(\gamma)=\bigoplus_r\sqrt{\alpha_r}\,v_{\phi_r}(\gamma)
  \]
  has Gram kernel
  \[
  \langle V(\gamma),V(\gamma')\rangle
  =L\,\widehat{\sum_r\alpha_r\phi_r^2}(\gamma-\gamma').
  \]

Putting `chi=(sum alpha_r phi_r^2)^(1/2)`, the direct sum is Gram-equivalent to the single effective taper `chi`.

Thus linear/direct-sum combinations do not open a new scalar rank–trace channel. A surviving multi-window argument must retain nonlinear joint information such as mixed moments, commutators, or thresholded differences.

## 4. Fixed-width taper clock near-extremizer

Let `0<=phi<=1`, let `phi` be supported in `[-L/2,L/2]`, and let it equal one on the plateau `[-L/2+w,L/2-w]`. Put

\[
q=\phi^2,
\qquad
A=\int q,
\qquad
B=\int q^2.
\]

On the natural clock `gamma_n=gamma_0+2*pi*n/L`, the normalized complete-frame coefficients are

\[
r_n=\frac{\widehat q(2\pi n/L)}{A}.
\]

Fourier-series Parseval gives the exact identity

\[
E_\phi(L):=\sum_{n\ne0}|r_n|^2
=
\frac{LB}{A^2}-1.
\tag{4.1}
\]

Since `B<=A` and `A>=L-2w`,

\[
0\le E_\phi(L)
\le\frac{2w}{L-2w}.
\tag{4.2}
\]

Use the repeating six-site integer occupancy pattern

\[
(1,1,1,1,2,0).
\tag{4.3}
\]

Per six sites,

\[
N=6,
\qquad
s_1=4,
\qquad
N_d=5,
\qquad
\sum m_n^2=8.
\]

Hence

\[
\frac{s_1}{N}=rac23,
\qquad
\frac{N_d}{N}=rac56,
\qquad
\frac{\sum m_n^2}{N}=rac43.
\]

For every `c>=2`, its same-scale scalar rank–trace defect is

\[
\Delta_c(\phi)
=
\sum_{i\ne j}m_im_j|r_{i-j}|^2.
\]

Because `m_i<=2`,

\[
\frac{\Delta_c(\phi)}{N}
\le
\frac{10}{3}E_\phi(L)
\le
\frac{20w}{3(L-2w)}
=o(1)
\]

for fixed `w`. Therefore every fixed finite family of fixed-width same-scale tapers admits a common `2/3` near-extremizer.

**No-go C.** Same-scale taper diversity at fixed boundary width cannot force a macroscopic aggregate defect using complete-frame zero-side geometry alone.

---

# Part II. The surviving cross-scale mechanism

## 5. Sampled-sinc symbol

Use the ideal box taper and normalize positions by the natural full-scale clock. At the shorter scale `lambda L`,

\[
r_\lambda(n)=\operatorname{sinc}(\lambda n),
\qquad
\operatorname{sinc}x=\frac{\sin\pi x}{\pi x}.
\]

Let `s_lambda(n)=r_lambda(n)^2`. For `1/2<=lambda<=1`, its discrete Fourier symbol is

\[
S_\lambda(\xi)
=
\sum_{n\in\mathbb Z}s_\lambda(n)e^{-2\pi in\xi}
=
\frac1\lambda
\sum_{k\in\mathbb Z}
\left(1-\frac{|\xi+k|}{\lambda}\right)_+.
\tag{5.1}
\]

On `[-1/2,1/2]`,

\[
\omega_\lambda:=\min S_\lambda
=
\frac{2\lambda-1}{\lambda^2}.
\tag{5.2}
\]

Therefore every finitely supported real sequence `x` satisfies

\[
\sum_{j,k}x_jx_k s_\lambda(j-k)
\ge
\omega_\lambda\sum_jx_j^2.
\tag{5.3}
\]

## 6. Ideal critical-lattice theorem

Let `m_j>=0` be integer occupancies on `d` clock sites, with

\[
\sum_jm_j=d=N.
\]

Put `x_j=m_j-1`. The shorter-scale second moment is

\[
F_\lambda
=
\sum_{j,k}m_jm_k s_\lambda(j-k).
\]

The constant mode contributes `N/lambda`, and (5.3) controls the mean-zero part:

\[
F_\lambda
\ge
\frac N\lambda
+
\omega_\lambda\sum_j(m_j-1)^2.
\tag{6.1}
\]

For integer `m>=0`,

\[
\mathbf 1_{m=1}\ge1-(m-1)^2.
\]

Hence

\[
s_1
\ge
N-\sum_j(m_j-1)^2.
\tag{6.2}
\]

The Zeta23 prime-side second-moment constant at scale `lambda` is

\[
\kappa_\lambda
=
\frac1\lambda+rac\lambda3.
\]

Combining `F_lambda<=(kappa_lambda+o(1))N` with (6.1)–(6.2) yields

\[
\frac{s_1}{N}
\ge
1-rac{\lambda^3}{3(2\lambda-1)}-o(1).
\tag{6.3}
\]

The right side is maximized at

\[
\lambda=\frac34.
\]

At this scale,

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
\frac{s_1}{N}\ge\frac{23}{32}-o(1).}
\tag{6.4}
\]

This theorem is exact in the ideal critical-lattice occupancy model. It is not yet a theorem about zeta zeros.

## 7. Exact exclusion margin at the `2/3` occupancy law

The `2/3` clock pattern has

\[
\frac1N\sum_j(m_j-1)^2=rac13.
\]

At `lambda=3/4`, (6.1) forces

\[
\frac{F_{3/4}}N
\ge
\frac43+rac8{27}
=
\frac{44}{27}.
\]

The prime-side upper constant is `19/12`, so the exact contradiction margin is

\[
\boxed{
\frac{44}{27}-rac{19}{12}=rac5{108}>0.}
\tag{7.1}
\]

This lower bound depends only on occupancy variance and is independent of how the empty, simple and double sites are arranged.

---

# Part III. A stationary-limit formulation

## 8. Ideal stationary lattice obstruction

The periodic computation has a more invariant formulation.

Consider a stationary random locally finite integer-weighted point measure on the normalized real line, with mean mass intensity one and finite second moment. Suppose its full-scale off-diagonal energy intensity is zero:

\[
\mathbb E
\sum_{x\ne y}m_xm_y\operatorname{sinc}^2(x-y)=0
\]

in the usual unit-volume/Palm normalization.

Because every summand is nonnegative and the nonzero zeros of `sinc^2` are exactly the nonzero integers, almost every realization is supported on a random translate

\[
\theta+\mathbb Z.
\]

Let `M_n` be its stationary integer occupancy process. Then

\[
\mathbb E M_0=1.
\]

Write `X_n=M_n-1` and `v=E[X_0^2]`. If `sigma=P(M_0=1)` is the simple-site density, then

\[
\mathbf1_{M_0=1}\ge1-(M_0-1)^2
\]

gives

\[
v\ge1-\sigma.
\tag{8.1}
\]

The covariance sequence of `X` has a nonnegative Herglotz spectral measure with total mass `v`. Therefore

\[
\begin{aligned}
\mathcal F_\lambda
&:=
\sum_{n\in\mathbb Z}
\operatorname{sinc}^2(\lambda n)
\mathbb E[M_0M_n]\\
&\ge
\frac1\lambda+\omega_\lambda v\\
&\ge
\frac1\lambda+\omega_\lambda(1-\sigma).
\end{aligned}
\tag{8.2}
\]

At `lambda=3/4`, imposing `F_lambda<=19/12` again gives

\[
\sigma\ge\frac{23}{32}.
\]

### Limiting contradiction route

Suppose a sequence of ideal full-scale configurations had:

- simple density tending to `2/3`;
- full-scale second moment at most `4/3+o(1)`;
- total mass density tending to one;
- enough local tightness to admit a stationary local weak limit.

The integer inequality

\[
\mathbf1_{m=1}\ge2m-m^2
\]

forces its diagonal second moment to tend to `4/3`. Hence the nonnegative full-scale off-diagonal energy tends to zero. Every stationary local weak limit is therefore lattice-supported, and (8.2) forces the shorter-scale second moment to be at least `44/27`, contradicting the `19/12` upper bound by `5/108`.

Thus the ideal model cannot have a sequence simultaneously approaching all full-scale equality conditions and satisfying the shorter-scale prime bound.

This avoids demanding an explicit point-by-point inverse theorem at the first stage. The remaining analytic work is to justify tightness, marked local convergence and lower semicontinuity for the actual Zeta23 zero-side objects.

---

# Part IV. Equality structure and off-line pairs

## 9. Exact equality normal form, conditional on A-RH-RTD-0001

This section depends on the unverified parent defect decomposition.

At `c=2`, exact equality in the leak-free count certificate forces:

1. every non-simple on-line multiplicity to equal two;
2. every off-line pair multiplicity to equal one;
3. every on-line evaluation vector to have norm one;
4. all six nonnegative parent defect terms to vanish.

The Schur–Jensen equality can be read rowwise. For `g_2(x)=x^2-2x-(x-2)_+^2`, the Bregman defects at diagonal values one and two are

\[
D_1(x)=
\begin{cases}
(x-1)^2,&x\le2,\\
2x-3,&x\ge2,
\end{cases}
\]

and

\[
D_2(x)=
\begin{cases}
(x-2)^2,&x\le2,\\
0,&x\ge2.
\end{cases}
\]

Therefore a simple atom coordinate sees only eigenvalue one. A double-atom coordinate sees no spectrum below two. Trace and rank then force the entire double block to equal `2I`. Thus the on-line atom Gram matrix is

\[
\operatorname{diag}(1,\ldots,1,2,\ldots,2).
\]

The parent defect identity further makes the aggregate off-line contribution a `2`-times projection orthogonal to the on-line range. Consequently the combined exact matrix has spectrum contained in `{0,1,2}`.

At flat moment equality, and after imposing the critical dimension relation `d/N->1`, the limiting spectral proportions are

\[
0:\frac16,
\qquad
1:\frac23,
\qquad
2:\frac16.
\]

This is the matrix counterpart of the clock occupancy law `(1,1,1,1,2,0)`.

### Important limitation

Aggregate equality does **not** imply that every individual off-line pair has zero horizontal depth. The next subsection gives an exact countermodel.

## 10. Isolated aligned pair depth penalty

For the ideal centered box and one isolated reflection pair aligned to one clock coordinate, put

\[
a=(\beta-1/2)L,
\qquad
S(a)=\frac{\sinh a}{a}.
\]

The normalized pair block has eigenvalues

\[
S(a)+1,
\qquad
-(S(a)-1).
\]

Its exact `c=2` defect is

\[
\Delta_{\mathrm{pair}}(a)
=2(S(a)^2-1).
\tag{10.1}
\]

Since `S(a)>=1+a^2/6`,

\[
\Delta_{\mathrm{pair}}(a)
\ge\frac23a^2.
\tag{10.2}
\]

Moreover, for `0<=lambda<=1`, the positive Taylor series gives

\[
S(\lambda a)-1
\le
\lambda^2(S(a)-1)
\]

and hence

\[
\Delta_{\mathrm{pair}}(\lambda a)
\le
\lambda^2\Delta_{\mathrm{pair}}(a).
\tag{10.3}
\]

For a general even fixed-width plateau taper, the same argument with probability density proportional to `phi^2` gives the lower bound

\[
\Delta_{\mathrm{pair}}
\ge
\frac23\bigl((\beta-1/2)L\bigr)^2
\left(1-rac{2w}{L}\right)^3.
\tag{10.4}
\]

This is useful only when individual pair blocks can be separated from one another.

## 11. Collective pair-cancellation no-go model

Let `e1,e2` be orthonormal. Choose `alpha,beta>=0` with

\[
\alpha^2-\beta^2=1.
\]

Define two hyperbolic pair blocks

\[
Q_1=2(\alpha^2e_1e_1^*-\beta^2e_2e_2^*),
\]

\[
Q_2=2(\alpha^2e_2e_2^*-\beta^2e_1e_1^*).
\]

Then

\[
Q_1+Q_2=2I_2
\]

for every `beta`, even though each individual pair has a nonzero negative direction when `beta>0`.

With `P=0`, `b=2` and `c=2`, the aggregate rank–trace defect is exactly zero. If the same swapped orientation persists under scale restriction and `alpha_lambda^2-beta_lambda^2=1`, the cancellation remains exact at every scale.

**No-go D.** Scalar trace/Frobenius/inertia information at one or finitely many scales cannot by itself recover individual off-line depths. A successful cross-scale argument must use the actual cross-kernel geometry tying different pair ordinates and tapers together; it cannot simply sum isolated-pair penalties.

---

# Part V. What remains viable

## 12. Refined surviving target

The earlier generic “two-window separation” target was too broad. The surviving route now has two coupled components.

### A. Critical-lattice extraction for the effective positive modes

Show that asymptotic near equality at the full scale produces, after negligible error and random recentering, a stationary marked limit whose effective positive modes are supported on one translate of the critical clock.

The desired proof can proceed either through:

- a quantitative inverse theorem for almost-orthogonal exponentials;
- a blockwise compactness argument;
- a stationary local weak limit and lower-semicontinuity argument.

The third formulation currently looks least dependent on explicit constants.

### B. Pair disentanglement

Use actual Poisson cross-kernels, not aggregate inertia alone, to prevent the two-pair cancellation mechanism from hiding a positive density of deep off-line pairs. A sufficient result would show that any aggregate cancellation resembling Section 11 forces a non-negligible mixed-scale or mixed-taper observable.

### Candidate contradiction chain

```text
simple proportion -> 2/3
  => all lambda=1 scalar/count inequalities asymptotically saturate
  => effective 0/1/2 spectral normal form + negligible leakage
  => stationary critical-lattice marked limit
  => lambda=3/4 aliasing lower bound >= 44/27
  => contradiction with prime-side upper bound 19/12
```

The exact available margin is `5/108`; every extraction, smoothing, truncation and pair-disentanglement error must fit below that margin in the limiting argument.

## 13. External theorem search boundary

Forward perturbation theorems such as Kadets' `1/4` theorem and Avdonin-type average perturbation results give Riesz-basis bounds when frequencies are already known to be close to the integers. They do not directly supply the inverse statement needed here: deriving lattice proximity from vanishing normalized Gram defect. A 2025 paper of Alemany and Nitzan provides quantitative lower Riesz bounds under Avdonin/Pavlov hypotheses, which may become useful after an approximate integer labelling has been extracted, but it does not remove the extraction step.

## 14. Current evidence and authority

Attached executable checks:

- `check_clock_model.py`
  - arbitrary-threshold envelope;
  - sampled-sinc symbol and exact `lambda=3/4` constants;
  - finite Toeplitz clock model;
  - arrangement-free circulant tests;
  - fixed-width taper Parseval scaling.
- `check_offline_pair.py`
  - isolated aligned-pair eigenvalues and depth penalty;
  - scale contraction;
  - collective two-pair cancellation countermodel.

These are deterministic algebraic/numerical regression checks. They are not proofs of the source-to-zeta bridge.

## 15. Cannot imply

- The ideal `23/32` bound is not an unconditional zeta-zero proportion.
- The exact `5/108` margin does not survive automatically under smoothing, truncation or off-line aggregation.
- The parent six-term defect identity remains unverified while Issue #25 is open.
- The stationary-limit route is a proof program until tightness, marked convergence and lower-semicontinuity are established for the actual zero-side matrices.
- Neither this package nor its computations prove or refute the Riemann hypothesis.
