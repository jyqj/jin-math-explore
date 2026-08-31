# A-GB-L35-0001 — Lemma 3.5 call compiler

**Issue:** `#34`  
**Branch:** `attempt/preproject-goldbach/l35-call-compiler-01`  
**Baseline:** `70484b065fc3b6a64f06955a5f9c895531750891`  
**Checkpoint:** `CP-0002`  
**Current verdict:** `INCONCLUSIVE`

This pre-genesis solver package compiles the uses of Lemma 3.5 in the low-\(p_1\)
parts of \(G_9,G_{11},G_{12}\). It records exact obligations and the earliest
unsupported interface. It is not a Project result or an independent
verification receipt.

## Progress through CP-0002

1. The theorem's assumptions on \(\beta_n\) are asymmetric. The structurally
   preferred orientation is

   \[
   \beta=p_1,\qquad \alpha=\text{complementary switched product}.
   \]

2. For a frozen dyadic prime block, the prime-supported \(\beta\)-sequence
   satisfies condition (3.2) by Siegel--Walfisz, including the exclusions for
   divisors of \(d\) and the global even integer. The small-prime-factor
   exclusion is also automatic for sufficiently large blocks.
3. For \(G_9\), the residual factor is prime outside a squareful-\(p_1\) branch
   of size \(O(N^{1-\alpha}\log N)\) and a divisor-of-\(N\) branch of size
   \(N^{o(1)}\). Thus the switched product is structurally
   \(p_1(p_2p_3)\).
4. The condition \(z\le Q^{1/2}\) in Lemma 2.5 is met after the safe
   upper-bound enlargement

   \[
   S(\mathscr B,\mathscr P,N^{1/2})
   \le S(\mathscr B,\mathscr P,Q^{1/2}).
   \]

   At \(z=Q^{1/2}\), \(s=2\), giving exactly

   \[
   \frac4{\theta(\nu)}=\frac{36}{5(1-\nu)},
   \qquad \frac4{\theta(1/10)}=8.
   \]
5. For \(G_{11},G_{12}\), the complementary \(\alpha\)-sequence contains a
   Buchstab-counted rough residual; it must not be silently replaced by an
   additional prime.

## Earliest unresolved step

Convert the G9 ordering and hyperbolic constraints into a rigorous Cartesian
upper cover with frozen

```text
M, N_beta, X=M*N_beta
alpha_m, beta_n
residue a
well-factorable lambda and level Q
```

for every box. Then prove a constant-multiple extension of Lemma 3.5 from
\(|a|\le X\) to the actual relation \(|N_{\rm global}|\le C_\varepsilon X\),
or redesign the decomposition so the stated range applies literally.

## Files

- `source-lock.json` — frozen source/version and legacy commitments.
- `call-matrix.json` — requirements, three calls, findings and current verdict.
- `progress.md` — append-only checkpoint derivation.
- `attempt.json` — artifact hashes and authority boundary.
- `check_call_matrix.py` — deterministic structural validator.

## Reproduction

```bash
python -S staging/preproject-goldbach/A-GB-L35-0001/check_call_matrix.py
```

A checker PASS means only that the checkpoint package is internally consistent.
