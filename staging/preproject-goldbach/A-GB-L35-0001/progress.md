# Progress log

## CP-0001 — source extraction and structural orientation

### Inputs read

- merged Goldbach baseline at `70484b065fc3b6a64f06955a5f9c895531750891`;
- Li–Liu `arXiv:2606.05224v2`;
- Lemma 3.5 and equation (3.2);
- Lemma 2.5 well-factorable upper-sieve remainder;
- definitions of \(G_9,G_{11},G_{12}\);
- equations (5.44)–(5.50);
- content commitments for the v0.3 interface audit and dependency graph.

### Source facts

Lemma 3.5 requires dyadic, fixed-order sequences \(\alpha_m,\beta_n\);
the exact equidistribution condition (3.2) and a small-prime exclusion for
\(\beta_n\); an order-1 well-factorable weight; and

\[
Q=X^{5(1-\nu)/9-\varepsilon},
\qquad
\nu=\frac{\log N_\beta}{\log X}\le\frac1{10}.
\]

The paper explicitly changes from Lemma 3.1 to Lemma 3.5 for the low-\(p_1\)
part of \(G_9\), then states the final integral. For \(G_{11},G_{12}\), it uses
“Similarly as before” and gives final integrals.

### New structured inference

The candidate orientation

\[
\beta=p_1,\qquad
\alpha=(\text{all complementary switched factors})
\]

is preferred over its reverse:

- it makes the short variable track \(p_1\);
- it explains the \(p_1=N^{1/10}\) theorem switch;
- a prime-supported \(\beta\) meets the roughness condition for large blocks;
- the level formula yields the observed \(36/[5(1-u)]\) signature.

This inference is not yet a verified application.

### New interface risk

The congruence residue is the global even integer \(N_{\rm global}\), whereas
Lemma 3.5 states uniformity for \(|a|\le X\), with \(X\) the local product of
dyadic scales. The proof must either establish the stated inequality for every
box or justify a constant-multiple extension while tracking its
\(\varepsilon\)-dependence.

No counterexample has been produced; the status is an open proof obligation.

### Next checkpoint

1. Derive the exact switched remainder for the low-\(p_1\) portion of \(G_9\).
2. Partition \(p_1,p_2\) and the inner prime into dyadic boxes.
3. Write the resulting \(\alpha,\beta,M,N_\beta,X,a,\lambda\) explicitly.
4. Prove the prime-\(\beta\) version of (3.2), including factors dividing
   \(d\) and \(N_{\rm global}\).
5. Repeat the reconstruction for \(G_{11},G_{12}\) only after the \(G_9\)
   template is complete.

### Current verdict

`INCONCLUSIVE`: the source-level call sites are located and a coherent
orientation is identified, but the bilinear forms and uniform constants have
not yet been frozen.


## CP-0002 — G9 switched reduction and prime-beta sublemma

### 1. G9 residual classification

For a term of \(G_9\), write

\[
N_{\rm global}-b=p_1p_2r,
\]

where \(b\) is the prime defining \(\mathscr A\). Since
\(p_2\ge N_{\rm global}^{1/3}\), a composite \(r\) has a prime factor

\[
s\le \sqrt r\le\sqrt{\frac{N_{\rm global}}{p_1p_2}}<p_2.
\]

Such an \(s\) is removed by the sieve unless \(s\mid N_{\rm global}p_1\).
The two exceptional branches are controllable:

- \(s=p_1\) places the element in \(\mathscr A_{p_1^2p_2}\); summing the
  trivial count gives
  \(O(N_{\rm global}^{1-\alpha}\log N_{\rm global})\).
- if \(s\mid N_{\rm global}\), then the prime \(b\equiv0\pmod s\), hence
  \(b=s\); summing divisor factorizations over primes dividing
  \(N_{\rm global}\) gives \(N_{\rm global}^{o(1)}\).

The case \(r=1\) is impossible for sufficiently large \(N_{\rm global}\),
because the definition of \(\mathscr A\) requires
\(p_1p_2\ge\varepsilon N_{\rm global}\), whereas
\(p_1p_2\le N_{\rm global}^{2/3}\).

Thus, up to the displayed negligible branches, \(r=p_3\) is prime and
\(p_3\ge p_2\). This identifies the switched product as

\[
p_1(p_2p_3)\equiv N_{\rm global}\pmod q.
\]

### 2. Prime-beta proof of condition (3.2)

Fix a dyadic block \(Y\le n<2Y\) and put

\[
\beta_n=\mathbf 1_{\{n\text{ prime}\}}\mathbf 1_{(n,N_{\rm global})=1}.
\]

For a fixed residue modulus \(h\) and \((h,n_0)=1\), Siegel--Walfisz on the
interval \([Y,2Y)\) gives equidistribution of the prime indicator. Removing
primes dividing \(d\) changes the two sides by at most a constant multiple of
the number of prime divisors of \(d\) in the interval. For \(h\ge2\), this
number is bounded by \(\tau_h(d)\); for \(h=1\), the two sides are identical.
The fixed exclusion of prime divisors of \(N_{\rm global}\) contributes only
\(O(1)\) primes because \(Y\) is a fixed positive power of
\(N_{\rm global}\). Therefore, for every fixed \(B,h\),

\[
\sum_{\substack{n\equiv n_0\pmod h\\(n,d)=1}}\beta_n
=\frac1{\varphi(h)}\sum_{(n,dh)=1}\beta_n
+O_{B,h}\!\left(
\frac{Y\tau_h(d)}{(\log 2Y)^B}
\right).
\]

This closes condition (3.2) **if** the call compiler proves that the theorem's
\(\beta\)-sequence is exactly the smallest-prime block.

The roughness hypothesis is then elementary for large \(Y\), since a prime
\(n\) has no proper prime factor and
\(n>\exp((\log\log n)^2)\).

### 3. Sieve-level coefficient bridge

The original switched prime contribution is bounded by a sift at
\(N_{\rm global}^{1/2}\). Lemma 2.5, however, states
\(z\le Q^{1/2}\). For an upper bound one may use monotonicity:

\[
S(\mathscr B,\mathscr P,N_{\rm global}^{1/2})
\le S(\mathscr B,\mathscr P,Q^{1/2}).
\]

At \(z=Q^{1/2}\), the linear-sieve parameter is \(s=2\), so
\(F(2)=e^\gamma\). Combining this with the dimension-one product at
\(z=Q^{1/2}\) yields the main coefficient \(4/\theta\). Hence

\[
\theta(\nu)=\frac{5(1-\nu)}9
\quad\Longrightarrow\quad
\frac4{\theta(\nu)}=\frac{36}{5(1-\nu)},
\]

and the splice at \(\nu=1/10\) is exactly \(8\).

### 4. Remaining G9 compiler gap

For dyadic scales \(p_1\asymp P\) and \(p_2p_3\asymp M\), the natural
sequences are

\[
\beta_n=\mathbf1_{n=p_1},\qquad
\alpha_m=\#\{(p_2,p_3):p_2p_3=m\}.
\]

Then \(\alpha_m\le\tau_2(m)\), and \(X=MP\) is comparable with the global
scale. However, the ordering, hyperbolic and product constraints couple
\(p_1\) to \(p_2,p_3\). They must be replaced by a rigorous Cartesian upper
cover, with boundary boxes separately bounded.

A second unresolved point remains: a box meeting
\(\varepsilon N_{\rm global}\le p_1p_2p_3\le N_{\rm global}\) only gives

\[
N_{\rm global}\le C_\varepsilon X,
\]

whereas the stated Lemma 3.5 assumes \(|a|\le X\). A constant-multiple version
is plausible but has not yet been proved from the cited primary theorem.

### 5. Correction for G11/G12

The final residual in \(G_{11},G_{12}\) is counted through Buchstab's function.
Consequently, the complementary \(\alpha\)-sequence should be modeled as
\(p_2p_3p_4r\) with a \(p_2\)-rough integer \(r\), not automatically as a
product with one additional prime.

### Current verdict

`INCONCLUSIVE`, with two genuine sub-obligations closed conditionally:

- prime-supported \(\beta\) satisfies (3.2) and the roughness condition;
- the \(36/5\) and \(8\) coefficient transfer follows exactly after the local
  level has been instantiated.

The earliest remaining step is the Cartesian G9 box compiler plus the
constant-multiple residue-range bridge.
