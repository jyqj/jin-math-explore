# Progress log

## CP-0001 — source extraction and structural orientation

The source-level call sites for Lemma 3.5 in \(G_9,G_{11},G_{12}\) were
located.  Its assumptions on \(\beta_n\) are asymmetric.  The structurally
preferred orientation was identified as
\[
\beta=p_1,\qquad \alpha=\text{the complementary switched product}.
\]
The exact identity
\[
\theta(\nu)=\frac{5(1-\nu)}9,\qquad
\frac4{\theta(\nu)}=\frac{36}{5(1-\nu)},\qquad
\frac4{\theta(1/10)}=8
\]
was checked.  The checkpoint remained inconclusive because no complete
bilinear cells or uniform constants had been frozen.

## CP-0002 — G9 residual reduction and prime-beta sublemma

For a \(G_9\) term, write
\[
N_{\rm global}-b=p_1p_2r.
\]
Outside a squareful-\(p_1\) branch
\(O(N_{\rm global}^{1-\alpha}\log N_{\rm global})\) and a branch supported on
prime divisors of \(N_{\rm global}\) of size \(N_{\rm global}^{o(1)}\), the
sifted residual is a prime \(p_3\ge p_2\).  Thus the switched product has the
form \(p_1(p_2p_3)\).

For a frozen dyadic prime block,
\[
\beta_n=\mathbf1_{\{n\ {\rm prime}\}}\mathbf1_{(n,N_{\rm global})=1},
\]
Siegel--Walfisz proves condition (3.2), and the small-prime exclusion is
automatic.  Upper-bound monotonicity permits lowering the sifting threshold
to \(Q^{1/2}\), giving the exact \(36/5\) coefficient genealogy.

## CP-0003 — primary normalization, residue bridge, and G9 interior cells

The cited primary result uses
\[
x=4MN,\qquad \nu=\frac{\log N}{\log x},
\]
rather than the restatement's \(X=MN\).  A solver lemma candidate extends the
primary result from \(|a|\le x\) to \(|a|\le Cx\) for fixed \(C\), based on the
source's statement that \(a\) enters only through integration by parts and
\(\tau(a)\).

The enhanced range was trimmed to
\[
p_1\le\varepsilon_0^{1/10}N_{\rm global}^{1/10},
\]
which gives \(\nu\le1/10\) exactly.  The fixed-ratio top slice was routed to
the coefficient-\(8\) treatment at
\(O_\varepsilon(N_{\rm global}/\log^3N_{\rm global})\) cost.

A fine multiplicative grid compiled the \(G_9\) interior with prime-supported
beta, \(\alpha\le\tau_2\), scale \(x=4PUV\), and polylogarithmically summable
theorem errors.  The first open layer became the hard product boundaries and
the exact \(Q/\lambda_l^+\) binding.

## CP-0004 — boundary bands, exact sieve binding, and rough residuals

### 1. Multiplicative mesh

Fix
\[
h=(\log N_{\rm global})^{-J},\qquad
\rho=e^h,\qquad J\ge4.
\]
Every prime or rough-residual variable is placed in a half-open cell
\([Y,\rho Y)\).  A \(G_9\) product cell varies by at most \(\rho^3\), while a
\(G_{11}/G_{12}\) product cell varies by at most \(\rho^5\).

### 2. G9 hard product boundaries

For scales \(P,U,V\), call the cell safe when
\[
PUV\ge\varepsilon_0N_{\rm global},
\qquad
\rho^3PUV\le N_{\rm global}.
\]
Every admissible \(G_9\) tuple not in a safe cell lies in one of two bands:
\[
\varepsilon_0N_{\rm global}
\le p_1p_2p_3
\le \rho^3\varepsilon_0N_{\rm global},
\]
or
\[
\rho^{-3}N_{\rm global}
\le p_1p_2p_3
\le N_{\rm global}.
\]

For a boundary \(T\in\{\varepsilon_0N_{\rm global},N_{\rm global}\}\) and
fixed \(p_1,p_2\), the allowed \(p_3\)-interval has length
\[
O\!\left(\frac{hT}{p_1p_2}\right)+O(1).
\]
Ignoring primality only enlarges the count.  The reciprocal sums over the
fixed positive-power ranges for \(p_1,p_2\) are \(O(1)\), while the sum of the
\(O(1)\) terms is power-saving because the maximal combined exponent of
\(p_1p_2\) is below \(0.563\).  Hence
\[
\#\{\text{\(G_9\) product-boundary tuples}\}
\ll \frac{N_{\rm global}}{\log^J N_{\rm global}}
   +N_{\rm global}^{0.563}.
\]
For \(J\ge4\) this is below the \(N/\log^2N\) main scale by at least two
logarithms.

This is a positive error in an upper bound for \(G_9\).  Since \(G_9\) is
subtracted in the final lower bound, it has the harmful sign and is handed to
`A-GB-ERR-0001`.

### 3. Exact cellwise linear-sieve remainder

For a safe cell \(C\), define
\[
Y_C=\sum_{m,n}\alpha_C(m)\beta_C(n)
\]
and the weighted multiset
\[
\mathscr B_C=\{N_{\rm global}-mn\}
\]
with multiplicity \(\alpha_C(m)\beta_C(n)\).

For squarefree \(q\) composed of primes not dividing \(N_{\rm global}\),
\[
A_C(q)=
\sum_{mn\equiv N_{\rm global}\pmod q}
\alpha_C(m)\beta_C(n).
\]
Use the linear-sieve density
\[
\frac{\omega(q)}q=\frac1{\varphi(q)}.
\]
Then
\[
r_C(q)=A_C(q)-\frac{Y_C}{\varphi(q)}
      =E_C(q)-H_C(q),
\]
where
\[
E_C(q)=A_C(q)
-\frac1{\varphi(q)}
 \sum_{(mn,q)=1}\alpha_C(m)\beta_C(n)
\]
is exactly the bracket in Lemma 3.5, and
\[
H_C(q)=\frac1{\varphi(q)}
 \sum_{(mn,q)>1}\alpha_C(m)\beta_C(n).
\]

The second term cannot be silently deleted.  It is the analogue of the
separate \(R_2\) correction displayed in the paper's \(G_8\) model.

### 4. Binding \(Q_C\) and \(\lambda^+_{C,l}\)

Let beta have scale \(P\), alpha scale \(M\), and put
\[
x_C=4PM,\qquad
\nu_C=\frac{\log P}{\log x_C},\qquad
\theta_C=\frac{5(1-\nu_C)}9.
\]
Fix one distribution loss \(\delta_{\rm dist}>0\), and define
\[
Q_C=x_C^{\theta_C-\delta_{\rm dist}},
\qquad
z_C=Q_C^{1/2}.
\]

Apply Lemma 2.5 at \(Q_C,z_C\).  It supplies
\[
1\le l\le L=\exp(8\eta^{-3})
\]
upper weights \(\lambda^+_{C,l}\), each order-1 well-factorable at level
\(Q_C\).  Extend each by zero away from \(q\mid P_N(z_C)\), and apply Lemma
3.5 separately to every \(l\).  Thus the weighted sum of \(E_C(q)\) has an
arbitrarily large logarithmic saving.

The finite factor \(L\), the choice of \(\eta\), and the sieve error
\[
E\ll \eta+\eta^{-8}e^K(\log Q_C)^{-1/3}
\]
are explicit handoffs to `A-GB-ERR-0001`.

### 5. The coprimality correction is power-saving

Every prime factor of \(mn\) in the compiled families is at least
\(N_{\rm global}^{4/53}\), after the separately bounded exceptional branches
are removed.  If \(\ell\mid(mn,q)\), then for an order-1 weight
\[
\sum_{\substack{q\mid P_N(z_C)\\ \ell\mid q}}
\frac{|\lambda^+_{C,l}(q)|}{\varphi(q)}
\ll \frac{\log z_C}{\ell}.
\]
The total multiplicity is bounded by a fixed divisor sum:
\[
\sum_{t\le N_{\rm global}}\tau_k(t)
\ll N_{\rm global}\log^{k-1}N_{\rm global}
\]
for fixed \(k\).  Consequently,
\[
\sum_{l\le L}\sum_q
|\lambda^+_{C,l}(q)|H_C(q)
\ll_{\eta,J}
N_{\rm global}^{1-4/53+o(1)}.
\]
This is again handed to the common-error attempt.

### 6. Main coefficient

At \(z_C=Q_C^{1/2}\), the upper linear-sieve parameter is \(s=2\), hence
\(F(2)=e^\gamma\).  With the dimension-one product,
\[
V_N(z_C)\sim\frac{2e^{-\gamma}C(N_{\rm global})}{\log z_C},
\]
the cell main factor is
\[
Y_CV_N(z_C)F(2)
=(4+o(1))\frac{C(N_{\rm global})Y_C}{\log Q_C}.
\]
Thus the normalizer is
\[
\frac4{\theta_C-\delta_{\rm dist}}
=\frac{36}{5(1-\nu_C)}+O(\delta_{\rm dist})
\]
uniformly on \(\nu_C\le1/10\), and equals \(8+O(\delta_{\rm dist})\) at the
splice.

### 7. G11/G12 rough-residual compiler

Write
\[
N_{\rm global}-b=p_1p_2p_3p_4r.
\]
The original sieve removes every prime factor of \(r\) below \(p_2\) that is
coprime to \(N_{\rm global}p_1\).  A surviving factor \(p_1\) produces a
squareful branch
\[
O(N_{\rm global}^{1-4/53+o(1)}),
\]
and a surviving prime divisor of \(N_{\rm global}\) forces the original
Goldbach prime \(b\) to equal that divisor, giving \(N_{\rm global}^{o(1)}\).
Outside these branches,
\[
r=1\quad\text{or}\quad P^-(r)\ge p_2,
\qquad (r,N_{\rm global}p_1)=1.
\]

For cells
\[
p_1\sim P,\quad p_2\sim U,\quad p_3\sim V,\quad
p_4\sim W,\quad r\sim R,
\]
put \(p_1\) in beta and define alpha by the constrained factorizations
\[
m=p_2p_3p_4r.
\]
All ordering and roughness conditions except \(p_1\le p_2\) lie entirely
inside alpha, and
\[
|\alpha(m)|\le\tau_4(m),\qquad |\beta(n)|\le1.
\]
The supports lie in factor-two intervals for large \(N_{\rm global}\).

The cross-sequence cells with \(p_1\asymp p_2\) form a multiplicative diagonal
of width \(O(h)\).  A trivial interval count gives
\[
O\!\left(\frac{N_{\rm global}}{\log^J N_{\rm global}}\right)
+O\!\left(N_{\rm global}^{1-4/53+o(1)}\right).
\]
The two hard product boundaries contribute
\[
O\!\left(\frac{N_{\rm global}}{\log^J N_{\rm global}}\right)
+O\!\left(N_{\rm global}^{7/11+o(1)}\right).
\]

There are \(O(\log^{5(J+1)}N_{\rm global})\) safe cells.  Taking Lemma 3.5's
arbitrary saving exponent
\[
A>5(J+1)+10
\]
absorbs their summed theorem errors.

### 8. CP-0004 verdict

All thirteen call-interface requirements now have a parametric solver proof
and explicit error handoff.  The three calls are frozen as `SOLVER_PASS`.

The attempt verdict is therefore `PASS`, but only at solver-candidate level.
The fixed-multiple Fouvry extension, residual reductions, boundary estimates,
\(E_C-H_C\) decomposition and power-saving correction require a fresh,
context-isolated verifier.

This verdict excludes the Buchstab main-mass calculation, \(g_{11},g_{12}\)
numerics, `G_7`, the complete signed error ledger, the common \(N_0\), the
Li--Liu main theorem and binary Goldbach.
