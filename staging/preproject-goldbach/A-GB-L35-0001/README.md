# A-GB-L35-0001 — Lemma 3.5 call compiler

**Issue:** `#34`  
**Branch:** `attempt/preproject-goldbach/l35-call-compiler-01`  
**Baseline:** `70484b065fc3b6a64f06955a5f9c895531750891`  
**Checkpoint:** `CP-0001`  
**Current verdict:** `INCONCLUSIVE`

This pre-genesis solver package compiles the uses of Lemma 3.5 in the low-\(p_1\) parts of
\(G_9,G_{11},G_{12}\). It records exact obligations and the earliest unsupported
interface. It is not a Project result or an independent verification receipt.

## What CP-0001 establishes

1. The theorem's assumptions on \(\beta_n\) are asymmetric; an omitted
   \(\alpha/\beta\) orientation must be reconstructed.
2. The structurally preferred orientation is

   \[
   \beta_n=\mathbf 1_{\{n=p_1\}},\qquad
   \alpha_m=\#\{\text{complementary switched factorizations of }m\}.
   \]

   This is still a hypothesis until the switched remainder is written block by block.
3. Under this orientation, the roughness condition on \(\beta\) is elementary for
   sufficiently large prime blocks, while condition (3.2) should be reduced to a
   precise prime-in-arithmetic-progressions lemma.
4. The algebraic coefficient signature is exact:

   \[
   \theta(\nu)=\frac{5(1-\nu)}9,\qquad
   \frac4{\theta(\nu)}=\frac{36}{5(1-\nu)},\qquad
   \frac4{\theta(1/10)}=8.
   \]

   This explains the displayed \(36/5\) and the continuous splice at \(1/10\),
   conditional on the local-variable mapping.
5. A previously implicit obligation is now explicit: the global residue
   \(a=N_{\rm global}\) must lie in Lemma 3.5's local uniform range \(|a|\le X\)
   for every dyadic box, or a constant-multiple extension must be justified.

## Earliest unresolved step

Write the low-\(p_1\) switched remainder before summing over prime ranges, then freeze
for each box:

```text
M, N_beta, X=M*N_beta
alpha_m, beta_n
residue a
well-factorable lambda and level Q
```

Only after this step can the call matrix move from structural inference to theorem
verification.

## Files

- `source-lock.json` — frozen source/version and legacy commitments.
- `call-matrix.json` — requirements, three calls, findings and current verdict.
- `progress.md` — append-only checkpoint narrative.
- `attempt.json` — artifact hashes and authority boundary.
- `check_call_matrix.py` — deterministic structural validator.

## Reproduction

```bash
python -S staging/preproject-goldbach/A-GB-L35-0001/check_call_matrix.py
```

A checker PASS means only that the checkpoint package is internally consistent.
