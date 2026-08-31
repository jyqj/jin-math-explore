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
