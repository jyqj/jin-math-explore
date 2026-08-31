# A-RH-LCI-0003 — fixed-depth block-angle collapse and generalized Vandermonde nondegeneracy

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint follows `shallow-cauchy-angle.md`. That note proved that every
finite shallow/confluent periodic fiber is nondegenerate, while long
pair/vacancy arcs can make the smallest angle exponentially small. The natural
remaining question was whether a fixed positive normalized horizontal depth
restores a period-independent angle gap.

It does not.

For every fixed normalized depth `a >= 0`, a contiguous block of pair residues
of length `P/6` has an explicit

\[
O_a\!\left(\frac{\log P}{P}\right)
\]

upper bound for the smallest squared principal angle against the full positive
span, regardless of where the equally many vacancies are placed. At the same
time, every finite positive-depth fiber is exactly invertible by a generalized
Vandermonde determinant. Thus the obstruction is approximate, not exact:
finite systems never realize the abstract hyperbolic swap perfectly, but their
angle can collapse as the period grows even when normalized pair depth stays
fixed and positive.

This refutes the density-only global angle route more decisively and leaves the
centered frequency-square trace as an essential component rather than an
optional supplement.

---

## 1. Fixed-depth periodic model

Let `P >= 2`. Work in `C^P` with normalized Fourier vectors

\[
f_r(j)=P^{-1/2}\omega^{rj},
\qquad
\omega=e^{2\pi i/P},
\qquad
0\le j<P.
\tag{1.1}
\]

Choose disjoint residue sets

\[
\mathcal A,\mathcal E\subset\mathbb Z/P\mathbb Z,
\qquad
|\mathcal A|=|\mathcal E|=k,
\qquad
1\le k\le P/2.
\tag{1.2}
\]

`A` consists of load-two off-line pair sites and `E` consists of vacancies.
The remaining set

\[
\mathcal S=(\mathbb Z/P\mathbb Z)\setminus
(\mathcal A\cup\mathcal E)
\]

contains simple on-line sites. The total multiplicity is

\[
|\mathcal S|+2|\mathcal A|=P.
\]

Use the standard fiber interval

\[
x\in[-1/2,-1/2+1/P),
\qquad
s_j=x+j/P.
\tag{1.3}
\]

For normalized horizontal depth `a >= 0`, define

\[
c_a(s)=\cosh(as),
\tag{1.4}
\]

\[
d_a(s)=
\begin{cases}
\sinh(as)/a,&a>0,\\
s,&a=0,
\end{cases}
\tag{1.5}
\]

and

\[
q_a(s)=\frac{d_a(s)}{c_a(s)}
=
\begin{cases}
\tanh(as)/a,&a>0,\\
s,&a=0.
\end{cases}
\tag{1.6}
\]

Let `M_g` denote diagonal multiplication by the sampled values `g(s_j)`, and
let `P_A,P_E,P_S` be the orthogonal Fourier projections onto the indicated
residue sets.

The positive span is

\[
\mathcal U_{P,a}
=
\operatorname{ran}P_{\mathcal S}
+\operatorname{ran}(M_{c_a}P_{\mathcal A}),
\tag{1.7}
\]

while the normalized negative synthesis is

\[
B_{P,a}=M_{d_a}F_{\mathcal A}.
\tag{1.8}
\]

Here `F_A : C^k -> C^P` is the Fourier synthesis isometry with columns
`f_p`, `p in A`.

Define the smallest squared principal-angle parameter by

\[
\eta_{P,a}
=
\inf_{b\ne0}
\frac{\operatorname{dist}(B_{P,a}b,\mathcal U_{P,a})^2}
     {\|B_{P,a}b\|^2}.
\tag{1.9}
\]

---

## 2. Every finite positive-depth fiber is exactly nondegenerate

Assume first that `a>0`. The pair columns satisfy

\[
c_a(s_j)f_p(j)+a d_a(s_j)f_p(j)
=
P^{-1/2}e^{ax}
\left(e^{a/P}\omega^p\right)^j,
\tag{2.1}
\]

\[
c_a(s_j)f_p(j)-a d_a(s_j)f_p(j)
=
P^{-1/2}e^{-ax}
\left(e^{-a/P}\omega^p\right)^j.
\tag{2.2}
\]

Thus, after the invertible pairwise column transform

\[
(c_af_p,d_af_p)
\longmapsto
(c_af_p+a d_af_p,c_af_p-a d_af_p),
\]

the full fiber matrix becomes a normalized Vandermonde matrix with nodes

\[
\Lambda_a=
\{\omega^r:r\in\mathcal S\}
\cup
\{e^{a/P}\omega^p:p\in\mathcal A\}
\cup
\{e^{-a/P}\omega^p:p\in\mathcal A\}.
\tag{2.3}
\]

All nodes are distinct: the three groups lie on the unit circle and on the two
distinct circles of radii `e^(a/P)` and `e^(-a/P)`.

If `M_{P,a}` is ordered as simple columns, positive pair columns, negative
pair columns, then

\[
\boxed{
|\det M_{P,a}|
=
\frac{P^{-P/2}}{(2a)^k}
\prod_{\lambda<\mu\in\Lambda_a}|\mu-\lambda|.
}
\tag{2.4}
\]

The fiber phase factors `e^(ax)` and `e^(-ax)` cancel pairwise. Therefore

\[
\boxed{\det M_{P,a}\ne0\quad(a>0).}
\tag{2.5}
\]

At `a=0`, the normalized columns converge to the confluent columns from
`shallow-cauchy-angle.md`, whose missing-residue projection is an invertible
Cauchy matrix. Hence every fixed finite fiber is nondegenerate for all
`a>=0`.

Equation (2.4) is useful for exact finite checks, but nonvanishing alone gives
no uniform lower bound as `P` grows.

---

## 3. A cyclic Fourier-leakage lemma

Let a sampled sequence `g_j` have normalized discrete Fourier coefficients

\[
\widehat g(n)=
\frac1P\sum_{j=0}^{P-1}g_j\omega^{-nj}.
\tag{3.1}
\]

Define its cyclic total variation by

\[
V_{\rm cyc}(g)
=
\sum_{j=0}^{P-1}|g_{j+1}-g_j|,
\qquad g_P=g_0.
\tag{3.2}
\]

Discrete summation by parts gives, for `n != 0 mod P`,

\[
\boxed{
|\widehat g(n)|
\le
\frac{V_{\rm cyc}(g)}
{P|1-\omega^n|}.
}
\tag{3.3}
\]

Let

\[
d(n)=\min(n,P-n),
\qquad1\le n<P.
\]

Since

\[
|1-\omega^n|
=2\sin(\pi d(n)/P)
\ge4d(n)/P,
\tag{3.4}
\]

we have

\[
|\widehat g(n)|
\le\frac{V_{\rm cyc}(g)}{4d(n)}.
\tag{3.5}
\]

Now suppose `A` is a cyclic interval of `k<=P/2` consecutive residues. For a
shift of circular length `d`, at most `min(k,d)` points leave the interval.
Consequently

\[
\begin{aligned}
\|(I-P_{\mathcal A})M_gP_{\mathcal A}\|_{HS}^2
&=
\sum_{p\in\mathcal A}
\sum_{r\notin\mathcal A}
|\widehat g(r-p)|^2\\
&\le
\frac{V_{\rm cyc}(g)^2}{8}
\sum_{d=1}^{\lfloor P/2\rfloor}
\frac{\min(k,d)}{d^2}\\
&\le
\boxed{
\frac{V_{\rm cyc}(g)^2}{8}
(\log k+2).
}
\tag{3.6}
\end{aligned}
\]

The logarithm comes only from the two frequency boundaries of the long block.

For `q_a`, monotonicity on the physical interval gives

\[
V_{\rm cyc}(q_a)\le4Q_a,
\tag{3.7}
\]

where

\[
Q_a=
\begin{cases}
\tanh(a/2)/a,&a>0,\\
1/2,&a=0.
\end{cases}
\tag{3.8}
\]

Also

\[
Q_a\le1/2.
\tag{3.9}
\]

---

## 4. Constructing a positive approximation

The identity

\[
d_a=c_aq_a
\tag{4.1}
\]

supplies an explicit approximation to every negative vector.

For `v in ran P_A`, choose the positive pair vector

\[
M_{c_a}P_{\mathcal A}M_{q_a}v
\in
\operatorname{ran}(M_{c_a}P_{\mathcal A}).
\tag{4.2}
\]

The difference from the negative vector is

\[
M_{d_a}v-M_{c_a}P_{\mathcal A}M_{q_a}v
=
M_{c_a}(I-P_{\mathcal A})M_{q_a}v.
\tag{4.3}
\]

The `P_S` component of this difference can be canceled by a simple positive
Fourier vector. Therefore, with `Pi_U` the orthogonal projection onto the full
positive span,

\[
\boxed{
\|(I-\Pi_{\mathcal U})B_{P,a}\|_F^2
\le
C_a^2
\|(I-P_{\mathcal A})M_{q_a}P_{\mathcal A}\|_{HS}^2,
}
\tag{4.4}
\]

where

\[
C_a=\cosh(a/2).
\tag{4.5}
\]

Notice that this construction does not use the location of the vacancy set.
It uses only the long consecutive pair block and the availability of all
simple frequencies outside the pair and vacancy sets.

---

## 5. Explicit fixed-depth angle collapse

All negative columns have the same norm because modulation does not change
absolute values. Moreover

\[
|d_a(s)|\ge|s|
\tag{5.1}
\]

and the equally spaced sample variance gives

\[
\frac1P\sum_{j=0}^{P-1}s_j^2
\ge
\frac{P^2-1}{12P^2}.
\tag{5.2}
\]

Hence

\[
\boxed{
\|B_{P,a}\|_F^2
\ge
k\frac{P^2-1}{12P^2}.
}
\tag{5.3}
\]

Because the column norms are equal, the minimum principal-angle ratio is at
most the average of the individual column ratios:

\[
\eta_{P,a}
\le
\frac{\|(I-\Pi_{\mathcal U})B_{P,a}\|_F^2}
     {\|B_{P,a}\|_F^2}.
\tag{5.4}
\]

Combining (3.6), (4.4), and (5.3) yields the main theorem.

### Theorem B — fixed-depth global angle no-go

Let `A` be a consecutive residue block of length `k<=P/2`, and let `E` be any
disjoint vacancy set with `|E|=k`. Then

\[
\boxed{
\eta_{P,a}
\le
\min\left\{
1,
\frac{3C_a^2V_{\rm cyc}(q_a)^2P^2}
{2k(P^2-1)}
(\log k+2)
\right\}.
}
\tag{5.5}
\]

Using (3.7),

\[
\boxed{
\eta_{P,a}
\le
\min\left\{
1,
24C_a^2Q_a^2
\frac{P^2}{k(P^2-1)}
(\log k+2)
\right\}.
}
\tag{5.6}
\]

At the critical `2/3` simple-density choice

\[
k=P/6,
\]

this becomes

\[
\boxed{
\eta_{P,a}
\le
\min\left\{
1,
144C_a^2Q_a^2
\frac{P}{P^2-1}
(\log(P/6)+2)
\right\}.
}
\tag{5.7}
\]

Since `Q_a<=1/2`, the simpler bound

\[
\eta_{P,a}
\le
\min\left\{
1,
36\cosh^2(a/2)
\frac{P}{P^2-1}
(\log(P/6)+2)
\right\}
\tag{5.8}
\]

also holds.

For every fixed finite `a`,

\[
\boxed{
\eta_{P,a}
=O_a\!\left(\frac{\log P}{P}\right)
\longrightarrow0.
}
\tag{5.9}
\]

The explicit constants are deliberately coarse. Their value is the qualitative
uniform no-go: fixed positive normalized depth does not rescue a global angle
gap from density information alone.

---

## 6. Relation to the earlier Cauchy and local-matching results

There is no contradiction with the finite Cauchy theorem:

- (2.5) says every finite fiber has strictly positive angle;
- (5.9) says those positive angles need not have a common lower bound.

There is also no contradiction with the bounded pair/vacancy matching bound in
`shallow-cauchy-angle.md`. That bound concerns the **raw missing-residue
projection**

\[
\|P_{\mathcal E}V\|_F^2/\|V\|_F^2
\]

before optimizing over linear combinations of positive pair columns. Theorem B
allows those pair-positive combinations and controls the actual distance to the
entire positive span. A raw transport lower bound alone therefore does not
supply an operator-level Schur gap when matched blocks grow without bound.

A viable local angle theorem needs stronger structure, for example:

1. a decomposition into uniformly bounded matched blocks;
2. a local Hall condition plus a uniform block inverse;
3. coefficient locality or diagonal dominance preventing long-block
   cancellation;
4. an explicit exceptional-mass term charged elsewhere.

---

## 7. Numerical stress test

The deterministic checker

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_fixed_depth_angle.py
```

verifies:

- the generalized Vandermonde log-determinant formula on random finite sets;
- the cyclic-variation bound for `q_a`;
- the Hilbert--Schmidt leakage estimate (3.6);
- the explicit positive approximation (4.3)--(4.4);
- the denominator bound (5.3);
- the final theorem bound;
- direct principal-angle scans for depths `a=0,0.5,1,2,4`.

For the opposite-arc family, representative smallest-angle values are:

```text
a=1:
P=6   8.824e-02
P=12  7.646e-05
P=18  1.978e-08
P=24  3.516e-12
P=30  5.096e-16

a=4:
P=6   1.227e-01
P=12  2.734e-04
P=18  1.282e-07
P=24  3.133e-11
P=30  5.710e-15
```

The observed collapse is much faster than the proved `O_a(log P/P)` upper
bound. Numerical zeros at larger periods are floating-point underflow and do
not contradict finite Vandermonde nondegeneracy.

---

## 8. Consequence for the Zeta23 research architecture

The angle route is now sharply scoped.

A theorem of the form

```text
critical density + simple density <= 2/3 + bounded normalized depth
    => uniform global principal-angle gap
```

is false even in the ideal periodic Gabor model.

The surviving hybrid is:

\[
\boxed{
\begin{aligned}
&\lambda=1:\quad
  \text{scalar defect and local random-coset compactness},\\
&\lambda=3/4:\quad
  \text{centered weighted trace to control total squared depth},\\
&\text{local blocks}:\quad
  \text{angle estimates only after bounded local inversion/balance},\\
&\lambda=3/4:\quad
  \text{Fourier variance to charge phase-separated residual laws}.
\end{aligned}
}
\tag{8.1}
\]

The weighted trace is essential because it sees the additive
`-2 sum n_p delta_p^2` term even when global positive/negative spans become
nearly parallel.

---

## 9. Authority boundary

Proof candidates/exact finite identities in this checkpoint:

- the arbitrary-depth generalized Vandermonde determinant (2.4);
- finite positive-depth nondegeneracy (2.5);
- cyclic Fourier leakage (3.3)--(3.6);
- the constructive approximation (4.3)--(4.4);
- the fixed-depth angle upper bounds (5.5)--(5.9).

Still open:

- an operator-level angle lower bound on uniformly bounded local blocks;
- transfer through the smooth taper and actual finite Zeta23 compression;
- the signed matrix version of the weighted finite-section tail;
- the `lambda=3/4` prime-side centered trace;
- closure of all losses inside the `5/108` budget.

This checkpoint concerns ideal periodic fiber models. It neither constructs
actual zeta zeros nor improves an unconditional critical-line proportion, and
it does not prove or refute RH.
