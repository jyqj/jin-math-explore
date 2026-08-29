# A-RH-XSR-0002 — threshold optimality and cross-scale rigidity

Status: `frozen_for_review`

Issue: `#28`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-cross-scale-rigidity-02`

Frozen parent: `A-RH-RTD-0001 @ 2f2ecdac7aec73d3996d3484e7a56b051a718f11`

Pinned upstream source: `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`

Relevant source paths:

- `zeta23/Zeta23/Assembly/Certificate.lean`
- `zeta23/Zeta23/Poisson.lean`
- `zeta23/Zeta23/Taper.lean`
- `zeta23/Zeta23/ZeroSide/RankTraceMult.lean`
- `zeta23/Zeta23/ZeroSide/TightMult.lean`

This is a frozen pre-genesis solver package. Nothing below is a governed Project theorem, an independently verified result, an unconditional improvement of a zeta-zero proportion, or a proof of the Riemann hypothesis.

## 0. Main outcome

The second attempt found a concrete positive mechanism in the **ideal rectangular critical-lattice tangent model**:

\[
\boxed{\lambda=\frac34}
\]

combined with the Zeta23 first/second-moment budget forces

\[
\boxed{\frac{N_0^s}{N}\ge\frac{23}{32}=0.71875}
\]

and, in the same collapsed occupancy model,

\[
\boxed{\frac{N_d}{N}\ge\frac{55}{64}=0.859375.}
\]

The exact ideal contradiction to a simple proportion at most \(2/3\) is

\[
\boxed{\frac5{108}}
\]

per unit multiplicity before geometric, taper and tail losses.

This is not yet a theorem about zeta zeros. The missing bridge is a two-scale inverse/stability theorem: small first-scale Zeta23 defect must force the genuine zero configuration, after discarding negligible mass, to look like the integer-load critical lattice on which the second-scale Fourier-symbol argument applies.

The attempt also proves or isolates several no-go statements:

1. varying the rank–trace threshold \(c\), or taking positive mixtures of such scalar inequalities, cannot improve the \(c=2\) coefficient when only the same first and second moments are consumed;
2. changing only the sampling-lattice phase has no bulk effect on the infinite-grid on-line Gram matrix;
3. same-scale linear combinations and Gram-level direct sums collapse to one effective taper;
4. fixed-width edge smoothing creates only \(o(1)\) same-scale defect on an exact critical lattice;
5. even the continuum of all rectangular scalar second-scale moments has an ideal-model ceiling at \(23/32\).

The surviving route is therefore not “optimize one more scalar certificate”. It is:

> prove a two-scale sinc-rigidity / collapsed-lattice inverse theorem, or exhibit a genuine near-extremal counterconfiguration.

---

## 1. Scalar-threshold no-go

For \(1\le c\le2\),

\[
k_c(1)=2c-1,
\qquad
k_c(m)=c^2\quad(m\ge2).
\]

If \(s_1\) counts simple on-line points, \(s_2\) counts multiple on-line points, and \(p\) counts off-line reflection pairs, then

\[
2c\operatorname{tr}G-\|G\|_F^2-\frac{c^2}{2}N
\le A(c)s_1,
\qquad
A(c)=2c-1-\frac{c^2}{2}.
\tag{1.1}
\]

Under the moment information used by `Assembly/Certificate.lean`,

\[
\operatorname{tr}G\ge(1-o(1))N,
\qquad
\|G\|_F^2\le(\kappa+o(1))N,
\]

this gives

\[
\frac{s_1}{N}
\ge B_c(\kappa)-o(1),
\qquad
B_c(\kappa)=1-\frac{\kappa-1}{A(c)}.
\tag{1.2}
\]

Since \(A(c)\le A(2)=1\),

\[
\boxed{B_c(\kappa)\le B_2(\kappa)=2-\kappa.}
\tag{1.3}
\]

For nonnegative weights \(w_i\), the corresponding positive mixture has coefficient

\[
1-(\kappa-1)
\frac{\sum_iw_i}{\sum_iw_iA(c_i)}
\le2-\kappa.
\]

For \(c<1\), the scalar function does not distinguish positive integer multiplicities. For \(c\ge2\), the frozen model

\[
P=\operatorname{diag}(1,1,1,1,2),\qquad Q=0
\]

already realizes the \(2/3\) obstruction. Thus the scalar-threshold continuum is exhausted.

---

## 2. Exact Schur/Bregman rigidity

Write

\[
P=WW^*,\qquad M=W^*W,
\qquad a_j=M_{jj}=m_j\|v_j\|^2.
\]

Let \(\lambda_r\) be the eigenvalues of \(M\), and let

\[
w_{jr}=|U_{jr}|^2,
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
    =\sum_{j,r}w_{jr}D_c(\lambda_r\mid a_j),
\tag{2.1}
\]

where

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

Every term is nonnegative. Equality is completely characterized:

- if \(a_j<c\), then the coordinate \(e_j\) lies in the eigenspace of eigenvalue \(a_j\);
- if \(a_j\ge c\), then \(e_j\) lies in the spectral subspace \([c,\infty)\).

For \(a_j<c\), the spectral leakage bounds are

\[
\sum_{\substack{\lambda_r\le c\\|\lambda_r-a_j|\ge\delta}}w_{jr}
\le\frac{J_{c,j}}{\delta^2},
\qquad
\sum_{\lambda_r\ge c}w_{jr}
\le\frac{J_{c,j}}{(c-a_j)^2}.
\tag{2.3}
\]

The equivalent Gram formula is

\[
J_c
=
\sum_{i\ne j}|M_{ij}|^2
-\operatorname{tr}(M-cI)_+^2
+\sum_j(a_j-c)_+^2.
\tag{2.4}
\]

Combining (2.4) with the six-term identity of `A-RH-RTD-0001`, for \(Q=0\), \(b=0\),

\[
\boxed{
\Delta_c
=
\sum_{i\ne j}|M_{ij}|^2
+
\sum_j(a_j-c)_+^2.
}
\tag{2.5}
\]

This strengthens the parent attempt: no additional assumption \(P\preceq cI\) is required.

---

## 3. Cross-Poisson identity and same-scale collapse

For two real tapers supported on \([-L/2,L/2]\), with sufficient regularity and summability, use

\[
\widehat\phi(z)=\int_{\mathbb R}\phi(u)e^{izu}\,du,
\qquad
\tau_k=s+\frac{2\pi k}{L}.
\]

Then

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

For even tapers the right side is \(L\widehat{\phi_1\phi_2}(x-y)\). The lattice origin \(s\) cancels.

Consequences for the full infinite grid:

- phase shifts do not change the bulk on-line atom Gram matrix;
- a coordinatewise linear combination is another single taper;
- for \(v=\bigoplus_i\alpha_iv_{\phi_i}\), the Gram kernel is generated by \(\sum_i\alpha_i^2\phi_i^2\), so the direct sum collapses at the Gram level to one effective scalar kernel.

A viable multi-window argument must retain a genuinely mixed observable such as

\[
\operatorname{tr}(P_1P_2)=\|W_1^*W_2\|_F^2.
\]

---

## 4. Fixed-edge same-scale no-go

Assume

\[
0\le\phi\le1,
\qquad
\phi=1\text{ away from two edge strips of total width }2w,
\qquad
\operatorname{supp}\phi\subset[-L/2,L/2].
\]

Put

\[
a=\frac1L\int\phi^2,
\qquad
b=\frac1L\int\phi^4.
\]

At critical-lattice separation \(2\pi r/L\), Parseval gives

\[
\sum_{r\ne0}|K_r|^2
=
\frac{b-a^2}{a^2}
\le
\frac{2w}{La^2}.
\tag{4.1}
\]

For integer loads bounded by \(M\), the normalized off-diagonal defect is at most

\[
M\sum_{r\ne0}|K_r|^2
=O(Mw/L).
\tag{4.2}
\]

Since Zeta23 fixes \(w\) while \(L\to\infty\), edge-profile optimization at one scale cannot create a fixed macroscopic gap on the exact critical-lattice extremizer.

---

## 5. Ideal rectangular critical-lattice theorem

Normalize the first critical lattice to \(\mathbb Z\). Let

\[
m=(m_0,\ldots,m_{p-1})\in\mathbb Z_{\ge0}^p,
\qquad
\sum_{n=0}^{p-1}m_n=p.
\tag{5.1}
\]

At relative support length \(0<\lambda\le1\), use

\[
K_\lambda(r)=\frac{\sin(\pi\lambda r)}{\pi\lambda r}.
\tag{5.2}
\]

For the unnormalized DFT

\[
\widehat m(q)=\sum_nm_ne^{-2\pi iqn/p},
\]

the normalized Frobenius energy is

\[
\mathcal E_\lambda(m)
=
\frac1{p^2}
\sum_{q=0}^{p-1}
|\widehat m(q)|^2F_\lambda(q/p),
\tag{5.3}
\]

where

\[
F_\lambda(x)
=
\frac{(\lambda-x)_++(\lambda-(1-x))_+}{\lambda^2}.
\tag{5.4}
\]

For \(\lambda\ge1/2\),

\[
F_\lambda(0)=\frac1\lambda,
\qquad
\min_{x\ne0}F_\lambda(x)
=f_\lambda=rac{2\lambda-1}{\lambda^2}.
\tag{5.5}
\]

Let

\[
V(m)=\frac1p\sum_n(m_n-1)^2.
\]

Parseval yields

\[
\boxed{
\mathcal E_\lambda(m)
\ge
\frac1\lambda+f_\lambda V(m).
}
\tag{5.6}
\]

The Zeta23 ideal second-moment budget is

\[
\mathcal E_\lambda(m)
\le
\kappa(\lambda)+o(1),
\qquad
\kappa(\lambda)=\frac1\lambda+rac\lambda3.
\tag{5.7}
\]

Hence

\[
V(m)
\le
\frac{\lambda^3}{3(2\lambda-1)}+o(1).
\tag{5.8}
\]

For every integer \(m\ge0\),

\[
m^2\ge2m-\mathbf1_{\{m=1\}},
\qquad
m^2\ge3m-2\mathbf1_{\{m>0\}}.
\tag{5.9}
\]

If

\[
S=\#\{n:m_n=1\},
\qquad
D=\#\{n:m_n>0\},
\]

then

\[
\frac Sp\ge1-V(m),
\qquad
\frac Dp\ge1-\frac{V(m)}2.
\tag{5.10}
\]

The right side of (5.8) is minimized at \(\lambda=3/4\). There

\[
f_{3/4}=\frac89,
\qquad
V(m)\le\frac9{32}+o(1),
\]

so

\[
\boxed{
\frac Sp\ge\frac{23}{32}-o(1),
\qquad
\frac Dp\ge\frac{55}{64}-o(1).
}
\tag{5.11}
\]

If \(S/p\le2/3\), then \(V\ge1/3\), and

\[
\mathcal E_\lambda(m)-\kappa(\lambda)
\ge
g(\lambda),
\]

where

\[
\boxed{
g(\lambda)
=
\frac{(1-\lambda)(\lambda^2+\lambda-1)}{3\lambda^2}.}
\tag{5.12}
\]

This is positive for

\[
\frac{\sqrt5-1}{2}<\lambda<1,
\]

and

\[
g(3/4)=\frac5{108}.
\tag{5.13}
\]

Thus a perfect \(2/3\) critical-lattice tangent extremizer is incompatible with the \(\lambda=3/4\) second moment.

---

## 6. New ceiling: \(23/32\) is asymptotically sharp for all rectangular scalar second moments

Let \(d_n=m_n-1\), and let \(\sigma\) be its normalized spectral measure. The continuum of rectangular constraints is

\[
\int F_\lambda(x)\,d\sigma(x)
\le\frac\lambda3,
\qquad0<\lambda\le1.
\tag{6.1}
\]

The relaxed measure

\[
\sigma_*=\frac9{32}\delta_{1/2}
\tag{6.2}
\]

satisfies every inequality because

\[
\inf_{\lambda>1/2}
\frac{\lambda/3}{F_\lambda(1/2)}
=
\frac9{32},
\]

with equality at \(\lambda=3/4\).

It is approached by integer sequences. For \(p=64k\), take an alternating block of length \(18k\),

\[
d_n=(-1)^n\quad(0\le n<18k),
\qquad
d_n=0\quad(18k\le n<64k),
\]

and set \(m_n=1+d_n\). Then

\[
m_n\in\{0,1,2\},
\quad
\frac1p\sum m_n=1,
\quad
V=\frac9{32},
\quad
\frac Sp=\frac{23}{32}.
\]

The spectral measures are shifted Fejér kernels concentrating at \(1/2\). The deterministic \(p=64\) instance already has maximum sampled all-scale excess approximately

\[
9.95308\times10^{-4}.
\]

Therefore scalar access to all rectangular first/second-moment scales cannot, in this ideal model, force a universal simple proportion above \(23/32\). A stronger result needs mixed operators, higher moments, additional arithmetic, or stronger realizability information.

---

## 7. Period-six signal and exact correction

For the periodic pattern with four simple cells, one double cell and one vacancy, the worst circular arrangement places the double cell adjacent to the vacancy. Its ideal gain over \(2/3\) is

\[
G_6(\lambda)=
\begin{cases}
\dfrac{-36\lambda^3+48\lambda-19}{108\lambda^2},
&1/2\le\lambda\le2/3,\\[6pt]
\dfrac{-36\lambda^3+66\lambda-31}{108\lambda^2},
&2/3\le\lambda\le5/6,\\[6pt]
\dfrac{-\lambda^3+2\lambda-1}{3\lambda^2},
&5/6\le\lambda\le1.
\end{cases}
\tag{7.1}
\]

The maximum occurs at the root

\[
18\lambda^3+33\lambda-31=0,
\qquad
\lambda_*\approx0.728504383258803,
\]

and gives the period-six ideal bound

\[
0.721843050317375.
\]

At \(\lambda=3/4\),

\[
G_6(3/4)=\frac{53}{972},
\qquad
\frac23+G_6(3/4)=\frac{701}{972}.
\]

This stronger value is **not universal**. The period-twelve pattern

\[
(2,0,1,2,0,1,1,1,1,1,1,1)
\]

has at \(\lambda=3/4\)

\[
\delta_{12}
=
\frac{76-2\sqrt3}{243}
<
\frac{74}{243}=\delta_6.
\]

The universal ideal bound retained by this attempt is therefore \(23/32\), not \(0.721843\).

---

## 8. Ideal isolated off-line pair depth penalty

For the rectangular full grid, let

\[
y=L(\beta-1/2),
\qquad
S(y)=\frac{\sinh y}{y}.
\]

A reflection pair of multiplicity \(m\) has one positive and one negative eigenvalue

\[
m(S+1),
\qquad
-m(S-1).
\]

Its pure \(c=2\) defect is

\[
\boxed{
\Delta_{\mathrm{pair}}(m,y)
=4(m-1)^2
+2m^2\left[\left(\frac{\sinh y}{y}\right)^2-1\right].
}
\tag{8.1}
\]

Since \(\sinh y/y\ge1+y^2/6\),

\[
\boxed{
\Delta_{\mathrm{pair}}(m,y)
\ge4(m-1)^2+\frac23m^2y^2.
}
\tag{8.2}
\]

Near equality forces \(m=1\) and \(|\beta-1/2|L=o(1)\). As \(y\to0\), the pair behaves like a load-two tangent cell. This justifies including shallow simple off-line pairs in the collapsed occupancy model, but does not yet control interactions among many pairs.

---

## 9. Stability bridges

### 9.1 Kadec-neighborhood estimate

For a periodic load sequence \(m_n\in\{0,1,2\}\), perturb the occupied sites to

\[
x_n=n+u_n,
\qquad
\|u\|_\infty\le1/4.
\]

With

\[
q_\lambda(t)=\operatorname{sinc}^2(\pi\lambda t),
\]

one has, for \(r\ne0\) and \(|d|\le1/2\),

\[
q_1(r+d)
\ge
\frac{4d^2}{\pi^2(|r|+1/2)^2}.
\tag{9.1}
\]

If

\[
L_{\lambda,r}
=
\sup_{|t-r|\le1/2}|q_\lambda'(t)|,
\]

Cauchy–Schwarz gives

\[
\boxed{
|D_\lambda(u)-D_\lambda(0)|
\le C_{\lambda,M}\sqrt{D_1(u)},
}
\tag{9.2}
\]

where

\[
C_{\lambda,M}^2
=M\sum_{r\ne0}
\frac{L_{\lambda,r}^2}{4/[\pi^2(|r|+1/2)^2]}.
\tag{9.3}
\]

A coarse bound is

\[
C_{\lambda,M}^2
\le
M\left(
\frac{9\pi^2}{\lambda^2}
+
\frac{252\zeta(3)}{\pi\lambda^3}
+
\frac{3\pi^2}{\lambda^4}
\right).
\tag{9.4}
\]

At \(\lambda=3/4\), \(M=2\), this gives \(C<31\). Combining (9.2) with the ideal gap \(5/108\) yields a positive conditional tradeoff margin greater than \(2.2\times10^{-6}\).

This proves local stability only after a one-quarter-lattice matching has already been supplied.

### 9.2 Compactness-gap candidate

For any fixed

\[
\frac{\sqrt5-1}{2}<\lambda<1,
\]

the target qualitative theorem is

\[
\boxed{
\max\left\{
\Delta_1/p,
\mathcal E_\lambda-\kappa(\lambda)
\right\}
\ge\eta_\lambda>0
}
\tag{9.5}
\]

for periodic marked configurations of mean load one and simple density at most \(2/3\).

The proposed contradiction proof is:

1. randomly translate periodic near-counterexamples and take a stationary local weak limit;
2. lower semicontinuity sends the first-scale defect to zero;
3. because \(q_1(t)>0\) away from nonzero integers, the limiting support lies in one coset of \(\mathbb Z\);
4. the load-excess term forces marks at most two;
5. mean one and simple density at most \(2/3\) force variance at least \(1/3\);
6. Herglotz spectral representation and the symbol floor give the positive gap (5.12).

The topology, preservation of intensity, diagonal renormalization and lower-semicontinuity steps are not yet fully proved. Equation (9.5) remains an incomplete proof candidate.

### 9.3 Smooth-taper transfer at an exact lattice

For a fixed relative scale and fixed edge width, the normalized squared taper on the unit torus differs from the rectangular indicator only on measure \(O(w/L)\). Hence

\[
\|f_{\lambda,L}-f_{\lambda,\infty}\|_2^2
=O(w/L).
\]

Parseval and Cauchy–Schwarz give uniform convergence of the sampled Gram symbols:

\[
\boxed{
\sup_x|F_{\lambda,L}(x)-F_\lambda(x)|
=O(\sqrt{w/L}).
}
\tag{9.6}
\]

Thus the exact-lattice ideal bounds survive fixed-width smooth tapering with \(o(1)\) error for load sequences with bounded second moment. The principal unresolved difficulty is geometric stability of the zero configuration and interaction of shallow off-line pairs, not the taper discontinuity itself.

---

## 10. Deterministic computation

Run:

```bash
python3 explore_cross_scale.py
```

The harness checks the exact rational constants, Fourier-symbol formulas, scalar-threshold optimum, period-six expressions, period-twelve counterexample, isolated-pair depth formula, alternating-block ceiling sequence, and direct-sum agreement.

Recorded deterministic output:

```text
PASS exact algebraic/closed-form checks
threshold continuum maximum: c=2
universal exact-lattice optimum scale: lambda=3/4
universal variance cap: 9/32
universal simple bound: 23/32
universal distinct bound: 55/64
period-six optimum lambda: 0.728504383258803
period-six optimum simple proportion: 0.721843050317375
p=64 alternating-block max sampled all-scale excess: 0.000995308
coarse Kadec constant: approximately 30.986
conditional margin: greater than 2.2e-6
```

Optional deterministic coordinate search:

```bash
python3 explore_cross_scale.py \
  --jitter-search \
  --jitter-lambda 0.9 \
  --starts 12 \
  --periods 240 \
  --rounds 50
```

Recorded heuristic result:

```text
min max-gap          0.019220519
first-scale defect   0.019220518
second-scale excess  0.019220519
displacements        0,-0.1680341,-0.1445718,-0.1085521,-0.0630122
```

The coordinate search is not a global optimization and is not proof.

---

## 11. Next decisive theorem

> **Two-scale sinc-rigidity / collapsed-lattice inverse theorem.**  
> If the genuine first-scale Zeta23 \(c=2\) defect is \(o(N)\), then after discarding \(o(N)\) mass and accounting for normalization and tail errors:
>
> 1. simple on-line atoms lie near a common critical sampling lattice;
> 2. on-line doubles and shallow simple off-line pairs become load-two tangent cells;
> 3. deep or multiple off-line pairs pay a positive macroscopic defect;
> 4. the \(\lambda=3/4\) second-scale Frobenius energy obeys the lattice lower bound up to \(o(N)\).

The target prime-side budget is

\[
\|G_{3/4}\|_F^2
\le
\left(\frac{19}{12}+o(1)\right)N.
\]

If the simple critical-line proportion stayed at or below \(2/3\), the ideal zero side would exceed that budget by \(5N/108\) before stability losses.

Remaining obligations:

1. independent verification of both frozen attempts;
2. rigorous inverse/matching theorem for nonuniform zero ordinates;
3. multi-pair off-line stability;
4. leak-free normalization bookkeeping;
5. transfer through the smooth finite grid, tail matrix and two prime-side moment estimates.

---

## 12. Correction and authority ledger

Corrections retained rather than overwritten:

1. the parent attempt's initial scalar sign error was corrected before its freeze;
2. the period-six value \(0.721843\) was downgraded after the exact period-twelve counterexample;
3. the full \(Q=0\) Gram-defect formula was strengthened by removing the unnecessary provisional assumption \(P\preceq cI\).

Evidence grades are recorded claim-by-claim in `attempt.json`.

This package does **not** establish:

- an unconditional improvement of the published zeta-zero proportion;
- the compactness-gap theorem;
- a multi-pair off-line estimate;
- a proof or disproof of the Riemann hypothesis.
