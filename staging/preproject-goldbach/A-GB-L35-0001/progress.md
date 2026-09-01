# Progress log

## CP-0001 — source extraction and structural orientation

The source-level call sites for Lemma 3.5 in \(G_9,G_{11},G_{12}\) were located.
The assumptions on \(\beta_n\) are asymmetric, and the structurally preferred
orientation was identified as
\[
\beta=p_1,\qquad \alpha=\text{the complementary switched product}.
\]
The coefficient identity
\[
\theta(\nu)=\frac{5(1-\nu)}9,\qquad
\frac4{\theta(\nu)}=\frac{36}{5(1-\nu)},\qquad
\frac4{\theta(1/10)}=8
\]
was checked exactly.  The checkpoint remained inconclusive because the actual
bilinear cells and uniform constants had not been frozen.

## CP-0002 — G9 residual reduction and prime-beta sublemma

For a \(G_9\) term write
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
\beta_n=\mathbf 1_{\{n\ {\rm prime}\}}\mathbf 1_{(n,N_{\rm global})=1},
\]
Siegel--Walfisz proves condition (3.2), and the small-prime exclusion is
automatic.  Upper-bound monotonicity permits lowering the sifting threshold to
\(Q^{1/2}\), giving the exact \(36/5\) coefficient genealogy.

The earliest remaining issues were a Cartesian box decomposition, the relation
between the global residue and the local product scale, and the exact
\(\nu\le1/10\) endpoint.

## CP-0003 — primary-source normalization, residue bridge, and G9 interior cells

### 1. Primary-source normalization correction

Li--Liu state Lemma 3.5 with sequences supported in \([M,2M]\), \([N,2N]\)
and \(X=MN\).  The cited primary source, Fouvry's Corollaire 2(i), instead
normalizes the scale as
\[
x=4MN,\qquad \nu=\frac{\log N}{\log x},
\]
and is uniform for \(|a|\le x\).

The factor \(4\) is asymptotically harmless for the exponent and log-saving
because the theorem contains an arbitrary exponent loss, but it is not
harmless bookkeeping: it must be restored when checking the residue range and
the exact definition of \(\nu\).

### 2. Fixed-multiple residue lemma

**Lemma candidate.**  For every fixed \(C\ge1\), Fouvry Corollaire 2(i)
continues to hold uniformly for
\[
|a|\le Cx
\]
with an implied constant depending on \(C\).

**Proof audit.**  At the end of the proof under condition (C.2), Fouvry states
that the size of \(a\) enters only:

1. in the integration-by-parts derivative bounds; and
2. through the divisor function \(\tau(a)\).

Replacing \(|a|\le x\) by \(|a|\le Cx\) multiplies the derivative bounds by a
fixed factor.  Moreover, for every auxiliary \(\delta>0\),
\[
\tau(a)\ll_\delta |a|^\delta
       \le C^\delta x^\delta,
\]
which is absorbed by the arbitrary internal power/log slack.  No other step of
the source proof uses the magnitude of \(a\).

This is a complete solver derivation but still requires a fresh verifier to
check every occurrence of \(a\) in the primary proof.

### 3. Application to the Goldbach residue

Use a fine multiplicative cell ratio
\[
\rho=\exp((\log N_{\rm global})^{-J}),\qquad J\ge4,
\]
so that \(\rho^3\le4\) for large \(N_{\rm global}\).  In a \(G_9\) cell let
\[
p_1\in[P,\rho P),\quad
p_2\in[U,\rho U),\quad
p_3\in[V,\rho V).
\]
Set \(M=UV\).  Then
\[
t=p_1p_2p_3\le \rho^3 PM\le4PM=x.
\]
The Goldbach construction also has \(t\ge\varepsilon_0N_{\rm global}\), hence
\[
N_{\rm global}\le\varepsilon_0^{-1}x.
\]
The fixed-multiple lemma applies with \(C=\varepsilon_0^{-1}\).  Its constant
is allowed to depend on the paper's fixed \(\varepsilon_0\).

Thus the earlier residue-range obstruction is repaired; it is no longer the
first unresolved step.

### 4. Exact treatment of the \(\nu=1/10\) endpoint

The primary-source short exponent is
\[
\nu=\frac{\log P}{\log x}.
\]
Put
\[
c_{\varepsilon}=\varepsilon_0^{1/10}.
\]
For enhanced-level cells with
\[
p_1\le c_\varepsilon N_{\rm global}^{1/10},
\]
we have
\[
P^{10}\le\varepsilon_0N_{\rm global}\le x,
\]
so \(\nu\le1/10\) exactly.

The discarded transition slice
\[
c_\varepsilon N_{\rm global}^{1/10}
   <p_1\le N_{\rm global}^{1/10}
\]
has fixed multiplicative width.  Mertens' theorem for primes gives
\[
\sum_{\text{transition slice}}\frac1p
  =O_\varepsilon\!\left(\frac1{\log N_{\rm global}}\right).
\]
Sending this slice to the coefficient-\(8\) treatment changes the \(G_9\)
upper bound by
\[
O_\varepsilon\!\left(\frac{N_{\rm global}}{\log^3N_{\rm global}}\right).
\]
The lower bound \(\nu\ge\varepsilon_{\rm lemma}\) follows from
\(p_1\ge N_{\rm global}^{4/53}\) and \(x\le4N_{\rm global}\) for sufficiently
large \(N_{\rm global}\).

This closes the range condition, with the transition error handed to
`A-GB-ERR-0001`.

### 5. G9 interior cell compiler

For every \(p_1\)-cell define
\[
\beta_P(n)=
\mathbf1_{\{n\ {\rm prime},\ P\le n<\rho P,\ (n,N_{\rm global})=1\}}.
\]
For \(p_2,p_3\)-cells define
\[
\alpha_{U,V}(m)=
\#\{(p_2,p_3):p_2p_3=m,\ U\le p_2<\rho U,\
V\le p_3<\rho V,\ p_2\le p_3,\ (m,N_{\rm global})=1\}.
\]
Then
\[
|\beta_P(n)|\le1,\qquad
|\alpha_{U,V}(m)|\le\tau_2(m),
\]
and the supports lie in \([P,2P]\) and \([UV,2UV]\).  On every cell whose
whole product box lies in
\[
\varepsilon_0N_{\rm global}\le p_1p_2p_3\le N_{\rm global},
\]
all dyadic-support, order, local-scale, prime-\(\beta\), residue and \(\nu\)
requirements are explicit.

The condition
\[
p_2\le (N_{\rm global}/p_1)^{1/2}
\]
does not create a separate interior constraint: it follows from
\(p_3\ge p_2\) and \(p_1p_2p_3\le N_{\rm global}\).

There are only polylogarithmically many fine cells.  Since Lemma 3.5 allows
arbitrary log saving \(A\), the sum of the **interior theorem errors** is
absorbed by choosing \(A\) larger than the mesh exponent.

### 6. Earliest remaining obstruction

The first unresolved G9 step is now:

1. give a signed, source-backed treatment of cells crossing
   \(p_1p_2p_3=\varepsilon_0N_{\rm global}\) or
   \(p_1p_2p_3=N_{\rm global}\), or replace the hard product cutoff by a
   smooth hyperbolic/Mellin partition;
2. bind every interior cell to the actual order-1 well-factorable remainder
   weight from Lemma 2.5 and verify the exact level \(Q\);
3. carry the top-slice and mesh-boundary losses into the common error ledger;
4. reconstruct the Buchstab-counted rough residual for \(G_{11},G_{12}\).

### Current verdict

`INCONCLUSIVE`, but the frontier moved: the residue-size and \(\nu\)-endpoint
questions are repaired by a primary-source normalization audit and explicit
range split.  The active obstruction is the product-boundary partition and
cellwise sieve-weight binding.
