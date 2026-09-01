# A-GB-L35-0001 — Lemma 3.5 call compiler

**Issue:** `#34`  
**Branch:** `attempt/preproject-goldbach/l35-call-compiler-01`  
**Baseline:** `70484b065fc3b6a64f06955a5f9c895531750891`  
**Checkpoint:** `CP-0003`  
**Current verdict:** `INCONCLUSIVE`

This pre-genesis package compiles the uses of Lemma 3.5 in the low-\(p_1\)
parts of \(G_9,G_{11},G_{12}\).  It is solver output, not a Project result or
an independent verification receipt.

## New progress at CP-0003

1. The cited primary theorem was inspected.  Fouvry's normalization is
   \(x=4MN\), not \(X=MN\).
2. A fixed-multiple extension
   \[
   |a|\le Cx
   \]
   was derived from the primary proof for fixed \(C\).  In the Goldbach cells,
   \(N_{\rm global}\le x/\varepsilon_0\), repairing the earlier residue-range
   obstruction.
3. The enhanced-level range is trimmed to
   \[
   p_1\le\varepsilon_0^{1/10}N_{\rm global}^{1/10},
   \]
   which gives \(\nu\le1/10\) exactly.  The remaining constant-ratio slice is
   handed to the coefficient-\(8\) method with
   \(O_\varepsilon(N/\log^3N)\) cost.
4. A fine multiplicative compiler now gives valid **G9 interior cells** with
   prime-supported \(\beta\), \(\alpha\le\tau_2\), explicit primary scale
   \(x=4MP\), and polylogarithmically summable theorem errors.

## Earliest unresolved step

Treat the two product-boundary cell families without losing the signed sieve
remainder, and bind each interior cell to the exact Lemma 2.5 well-factorable
weight and level \(Q\).  The Buchstab rough residual for \(G_{11},G_{12}\)
also remains open.

## Files

- `source-lock.json` — Li--Liu and Fouvry source/version/normalization record.
- `call-matrix.json` — requirements, calls, findings and active obstruction.
- `progress.md` — append-only mathematical checkpoint derivation.
- `attempt.json` — artifact hashes and authority boundary.
- `check_call_matrix.py` — deterministic package checker.

## Reproduction

```bash
python -S staging/preproject-goldbach/A-GB-L35-0001/check_call_matrix.py
```

A checker PASS establishes internal consistency only.  It does not verify the
fixed-multiple source lemma, the complete Li--Liu proof, or binary Goldbach.
