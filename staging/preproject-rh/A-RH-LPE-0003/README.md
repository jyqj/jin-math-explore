# Pre-genesis RH attempt III: critical-lattice phase extraction

Status: `active / proof_candidate`

Attempt ID: `A-RH-LPE-0003`

Actor/run: `openai-gpt-5.6-pro / run-20260829-rh-lattice-extraction-03`

Base: `A-RH-RTD-0002@698d28d4e074f09fdb7dfdaffc65df1cdc94727b`

Issue: `#30`

Independent parent verification: `#29` for `A-RH-RTD-0002`, `#25` for `A-RH-RTD-0001`

Sibling isolation: `#28` is an independent active attempt; its staging is not read by this run.

This is single-writer pre-genesis staging. It does not create a governed Riemann-hypothesis Project, modify a Project head, publish a shared result, improve an unconditional zeta-zero proportion, or prove the Riemann hypothesis.

## 1. Why this attempt exists

The preceding attempt found a finite ideal two-scale mechanism with optimal relative scale `3/4`. At fixed reference density `theta`, the model gain over the one-scale Zeta23 certificate is

\[
\frac{5\theta}{96}-\frac98\varepsilon.
\]

The main unresolved bridge was described as “extract a critical-lattice occupancy model from near equality.” That phrase was still too coarse. This attempt decomposes it into exact finite lemmas and identifies which part genuinely remains analytic.

## 2. Main finite result: local phase synchronization

For a weighted graph on real positions `x_i`, assume the graph Poincaré inequality with constant `lambda_G`, every positive edge has coordinate length at most `R`, and define

\[
E_{\rm sinc}
=\sum_{i<j}a_{ij}\operatorname{sinc}^2(x_i-x_j).
\]

Then some phase `tau mod 1` satisfies

\[
\boxed{
\sum_iw_i\operatorname{dist}(x_i-\tau,\mathbb Z)^2
\le
\frac{\pi^2R^2}{2\lambda_G}E_{\rm sinc}.}
\]

The proof embeds each point as `exp(2*pi*i*x_i)`, applies the weighted graph Poincaré inequality, projects the weighted mean back to the unit circle, and converts chordal distance to torus distance.

This is not merely a numerical observation; a complete derivation with constants is in `phase-synchronization.md`.

## 3. Strong simplification: bounded blocks need no conjectural graph gap

Inside one interval of diameter `R`, choose the complete weighted graph

\[
a_{ij}=w_iw_j.
\]

Its weighted Poincaré constant is **exactly** the total block mass

\[
\lambda_G=W=\sum_iw_i.
\]

Therefore

\[
\sum_iw_i\operatorname{dist}(x_i-\tau,\mathbb Z)^2
\le
\frac{\pi^2R^2}{2W}
\sum_{i<j}w_iw_j\operatorname{sinc}^2(x_i-x_j).
\]

This removes one proposed bottleneck: a separate local spectral-gap conjecture is unnecessary if the long-scale defect controls the complete pair energy inside each bounded block.

## 4. Quantitative random-partition extraction

For an integer-weighted real configuration of total mass `N`, let

\[
E=\sum_{i<j}m_im_j\operatorname{sinc}^2(x_i-x_j),
\qquad e=E/N.
\]

Partition the line into shifted blocks of length `R`. Applying the complete-block theorem in every block gives total squared phase loss at most

\[
\frac{\pi^2R^2}{2}E.
\]

After deleting points farther than `eta` from their block phase and points within local observation radius `r` of a block boundary, one can choose the shift so that the deleted mass fraction is at most

\[
\frac{\pi^2R^2e}{2\eta^2}+rac{2r}{R}.
\]

The balanced choice

\[
R=e^{-1/5},
\qquad
\eta=e^{1/5}
\]

gives deleted fraction

\[
\le
\left(\frac{\pi^2}{2}+2r\right)e^{1/5},
\]

while every retained radius-`r` neighborhood lies within `e^{1/5}` of a single blockwise translate of `Z`.

Thus the ideal implication

```text
long-scale complete sinc energy = o(N)
  => after deleting o(N) mass, every fixed local window is asymptotically lattice-supported
```

is now a finite theorem candidate with an explicit rate.

## 5. A global phase is not required for the ideal two-scale count

Different large blocks may have different lattice phases. Because the short kernel `sinc^2(alpha t)` is nonnegative, cross-block terms may be discarded. On periodized ideal blocks, the symbol lower bound and Cauchy--Schwarz combine to give

\[
F_{\rm block}
\ge
\omega_\alpha\sum m_{b,n}^2
+
\left(\frac1\alpha-\omega_\alpha\right)\frac N\theta,
\qquad
\omega_\alpha=\frac{2\alpha-1}{\alpha^2}.
\]

The integer inequality `1_{m=1} >= 2m-m^2` then recovers

\[
\frac{s_1}{N}
\ge
2-\frac1\theta-
\frac{\alpha\theta}{3\omega_\alpha}
-
\frac\varepsilon{\omega_\alpha}.
\]

At `alpha=3/4`, this is the parent bound

\[
2-\frac1\theta-rac{9\theta}{32}-\frac98\varepsilon.
\]

Therefore phase stitching across the entire height window is not necessary for the cyclic ideal model. Only local phases on growing blocks are needed.

## 6. Finite intervals and approximate lattice points

Two further finite corrections are recorded.

### 6.1 Toeplitz boundary correction

For a finite `d`-cell interval, the constant vector is not an exact eigenvector of the Toeplitz sinc-squared matrix. Writing the missing row sums as `b_i`, with

\[
B_d=\sum b_i,
\qquad
C_d=\sum b_i^2,
\]

the exact lower bound is

\[
\langle m,T_dm\rangle
\ge
(\omega_\alpha-\rho)V
+
\frac{N^2}{\alpha d}
-
\mu^2\left(B_d+\frac{C_d}{\rho}\right).
\]

The package proves

\[
B_d=O(\log d),
\qquad C_d=O(1)
\]

with explicit constants. Hence large blocks recover the cyclic formula up to a boundary loss, provided high-density blocks are controlled.

### 6.2 Approximate-cell kernel stability

If every retained point is within `eta<=1/4` of a block lattice cell, then at `alpha=3/4` the short quadratic form differs from its exact-cell form by at most

\[
25.226\,\eta\sum_nm_n^2.
\]

This follows from an `ell^1` bound on the sampled derivative of `sinc^2(3t/4)` and Young's convolution inequality. Therefore `eta->0` and a cell second moment `O(N)` make the positional replacement cost `o(N)`.

## 7. Exact obstruction models retained

Two countermodels prevent overclaiming.

1. **Disconnected cosets.** Two disconnected integer cosets can have zero edge sinc energy while no common global phase exists. Connectedness, overlap, or the local-block interpretation is essential.
2. **Low-gap path.** For `x_j=j+j/n` on a path, the sinc energy is `Theta(1/n)`, the graph gap is `Theta(1/n^2)`, and common-phase loss is `Theta(n)`. A global graph argument cannot suppress the inverse-gap factor.

The random-partition route bypasses both obstructions by seeking local phases on blocks whose diameter grows only after the long-scale energy per mass tends to zero.

## 8. Deterministic evidence

Run:

```bash
python3 check_phase_synchronization.py \
  --trials 250 \
  --size 24 \
  --overlap-points 16 \
  --seed 20260829 \
  --max-power 9
```

The current exact script reports PASS for:

- weighted local phase synchronization;
- the exact complete-block gap `lambda_G=sum w_i`;
- overlap phase stitching;
- finite-Toeplitz boundary inequalities;
- the `25.226 eta` approximate-cell kernel bound;
- random-partition phase and exceptional-mass bounds;
- the disconnected two-coset countermodel;
- the low-gap path scaling model.

The checker validates finite identities and implementations. It is not evidence for the missing Zeta23 analytic hypotheses.

## 9. What remains genuinely hard

The phrase “critical-lattice extraction” has now been reduced to the following narrower obligations:

1. **on-line energy isolation** — derive `E=o(N)` for the effective on-line long-scale sinc/taper energy from near equality of the full indefinite `P+Q` certificate;
2. **off-line finite-section stability** — prevent off-line pair blocks from hiding a large on-line short-scale form; use the complete-frame `(p,p)` inertia theorem plus a quantitative finite-section/divided-difference lower bound;
3. **smooth-taper transfer** — compare the actual Zeta23 kernel with the ideal sinc-squared kernel;
4. **density and boundary ledger** — control high-density blocks and sum the finite-Toeplitz correction;
5. **deleted-mass contamination** — show that deleted atoms contaminate at most the same order of candidate simple cells and do not destroy the short-form upper bound;
6. **budget closure** — keep all normalized losses below
   \[
   \frac{-27\theta^2+128\theta-96}{108\theta}
   \]
   for a fixed `theta>(64-4sqrt(94))/27`.

## 10. Current research decision

The next active subproblem is no longer “prove one global lattice phase.” It is:

> Prove that parent rank--trace near equality yields an effective on-line complete sinc/taper energy `o(N)`, or construct an admissible indefinite `P+Q` countermodel showing that this implication fails even after the complete-frame pair-inertia constraints are imposed.

If the implication holds, the finite extraction, blockwise occupancy, Toeplitz and kernel-stability machinery in this package supplies most of the remaining ideal zero-side bridge.

## 11. Authority and non-implication boundary

- Every statement in this attempt is a solver proof candidate until a fresh independent-verifier run checks the frozen hashes.
- The parent attempts `A-RH-RTD-0001` and `A-RH-RTD-0002` are also awaiting independent verification.
- `E=o(N)` has not been proved for actual Zeta23 on-line modes.
- The actual smooth taper, finite grid, off-line pair contribution, tail and normalization have not been closed within budget.
- No unconditional zeta-zero proportion has been improved.
- Nothing here proves or refutes the Riemann hypothesis.
