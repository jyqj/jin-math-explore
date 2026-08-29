# A-RH-XSR-0002 — threshold optimality and cross-scale rigidity

Status: `working_draft`

Issue: `#28`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-cross-scale-rigidity-02`

Frozen parent: `A-RH-RTD-0001 @ 2f2ecdac7aec73d3996d3484e7a56b051a718f11`

Pinned source: `anthropics/formal-math@2bafb8c88f177284a2123b5fefa2ff84e2365eb6`

Primary source paths:

- `zeta23/Zeta23/Assembly/Certificate.lean`
- `zeta23/Zeta23/Poisson.lean`
- `zeta23/Zeta23/Taper.lean`
- `zeta23/Zeta23/ZeroSide/RankTraceMult.lean`
- `zeta23/Zeta23/ZeroSide/TightMult.lean`

This is pre-genesis solver staging. Nothing below is a Project theorem, an independently verified result, an unconditional improvement of a zeta-zero proportion, or a proof of the Riemann hypothesis.

## 0. Executive result

The second attempt produces one positive structural signal and several no-go results.

The positive signal is an exact theorem inside the **ideal rectangular critical-lattice model**. If the total multiplicity per critical cell is one on average and the second-scale Frobenius estimate has the Zeta23 value

\[
\kappa(\lambda)=\frac1\lambda+\frac{\lambda}{3},
\]

then the relative scale

\[
\boxed{\lambda=\frac34}
\]

forces

\[
\boxed{\frac{N_0^s}{N}\ge\frac{23}{32}=0.71875}
\]

and, in the same collapsed occupancy model,

\[
\boxed{\frac{N_d}{N}\ge\frac{55}{64}=0.859375.}
\]

This is **not yet a theorem about zeta zeros**. It is a theorem/proof candidate about the tangent model obtained when the first Zeta23 rank–trace certificate is close to equality: an almost critical Shannon lattice carrying integer loads. The missing bridge is a stability theorem that derives this lattice model, with controlled errors, from a small first-scale rank–trace defect for the genuine smooth Weil/Gabor compression.

The main no-go results are:

1. changing the scalar rank–trace threshold \(c\), or taking positive mixtures of such thresholds, cannot improve the \(c=2\) coefficient while consuming only the same first and second moments;
2. changing only the sampling-lattice phase has no bulk effect on the infinite-grid Gram matrix;
3. linear combinations and Gram-level direct sums of same-scale tapers collapse to one effective taper;
4. fixed-width edge smoothing creates only \(o(1)\) same-scale defect on an exact critical lattice;
5. even the **continuum of all rectangular second-scale moment inequalities** cannot, in the ideal occupancy model, force a universal simple proportion above \(23/32\): an alternating-block sequence is asymptotically sharp.

Thus the viable route has become precise:

> prove a two-scale stability/inverse theorem, not another scalar certificate.

---

## 1. Exact scalar no-go: \(c=2\) is optimal for the simple-zero certificate

Let the normalized zero-side matrix be decomposed as in Zeta23, and let the rank–trace parameter be \(c\). For \(1\le c\le2\),

\[
k_c(m)=c^2-(c-m)_+^2
\]

satisfies

\[
k_c(1)=2c-1,
\qquad
k_c(m)=c^2\quad(m\ge2).
\]

Writing \(s_1\) for the number of simple on-line points, \(s_2\) for the number of multiple on-line points, and \(p\) for the number of off-line reflection pairs, the rank–trace right side is bounded by

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

Then

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

for every \(\kappa\ge1\),

\[
\boxed{B_c(\kappa)\le B_2(\kappa)=2-\kappa.}
\tag{1.3}
\]

The conclusion is unchanged for every nonnegative linear combination of such threshold inequalities. If \(w_i\ge0\), the combined coefficient is

\[
1-(\kappa-1)
\frac{\sum_iw_i}{\sum_iw_iA(c_i)}
\le2-\kappa.
\]

For \(0<c<1\), all positive integer multiplicities satisfy \(k_c(m)=c^2\), so the scalar function does not distinguish simple from multiple points. For \(c\ge2\), the frozen model

\[
P=\operatorname{diag}(1,1,1,1,2),\qquad Q=0
\]

remains a feasible simultaneous-sharpness obstruction with simple proportion \(2/3\).

### Conclusion

The next gain cannot come from another scalar choice of \(c\), nor from a positive mixture of the existing first/second-moment count certificates.

---

## 2. Exact rowwise Jensen/Bregman decomposition

Let

\[
P=WW^*,\qquad M=W^*W,
\]

where the atom Gram matrix \(M\) has diagonal loads

\[
a_j=M_{jj}=m_j\|v_j\|^2.
\]

Let \(\lambda_r\) be the eigenvalues of \(M\), let \(U\) diagonalize \(M\), and put

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

All four expressions are nonnegative.

### Equality classification

\(J_c=0\) if and only if every coordinate \(e_j\) satisfies:

- if \(a_j<c\), then \(e_j\) lies in the eigenspace of \(M\) with eigenvalue exactly \(a_j\);
- if \(a_j\ge c\), then \(e_j\) lies entirely in the spectral subspace \([c,\infty)\).

For \(a_j<c\),

\[
\sum_{\substack{\lambda_r\le c\\|\lambda_r-a_j|\ge\delta}}w_{jr}
\le\frac{J_{c,j}}{\delta^2},
\qquad
\sum_{\lambda_r\ge c}w_{jr}
\le\frac{J_{c,j}}{(c-a_j)^2}.
\tag{2.3}
\]

Every simple atom in the \(c=2\) application has \(a_j\le1\), so the second denominator is at least one.

### Exact Gram-energy formula

A second expression is

\[
J_c
=
\sum_{i\ne j}|M_{ij}|^2
-\operatorname{tr}(M-cI)_+^2
+\sum_j(a_j-c)_+^2.
\tag{2.4}
\]

Combining this with the exact six-term defect identity from `A-RH-RTD-0001`, in the case \(Q=0\), \(b=0\),

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

Thus:

- nonorthogonality is charged exactly by off-diagonal Gram energy;
- atom loads above \(c\) are charged exactly by their squared excess;
- if every \(a_j\le c\), the full defect is precisely the off-diagonal energy.

This corrects and strengthens the first attempt's provisional `P <= cI` special case: that spectral-order assumption is unnecessary.

---

## 3. Exact common-grid cross-Poisson kernel and same-scale collapse

Let \(\phi_1,\phi_2\) be real compactly supported functions on \([-L/2,L/2]\), with enough regularity for Poisson summation, and use

\[
\widehat\phi(z)=\int_{\mathbb R}\phi(u)e^{izu}\,du.
\]

For an arbitrary lattice origin \(s\), put

\[
\tau_k=s+\frac{2\pi k}{L}.
\]

Then, first for real \(x,y\), and by holomorphic continuation wherever the series converges locally uniformly,

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

For even tapers this is \(L\widehat{\phi_1\phi_2}(x-y)\).

The lattice origin \(s\) cancels exactly.

### 3.1 Phase shifts

For a fixed taper and scale, changing only the grid origin leaves all infinite-grid on-line atom inner products unchanged. Hence the nonzero spectrum of the corresponding on-line matrix is unchanged. A phase-shift gain can only be a finite-truncation/tail effect or use information not contained in the bulk on-line Gram matrix.

### 3.2 Linear combinations

\[
\alpha\widehat\phi_1+\beta\widehat\phi_2
=
\widehat{\alpha\phi_1+\beta\phi_2}.
\]

A coordinatewise linear combination is another single taper.

### 3.3 Direct sums

For

\[
v(\gamma)=\bigoplus_i\alpha_i v_{\phi_i}(\gamma),
\]

the atom Gram kernel is

\[
L\,
\widehat{\sum_i\alpha_i^2\phi_i^2}
(\gamma-\gamma').
\]

If \(\psi^2=\sum_i\alpha_i^2\phi_i^2\), the direct-sum atom Gram matrix is the Gram matrix of one effective taper \(\psi\).

### Conclusion

A genuine multi-window argument must retain a mixed observable, for example

\[
\operatorname{tr}(P_1P_2)=\|W_1^*W_2\|_F^2,
\]

rather than collapsing all windows into one scalar certificate.

---

## 4. Same-scale edge-smoothing no-go

Let one taper satisfy

\[
0\le\phi\le1,\qquad
\phi=1\ \text{on}\ [-L/2+w,L/2-w],
\qquad
\operatorname{supp}\phi\subset[-L/2,L/2].
\]

Put

\[
a=\frac1L\int\phi^2,
\qquad
b=\frac1L\int\phi^4.
\]

At critical-lattice separation \(2\pi r/L\), the normalized Gram coefficient is

\[
K_r=\frac{\widehat{\phi^2}(2\pi r/L)}{aL}.
\]

After rescaling to the unit torus, Parseval gives

\[
\sum_{r\ne0}|K_r|^2
=
\frac{b-a^2}{a^2}.
\tag{4.1}
\]

Because \(0\le\phi\le1\),

\[
a^2\le b\le a,
\]

and because only two edge strips of total length \(2w\) differ from one,

\[
1-a\le\frac{2w}{L}.
\]

Therefore

\[
\boxed{
\sum_{r\ne0}|K_r|^2
\le
\frac{2w}{La^2}.
}
\tag{4.2}
\]

For a periodic integer load sequence \(0\le m_n\le M\), the normalized off-diagonal defect is at most

\[
M\sum_{r\ne0}|K_r|^2
=O\!\left(\frac{Mw}{L}\right).
\tag{4.3}
\]

Zeta23 keeps \(w\) fixed while \(L\to\infty\). Hence modifying the fixed-width edge profile, while keeping the same scale and using only its individual scalar frame energy, cannot produce a fixed macroscopic penalty on the exact critical-lattice extremizer.

---

## 5. Ideal rectangular critical-lattice theorem

This is the main positive result of the second attempt.

### 5.1 Collapsed occupancy model

Normalize the first critical lattice to \(\mathbb Z\). Let

\[
m=(m_0,\ldots,m_{p-1})\in\mathbb Z_{\ge0}^p
\]

be periodic, with total multiplicity

\[
\sum_{n=0}^{p-1}m_n=p.
\tag{5.1}
\]

Thus the mean load per critical cell is one.

A cell of load one represents a simple on-line atom in the collapsed equality model. A load two may represent an on-line double atom or the positive tangent mode of a shallow simple off-line reflection pair. Load zero is a vacancy.

At relative support length \(0<\lambda\le1\), the ideal rectangular normalized kernel is

\[
K_\lambda(r)
=\operatorname{sinc}(\pi\lambda r)
=\frac{\sin(\pi\lambda r)}{\pi\lambda r}.
\tag{5.2}
\]

Let

\[
\widehat m(q)=\sum_{n=0}^{p-1}m_ne^{-2\pi iqn/p}.
\]

The full normalized Frobenius energy is

\[
\mathcal E_\lambda(m)
=
\frac1{p^2}
\sum_{q=0}^{p-1}
|\widehat m(q)|^2
F_\lambda(q/p),
\tag{5.3}
\]

where the exact sampled sinc-square symbol is

\[
F_\lambda(x)
=
\frac{(\lambda-x)_++(\lambda-(1-x))_+}{\lambda^2},
\qquad 0\le x\le1.
\tag{5.4}
\]

For \(\lambda\ge1/2\),

\[
F_\lambda(0)=\frac1\lambda,
\qquad
\min_{x\ne0}F_\lambda(x)
=f_\lambda
:=\frac{2\lambda-1}{\lambda^2}.
\tag{5.5}
\]

### 5.2 Variance lower bound

Put

\[
V(m)=\frac1p\sum_{n=0}^{p-1}(m_n-1)^2.
\]

Parseval gives

\[
\frac1{p^2}\sum_{q\ne0}|\widehat m(q)|^2
=V(m).
\tag{5.6}
\]

Therefore

\[
\boxed{
\mathcal E_\lambda(m)
\ge
\frac1\lambda+f_\lambda V(m).
}
\tag{5.7}
\]

The ideal prime-side second-moment budget is

\[
\mathcal E_\lambda(m)
\le
\kappa(\lambda)+o(1),
\qquad
\kappa(\lambda)=\frac1\lambda+\frac\lambda3.
\tag{5.8}
\]

Combining (5.7) and (5.8),

\[
V(m)
\le
\frac{\lambda}{3f_\lambda}
=
\frac{\lambda^3}{3(2\lambda-1)}+o(1).
\tag{5.9}
\]

### 5.3 Integer multiplicity converts variance into simple/distinct counts

For every integer \(m\ge0\),

\[
m^2\ge2m-\mathbf 1_{\{m=1\}},
\tag{5.10}
\]

and

\[
m^2\ge3m-2\mathbf 1_{\{m>0\}}.
\tag{5.11}
\]

Using the mean-one condition (5.1), if

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
\tag{5.12}
\]

The right side of (5.9) is minimized at

\[
\lambda=\frac34,
\]

because the derivative of \(\lambda^3/(2\lambda-1)\) has sign \(4\lambda-3\). At this scale,

\[
f_{3/4}=\frac89,
\qquad
V(m)\le\frac9{32}+o(1).
\]

Hence

\[
\boxed{
\frac Sp\ge\frac{23}{32}-o(1),
\qquad
\frac Dp\ge\frac{55}{64}-o(1).
}
\tag{5.13}
\]

These are exact consequences of the ideal lattice model and the \(\lambda=3/4\) moment budget.

### 5.4 Excluding the \(2/3\) tangent extremizer

If \(S/p\le2/3\), then (5.12) forces \(V\ge1/3\). Thus

\[
\mathcal E_\lambda(m)-\kappa(\lambda)
\ge
g(\lambda),
\]

where

\[
\boxed{
g(\lambda)
=\frac{2\lambda-1}{3\lambda^2}-\frac\lambda3
=\frac{(1-\lambda)(\lambda^2+\lambda-1)}{3\lambda^2}.}
\tag{5.14}
\]

This is strictly positive for

\[
\frac{\sqrt5-1}{2}<\lambda<1.
\]

At \(\lambda=3/4\),

\[
g(3/4)=\frac5{108}.
\tag{5.15}
\]

Therefore the exact \(2/3\) critical-lattice extremizer cannot satisfy the second-scale Frobenius budget.

### Interpretation

The first-scale rank–trace proof can be sharp only by approaching a highly structured integer-load Shannon lattice. But the second-scale moment sees the nonconstant load sequence through a symbol whose nonzero-frequency floor is too high. This is the first concrete mechanism in the project that separates the \(2/3\) extremizer from a second admissible Zeta23 scale.

---

## 6. A new ceiling: \(23/32\) is asymptotically sharp for all rectangular second moments

The ideal theorem also exposes its own limitation.

Let \(d_n=m_n-1\), and let \(\sigma\) be the normalized spectral measure of the centered load sequence. The continuum of all rectangular moment budgets is

\[
\int F_\lambda(x)\,d\sigma(x)
\le
\frac\lambda3,
\qquad 0<\lambda\le1.
\tag{6.1}
\]

At the half-frequency,

\[
F_\lambda(1/2)
=\frac{(2\lambda-1)_+}{\lambda^2}.
\]

The relaxed spectral measure

\[
\sigma_*=\frac9{32}\,\delta_{1/2}
\tag{6.2}
\]

satisfies every inequality (6.1), because

\[
\inf_{\lambda>1/2}
\frac{\lambda/3}{F_\lambda(1/2)}
=
\inf_{\lambda>1/2}
\frac{\lambda^3}{3(2\lambda-1)}
=\frac9{32},
\]

with the minimum at \(\lambda=3/4\).

This relaxed extremizer has variance \(9/32\), corresponding to simple proportion \(23/32\).

It is asymptotically realizable by integer sequences. For \(p=64k\), take an alternating block of length \(18k\),

\[
d_n=(-1)^n\quad(0\le n<18k),
\qquad
d_n=0\quad(18k\le n<64k),
\]

and put \(m_n=1+d_n\). Then

\[
m_n\in\{0,1,2\},
\qquad
\frac1p\sum m_n=1,
\qquad
V=\frac9{32},
\qquad
\frac Sp=\frac{23}{32}.
\]

The spectral measures are shifted Fejér kernels concentrating at \(1/2\), so they converge weakly to (6.2). Consequently, their violations of the entire continuum (6.1) tend to zero.

The deterministic \(p=64\) instance has maximum sampled all-scale excess approximately

\[
9.95\times10^{-4},
\]

already concentrated near \(\lambda\approx0.745\).

### No-go conclusion

Even perfect access to **every rectangular first/second-moment scale** does not, by variance alone, force a universal ideal-lattice simple proportion above

\[
\boxed{\frac{23}{32}}.
\]

Going beyond this number requires a mixed operator, higher moments, extra arithmetic, or stronger realizability information than the scalar spectral measure.

---

## 7. Period-six exploration: stronger signal, non-universal constant

The first frozen extremizer used the periodic pattern

\[
(1,1,1,1,2,0).
\]

Let \(d\in\{1,2,3\}\) be the circular distance between the double cell and the vacancy. Put

\[
F_j=F_\lambda(j/6).
\]

The off-diagonal defects are

\[
\delta_1
=\frac1\lambda+\frac{F_1}{18}+\frac{F_2}{6}+\frac{F_3}{9}-\frac43,
\tag{7.1}
\]

\[
\delta_2
=\frac1\lambda+\frac{F_1}{6}+\frac{F_2}{6}-\frac43,
\tag{7.2}
\]

\[
\delta_3
=\frac1\lambda+\frac{2F_1}{9}+\frac{F_3}{9}-\frac43.
\tag{7.3}
\]

Moreover,

\[
\delta_2-\delta_1=\frac{F_1-F_3}{9}\ge0,
\qquad
\delta_3-\delta_1=\frac{F_1-F_2}{6}\ge0.
\tag{7.4}
\]

Thus the worst period-six arrangement has the double cell adjacent to the vacancy.

The corresponding ideal gain over \(2/3\) is

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
\tag{7.5}
\]

Its maximum occurs at the unique root of

\[
18\lambda^3+33\lambda-31=0,
\]

namely

\[
\lambda_*\approx0.728504383258803.
\]

At this point,

\[
G_6(\lambda_*)\approx0.055176383650709,
\]

so the period-six ideal bound is

\[
0.721843050317375.
\]

At the exact rational scale \(\lambda=3/4\),

\[
G_6(3/4)=\frac{53}{972},
\qquad
\frac23+G_6(3/4)=\frac{701}{972}.
\tag{7.6}
\]

### Important correction: this is not arrangement-universal

At \(\lambda=3/4\), the period-twelve pattern

\[
(2,0,1,2,0,1,1,1,1,1,1,1)
\]

has defect

\[
\delta_{12}
=\frac{76-2\sqrt3}{243}
\approx0.2985016394,
\]

whereas the period-six worst defect is

\[
\delta_6=\frac{74}{243}\approx0.3045267490.
\]

Thus the value \(0.721843\) is a **period-six structural signal**, not a universal cross-scale lower bound. The arrangement-independent result is Section 5, whose optimal simple bound is \(23/32\).

---

## 8. Ideal off-line reflection pair: exact depth penalty

The rectangular model also makes the off-line depth visible.

Let

\[
\phi_L=\mathbf 1_{[-L/2,L/2]},
\qquad
v_z(k)=\frac{\widehat\phi_L(z-\tau_k)}{L}.
\]

For

\[
z=\gamma-i\delta,
\qquad
y=L\delta,
\qquad
S(y)=\frac{\sinh y}{y},
\]

the analytically continued cross-Poisson identity gives

\[
v_z^Tv_z=1,
\qquad
\|v_z\|^2=S(y).
\]

Writing \(v_z=x+iu\),

\[
\langle x,u\rangle=0,
\qquad
\|x\|^2=\frac{S+1}{2},
\qquad
\|u\|^2=\frac{S-1}{2}.
\]

A reflection pair of multiplicity \(m\) contributes

\[
m(v_zv_z^T+\overline v_z\,\overline v_z^{\,T})
=2m(xx^T-uu^T),
\]

with one positive and one negative eigenvalue,

\[
m(S+1),
\qquad
-m(S-1).
\tag{8.1}
\]

Its pure-pair \(c=2\) rank–trace defect is exactly

\[
\boxed{
\Delta_{\mathrm{pair}}(m,y)
=4(m-1)^2
+2m^2\left[\left(\frac{\sinh y}{y}\right)^2-1\right].
}
\tag{8.2}
\]

Since

\[
\frac{\sinh y}{y}\ge1+\frac{y^2}{6},
\]

\[
\boxed{
\Delta_{\mathrm{pair}}(m,y)
\ge4(m-1)^2+\frac23m^2y^2.
}
\tag{8.3}
\]

Therefore near equality forces:

- pair multiplicity \(m=1\);
- normalized horizontal depth \(|\beta-1/2|L=o(1)\).

As \(y\to0\), the pair has positive eigenvalue \(2\), vanishing negative eigenvalue, and behaves exactly like a load-two tangent cell. This explains why the integer occupancy model of Section 5 is the correct first-order model for shallow off-line pairs as well as on-line double zeros.

---

## 9. Stability bridges

### 9.1 Explicit Kadec-neighborhood estimate

Let a \(p\)-periodic occupancy sequence satisfy \(m_n\in\{0,1,2\}\), and perturb the occupied centers to

\[
x_n=n+u_n,
\qquad
\|u\|_\infty\le\frac14.
\]

Put

\[
q_\lambda(t)=\operatorname{sinc}^2(\pi\lambda t).
\]

For \(r\ne0\) and \(|d|\le1/2\),

\[
q_1(r+d)
=\frac{\sin^2(\pi d)}{\pi^2(r+d)^2}
\ge c_r d^2,
\qquad
c_r=\frac4{\pi^2(|r|+1/2)^2}.
\tag{9.1}
\]

Let

\[
L_{\lambda,r}
=\sup_{|t-r|\le1/2}|q_\lambda'(t)|.
\]

Cauchy–Schwarz gives the exact conditional stability estimate

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
=M\sum_{r\ne0}\frac{L_{\lambda,r}^2}{c_r},
\qquad M=2.
\tag{9.3}
\]

The series converges because \(q_\lambda'(r)=O(r^{-2})\).

A coarse closed upper bound is

\[
C_{\lambda,M}^2
\le
M\left(
\frac{9\pi^2}{\lambda^2}
+\frac{252\zeta(3)}{\pi\lambda^3}
+\frac{3\pi^2}{\lambda^4}
\right).
\tag{9.4}
\]

At \(\lambda=3/4\), this gives \(C<31\).

Combining the first-scale gain \(D_1\) with the second-scale ideal gap \(g=5/108\),

\[
\max\{D_1,\ g-C\sqrt{D_1}\}
\ge
\left(
\frac{\sqrt{C^2+4g}-C}{2}
\right)^2.
\tag{9.5}
\]

The coarse bound yields a positive, though tiny, conditional margin exceeding

\[
2.23\times10^{-6}.
\]

This does not solve the real problem, because Kadec closeness has not yet been derived from the Zeta23 defect. It proves that once such closeness is available, the two-scale gap is stable rather than a discontinuous lattice artifact.

### 9.2 Qualitative compactness-gap theorem candidate

A stronger route may avoid explicit matching constants.

Fix

\[
\frac{\sqrt5-1}{2}<\lambda<1.
\]

Consider periodic marked point configurations of period length \(p\), total multiplicity \(p\), and simple-load density at most \(2/3\). Let

- \(\Delta_1\) be the full first-scale \(c=2\) defect, including noninteger-spacing Gram energy and the load-excess term from (2.5);
- \(\mathcal E_\lambda\) be the second-scale sinc-square Frobenius energy.

The candidate compactness statement is:

> There exists \(\eta_\lambda>0\), independent of the period, such that
> \[
> \boxed{
> \max\{\Delta_1/p,\ \mathcal E_\lambda-\kappa(\lambda)\}
> \ge\eta_\lambda.
> }
> \tag{9.6}
> \]

Proof strategy by contradiction:

1. randomly translate a sequence of periodic near-counterexamples and take a stationary local weak limit;
2. lower semicontinuity gives zero first-scale defect in the limit;
3. because \(q_1(t)>0\) away from nonzero integers, every pair of support points in a zero-defect limit differs by an integer, so the support lies in one random coset of \(\mathbb Z\);
4. the load-excess term forces marks at most two;
5. the stationary integer sequence has mean one and simple density at most \(2/3\), hence variance at least \(1/3\);
6. Herglotz spectral representation and the symbol floor (5.5) give
   \[
   \mathcal E_\lambda-\kappa(\lambda)\ge g(\lambda)>0,
   \]
   contradicting the assumed limit.

The remaining work is to write the topology, intensity preservation, diagonal renormalization, and lower-semicontinuity steps without hidden compactness assumptions. Until then, (9.6) remains a proof candidate.

### 9.3 Smooth-taper transfer at an exact lattice

The discontinuous rectangle is not itself an admissible Zeta23 taper, but fixed-width smoothing is asymptotically negligible in the critical-lattice symbol.

For relative scale \(\lambda\), define on the unit torus

\[
f_{\lambda,L}(x)
=\frac{\phi_{\lambda,L}(Lx)^2}{a_{\lambda,L}\lambda},
\]

and compare it with

\[
f_{\lambda,\infty}(x)
=\frac1\lambda\mathbf1_{[-\lambda/2,\lambda/2]}(x).
\]

The taper differs from the rectangle only on edge measure \(O(w/L)\), while \(a_{\lambda,L}=1+O(w/L)\). Hence, for fixed \(\lambda>0\),

\[
\|f_{\lambda,L}-f_{\lambda,\infty}\|_2^2
=O(w/L).
\tag{9.7}
\]

Parseval gives \(\ell^2\) convergence of the lattice Gram coefficients. Cauchy–Schwarz then gives \(\ell^1\) convergence of their squared coefficients, so the sampled symbols converge uniformly:

\[
\sup_x|F_{\lambda,L}(x)-F_\lambda(x)|
=O(\sqrt{w/L}).
\tag{9.8}
\]

For load sequences with uniformly bounded second moment, the ideal lattice inequalities therefore survive with \(o(1)\) errors under the actual fixed-width smooth taper.

This moves the principal obstruction away from taper regularity. The unresolved issue is the **geometric stability of the zero configuration**, especially the interaction of shallow off-line pairs and slowly varying lattice phase.

---

## 10. Deterministic computation

The repository script

```bash
python3 explore_cross_scale.py
```

checks:

- threshold-\(c\) optimality;
- the exact symbol and the \(23/32,55/64\) rational constants;
- positivity of the universal lattice gap above the golden-ratio threshold;
- the period-six closed forms and stationary point;
- the exact period-twelve counterexample;
- the single-pair depth formula and quadratic lower bound;
- an alternating-block sharpness sequence;
- direct truncated-sum agreement with the spectral closed form.

Recorded default output includes:

```text
universal exact-lattice optimum scale: lambda=3/4
universal variance cap: 9/32
universal simple bound: 23/32
universal distinct bound: 55/64
period-six optimum lambda: 0.728504383258803
period-six optimum simple proportion: 0.721843050317375
p=64 alternating-block max sampled all-scale excess: 0.000995308
```

The optional command

```bash
python3 explore_cross_scale.py \
  --jitter-search \
  --jitter-lambda 0.9 \
  --starts 12 \
  --periods 240 \
  --rounds 50
```

performs a deterministic coordinate search on the period-six pattern. It found

```text
min max-gap             0.019220519
first-scale defect      0.019220518
second-scale excess     0.019220519
displacements           0,-0.1680341,-0.1445718,-0.1085521,-0.0630122
```

This is heuristic evidence only. It supports local robustness but is neither global optimization nor proof.

---

## 11. Current route and decisive next lemma

The route now has a clearer logical form.

### What is exhausted

- scalar threshold optimization;
- positive mixtures of existing scalar count certificates;
- same-scale lattice phase shifts;
- same-scale linear combinations/direct sums;
- fixed-edge-profile optimization as a source of macroscopic lattice defect.

### What has a positive mechanism

- a second scale \(\lambda=3/4\) detects variance in the critical-lattice load sequence;
- integer multiplicity converts that variance into \(23/32\) simple and \(55/64\) distinct bounds in the ideal model;
- off-line depth has a positive quadratic defect;
- exact-lattice results survive fixed-width smooth tapering;
- Kadec-close configurations retain a positive two-scale gap.

### Next decisive theorem

The most focused next target is:

> **Two-scale sinc-rigidity / collapsed-lattice inverse theorem.**  
> Show that if the genuine first-scale Zeta23 \(c=2\) defect is \(o(N)\), then after discarding \(o(N)\) mass and accounting for the tail:
>
> 1. simple on-line atoms lie near a common critical sampling lattice;
> 2. on-line doubles and shallow simple off-line pairs become load-two tangent cells;
> 3. deep off-line pairs contribute a positive macroscopic defect through (8.3);
> 4. the second-scale \(\lambda=3/4\) Frobenius energy is bounded below by the lattice symbol estimate, up to \(o(N)\).

A successful version would contradict the prime-side bound

\[
\|G_{3/4}\|_F^2
\le
\left(\frac{19}{12}+o(1)\right)N
\]

whenever the simple critical-line proportion stayed at or below \(2/3\), and would therefore produce an unconditional positive improvement.

The unresolved obligations are:

1. independently verify `A-RH-RTD-0001` and the identities in this attempt;
2. map the leak-free normalization term into the two-scale defect;
3. prove the compactness/inverse step for nonuniform zero ordinates;
4. control shallow off-line pair interactions, not only isolated pairs;
5. propagate the positive zero-side gap through the actual smooth taper, finite grid, tail matrix, and two prime-side moment estimates.

---

## 12. Authority and correction ledger

Established only at solver/proof-candidate level:

- threshold \(c=2\) optimality in the scalar moment model;
- exact Bregman/Jensen decomposition;
- exact common-grid cross-Poisson identity;
- same-scale fixed-edge \(o(1)\) no-go;
- ideal rectangular critical-lattice symbol theorem;
- the \(23/32\) and \(55/64\) ideal bounds;
- continuum-second-moment sharpness at \(23/32\);
- period-six formulas and the period-twelve correction;
- isolated off-line-pair depth formula;
- conditional Kadec-neighborhood stability estimate.

Not established:

- the compactness-gap theorem in all technical detail;
- a lattice inverse theorem for actual zeta-zero compressions;
- a multi-pair off-line stability theorem;
- an unconditional improvement to any published zeta-zero proportion;
- any implication toward the full Riemann hypothesis.

Process corrections retained in the record:

1. the first attempt's intermediate scalar sign was corrected before freezing;
2. the period-six value \(0.721843\) was initially a strong numerical signal, then explicitly downgraded after a period-twelve counterexample showed it is not arrangement-universal;
3. the surviving universal ideal-model bound is \(23/32\), not \(0.721843\).
