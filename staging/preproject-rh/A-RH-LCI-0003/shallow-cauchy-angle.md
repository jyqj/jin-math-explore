# A-RH-LCI-0003 — arbitrary-period shallow Cauchy theorem and phase-separated angle collapse

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint continues the period-six analysis without changing any earlier
artifact. It asks whether the positive angle found for the canonical
`(1,1,1,1,2,0)` law can be made period-independent for arbitrary critical-
density `0/1/2` lattice laws.

The answer splits sharply:

1. **Every finite period is exactly nondegenerate.** At zero normalized depth,
   the missing-residue projection is a square Cauchy matrix and is always
   invertible.
2. **No uniform global angle follows from density alone.** A period-`6m`
   configuration with one macroscopic pair arc and one opposite vacancy arc
   has simple density exactly `2/3`, but its smallest squared principal angle
   tends to zero exponentially; even the natural column-average gap is
   `O(1/m)`.

Thus the period-six theorem is a genuine finite positive result, but it cannot
be promoted to a period-independent global angle theorem without a local
pair/vacancy balance hypothesis. This strengthens the case for a blockwise
angle theorem or the centered frequency-square trace.

---

## 1. Arbitrary-period shallow fiber model

Let `P >= 2`, let

\[
\mathcal P,\mathcal E\subset\mathbb Z/P\mathbb Z
\]

be disjoint sets of equal cardinality

\[
|\mathcal P|=|\mathcal E|=k.
\]

The residues in `P` are load-two reflection-pair sites, those in `E` are empty
sites, and every other residue is a simple on-line site. Hence the period mass
is

\[
(P-2k)+2k=P.
\]

Put

\[
\omega=e^{2\pi i/P}
\]

and choose the standard fiber phase

\[
x\in I_P=[-1/2,-1/2+1/P).
\]

The normalized Fourier residue vectors are

\[
f_r(j)=P^{-1/2}\omega^{rj},
\qquad 0\le j<P.
\tag{1.1}
\]

At zero normalized horizontal depth, the positive span is

\[
U_{\mathcal E}
=
\operatorname{span}\{f_r:r\notin\mathcal E\}.
\tag{1.2}
\]

The divided-difference limit of the negative vector at a pair residue
`p in P` is

\[
v_{p,x}(j)
=
\left(x+\frac jP\right)\omega^{pj}.
\tag{1.3}
\]

The orthogonal complement of `U_E` is exactly

\[
W_{\mathcal E}
=
\operatorname{span}\{f_e:e\in\mathcal E\}.
\tag{1.4}
\]

Let `V_x : C^k -> C^P` synthesize the columns (1.3), and let
`Pi_E` be the projection onto `W_E`.

---

## 2. Exact missing-residue projection

For `e in E` and `p in P`, the constant part of
`x+j/P` vanishes against the nontrivial root of unity. Using

\[
\sum_{j=0}^{P-1}jz^j=-\frac{P}{1-z},
\qquad z^P=1,\quad z\ne1,
\]

gives

\[
\boxed{
\langle f_e,v_{p,x}\rangle
=
-\frac{1}{\sqrt P\,(1-\omega^{p-e})}.
}
\tag{2.1}
\]

In particular, the projection matrix is independent of the fiber phase `x`.
Write it as

\[
C_{\mathcal E,\mathcal P}
=
\left[
-\frac{1}{\sqrt P\,(1-\omega^{p-e})}
\right]_{e\in\mathcal E,\ p\in\mathcal P}.
\tag{2.2}
\]

Let

\[
z_e=\omega^e,\qquad y_p=\omega^p.
\]

Since

\[
\frac1{1-y_p/z_e}
=
\frac{z_e}{z_e-y_p},
\]

(2.2) is a row-scaled Cauchy matrix. For fixed orderings of the two sets,

\[
\boxed{
\det C_{\mathcal E,\mathcal P}
=
\frac{(-1)^k}{P^{k/2}}
\left(\prod_{e\in\mathcal E}z_e\right)
\frac{
\prod_{e<e'}(z_{e'}-z_e)
\prod_{p<p'}(y_p-y_{p'})
}{
\prod_{e,p}(z_e-y_p)
},
}
\tag{2.3}
\]

up to the harmless sign convention induced by the chosen orderings.

All roots within each set are distinct and the two sets are disjoint, so every
factor in (2.3) is nonzero.

### Theorem A — finite-period shallow nondegeneracy

For every finite `P` and every disjoint equal-size pair/vacancy sets,

\[
\boxed{
\det C_{\mathcal E,\mathcal P}\ne0.
}
\tag{2.4}
\]

Consequently,

\[
U_{\mathcal E}\cap\operatorname{ran}V_x=\{0\}
\]

modulo the expected dimension statement, and the full `P`-column shallow
polyphase system is a basis. Its squared principal-angle parameter

\[
\eta_{P,\mathcal P,\mathcal E}(x)
=
\inf_{b\ne0}
\frac{\|\Pi_{\mathcal E}V_xb\|^2}{\|V_xb\|^2}
\tag{2.5}
\]

is strictly positive for every fixed finite configuration.

This generalizes the exact finite nonvanishing part of the period-six
checkpoint. It does **not** give a period-independent lower bound.

---

## 3. Exact column-average transport identity

Define the natural column-average squared gap

\[
\overline\eta_{P,\mathcal P,\mathcal E}(x)
=
\frac{\|\Pi_{\mathcal E}V_x\|_F^2}{\|V_x\|_F^2}.
\tag{3.1}
\]

Every negative column has the same norm

\[
S_P(x)
=
\sum_{j=0}^{P-1}
\left(x+\frac jP\right)^2.
\]

The variance identity and the range of `x` give

\[
\boxed{
\frac{P^2-1}{12P}
\le
S_P(x)
\le
\frac{P^2+2}{12P}.
}
\tag{3.2}
\]

From (2.1),

\[
\boxed{
\|\Pi_{\mathcal E}V_x\|_F^2
=
\frac1{4P}
\sum_{p\in\mathcal P}
\sum_{e\in\mathcal E}
\csc^2\!\left(\frac{\pi(p-e)}P\right).
}
\tag{3.3}
\]

Thus the average angle is governed by a concrete pair/vacancy transport
functional on the circle.

### Bounded matching gives a positive average gap

Suppose there is a bijection

\[
\pi:\mathcal P\to\mathcal E
\]

whose circular matching distance is at most `R<P/2`. Keeping only the matched
terms in (3.3) and using the upper bound in (3.2) gives

\[
\boxed{
\overline\eta_{P,\mathcal P,\mathcal E}(x)
\ge
\frac{3}{
(P^2+2)\sin^2(\pi R/P)
}.
}
\tag{3.4}
\]

For fixed `R`,

\[
\liminf_{P\to\infty}
\overline\eta_{P,\mathcal P,\mathcal E}(x)
\ge
\frac{3}{\pi^2R^2}.
\tag{3.5}
\]

This is only a column-average statement; it does not prevent cancellations
between different negative columns. It nevertheless identifies a concrete
local-balance hypothesis under which the average shallow defect survives.

---

## 4. Phase-separated period-`6m` family

Now take

\[
P=6m,
\]

\[
\mathcal P_m=\{0,1,\ldots,m-1\},
\qquad
\mathcal E_m=\{3m,3m+1,\ldots,4m-1\}.
\tag{4.1}
\]

There are `m` pair sites, `m` empty sites and `4m` simple sites, so

\[
\frac{\#\{\text{simple sites}\}}P=\frac23.
\tag{4.2}
\]

Every pair residue is at circular distance strictly larger than `P/3` from
every vacancy residue. Therefore

\[
|1-\omega^{p-e}|^2\ge3.
\tag{4.3}
\]

Combining (3.2)--(3.3),

\[
\boxed{
\overline\eta_{6m,\mathcal P_m,\mathcal E_m}(x)
\le
\frac{4m}{36m^2-1}
=
O(m^{-1}).
}
\tag{4.4}
\]

So even the total residual energy of the individual normalized negative
columns, relative to their total energy, vanishes.

This family is the opposite of the bounded-matching regime: pair mass and
vacancy mass are macroscopically separated. Under uniform random rooting, its
local mark law tends to a mixture with weights

\[
\frac16\{\text{all pair/load-two}\}
+
\frac16\{\text{all empty}\}
+
\frac23\{\text{all simple}\}.
\tag{4.5}
\]

It remains critical-density with simple density `2/3`, but local windows do not
contain balanced pair/vacancy information.

---

## 5. Exponential collapse of the smallest angle

The failure is stronger than (4.4).

Let

\[
\alpha=e^{i\pi/6},
\qquad
r_0=2\sin(\pi/12)=\sqrt{2-\sqrt3}<1.
\tag{5.1}
\]

The pair roots `y_p` lie within distance `r_0` of `alpha`, while the empty
roots `z_e` lie within distance `r_0` of `-alpha`.

For the Cauchy core

\[
D_{e,p}=\frac1{z_e-y_p},
\]

write

\[
z_e=-\alpha+\delta_e,
\qquad
y_p=\alpha+\varepsilon_p.
\]

Then

\[
D_{e,p}
=
-\frac1{2\alpha}
\frac1{
1-(\delta_e-\varepsilon_p)/(2\alpha)
}.
\tag{5.2}
\]

Since

\[
\left|
\frac{\delta_e-\varepsilon_p}{2\alpha}
\right|
\le r_0,
\]

truncating the geometric series after `R` terms gives an entrywise remainder

\[
\left|D_{e,p}-D^{(R)}_{e,p}\right|
\le
\frac{r_0^R}{2(1-r_0)}.
\tag{5.3}
\]

The truncated kernel is a polynomial of degree at most `R-1` in `delta_e`, so

\[
\operatorname{rank}D^{(R)}\le R.
\]

Choose `R=m-1`. Since the matrix is `m x m`, the smallest singular value of the
projection matrix (2.2) obeys

\[
\sigma_{\min}(C_{\mathcal E_m,\mathcal P_m})
\le
\frac{m}{2\sqrt P(1-r_0)}r_0^{m-1}.
\tag{5.4}
\]

To pass from the projection matrix to the generalized angle, let `b` be a unit
coefficient vector and put

\[
F_b(j)=\sum_{p\in\mathcal P_m}b_p\omega^{pj}.
\]

Parseval gives

\[
\sum_j|F_b(j)|^2=P.
\]

Delete one grid point nearest zero. At that point,

\[
|F_b(j_0)|^2\le m,
\]

and every remaining physical coordinate has magnitude at least `1/(2P)`.
Hence

\[
\|V_xb\|^2
\ge
\frac{P-m}{4P^2}
=
\frac5{24P}.
\tag{5.5}
\]

Applying (5.4) to a smallest-singular-vector coefficient yields

\[
\boxed{
\eta_{6m,\mathcal P_m,\mathcal E_m}(x)
\le
\frac{6m^2}{5(1-r_0)^2}
r_0^{2m-2}.
}
\tag{5.6}
\]

Therefore the smallest squared principal angle tends to zero exponentially,
although it is strictly positive at every finite period by Theorem A.

### Corollary — no density-only uniform angle theorem

There is no constant `eta>0` depending only on critical density and the bound

\[
\text{simple density}\le\frac23
\]

such that every finite shallow periodic configuration satisfies

\[
\eta_{P,\mathcal P,\mathcal E}(x)\ge\eta.
\tag{5.7}
\]

The finite exact Cauchy theorem and the asymptotic quantitative theorem point
in opposite directions: exact cancellation is impossible, but arbitrarily
accurate approximate cancellation is possible.

By continuity of the normalized `sinh(a s)/a` and `cosh(a s)` fibers at
`a=0`, one may choose a positive sequence `a_m -> 0` for which the same
principal-angle collapse occurs for genuinely off-line, increasingly shallow
pairs. This is a diagonal existence statement, not a uniform fixed-depth
theorem.

---

## 6. Consequences for the RH route

This checkpoint refutes the strongest global form of the angle strategy:

```text
critical density + simple density <= 2/3
    does not imply a period-independent principal-angle gap.
```

It does not refute the complete hybrid route.

1. The phase-separated family is shallow/tangent in the limit. The centered
   frequency-square trace is specifically designed to force or quantify this
   shallowness.
2. The `lambda=3/4` occupancy/Fourier-symbol argument still charges the
   `0/1/2` mark variance; the angle collapse does not remove the `5/108`
   second-scale margin.
3. A useful angle theorem must be **local or blockwise**, and must record a
   pair/vacancy transport condition, a local Hall-type balance, or an
   exceptional mass.
4. Equation (3.4) gives the first simple positive target: bounded local
   pair/vacancy matching preserves a nonzero average shallow gap.
5. To recover an operator-level Schur lower bound, one needs more than
   column-average transport—such as diagonal dominance, local Riesz bounds, or
   a decomposition into bounded-size matched blocks.

The refined architecture is therefore:

\[
\boxed{
\begin{aligned}
&\text{weighted trace removes deep pairs},\\
&\text{local compactness produces tangent }0/1/2\text{ cells},\\
&\text{local pair/vacancy balance controls shallow angles where available},\\
&\lambda=3/4\text{ Fourier variance charges phase-separated residual laws}.
\end{aligned}
}
\tag{6.1}
\]

---

## 7. Deterministic checker

Run

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_shallow_cauchy.py
```

The checker verifies:

- (2.1) against direct Fourier projection;
- the Cauchy determinant formula on random disjoint finite sets;
- the exact `O(1/P)` phase-separated column-average bound;
- the bounded-matching lower bound;
- the separated-arc low-rank approximation and (5.6);
- finite-period positivity versus numerical angle collapse.

Typical output includes

```text
P=6:   eta_min = 8.571e-02
P=12:  eta_min = 6.609e-05
P=18:  eta_min = 1.614e-08
P=24:  eta_min = 2.793e-12
P=30:  eta_min = 4.253e-16
```

Machine zero at larger periods is numerical underflow, not exact singularity;
Theorem A keeps every finite determinant nonzero.

---

## 8. Authority boundary

Proof candidates/exact finite identities in this checkpoint:

- arbitrary-period projection identity (2.1);
- Cauchy determinant and finite nondegeneracy (2.3)--(2.4);
- exact transport formula (3.3);
- bounded-matching average lower bound (3.4);
- phase-separated `O(1/P)` average collapse (4.4);
- separated-arc exponential principal-angle upper bound (5.6).

Still open:

- a local operator-level Schur gap under source-compatible hypotheses;
- fixed positive normalized depth uniformly in the period;
- smooth-taper and finite-section transfer for the arbitrary-period model;
- the `lambda=3/4` prime-side centered trace;
- integration into the full `5/108` error budget.

This is an ideal periodic shallow/confluent analysis. It does not construct
actual zeta zeros, improve an unconditional zero proportion, or prove RH.
