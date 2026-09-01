# A-GB-L35-0001 — Lemma 3.5 call compiler

**Issue:** `#34`  
**Branch:** `attempt/preproject-goldbach/l35-call-compiler-01`  
**Baseline:** `70484b065fc3b6a64f06955a5f9c895531750891`  
**Checkpoint:** `CP-0004`  
**Solver verdict:** `PASS`  
**Independent verification:** `PENDING`

This frozen pre-genesis package compiles the uses of Lemma 3.5 in the
low-\(p_1\) portions of \(G_9,G_{11},G_{12}\).  `PASS` is deliberately scoped
to the **call interface**: sequence orientation, support/order, local scale,
\(\nu\)-range, residue uniformity, well-factorable level, boundary removal,
remainder decomposition, coefficient transfer and error handoffs.

It is not a Project result or a verification receipt.

## What CP-0004 closes at solver level

1. **Hard product boundaries.**  A fine multiplicative grid with
   \[
   h=(\log N)^{-J},\qquad \rho=e^h,\qquad J\ge4
   \]
   separates safe cells from bands crossing
   \(p_1m=\varepsilon_0N\) or \(p_1m=N\).  Elementary interval counting gives
   \(O(N/\log^J N)\) plus power-saving terms.  For \(G_{11},G_{12}\), the
   cross-sequence diagonal \(p_1\asymp p_2\) has the same error type.

2. **Exact cellwise sieve/mean-value binding.**  For a cell with beta scale
   \(P\) and alpha scale \(M\), use
   \[
   x_C=4PM,\quad
   \nu_C=\frac{\log P}{\log x_C},\quad
   Q_C=x_C^{5(1-\nu_C)/9-\delta},\quad
   z_C=Q_C^{1/2}.
   \]
   Lemma 2.5 supplies finitely many order-1 well-factorable
   \(\lambda^+_{C,l}\) at the same level \(Q_C\); Lemma 3.5 is applied to
   each \(l\).

3. **Coprimality correction made explicit.**  The linear-sieve remainder is
   written
   \[
   r_C(q)=E_C(q)-H_C(q),
   \]
   where \(E_C\) is exactly the Lemma 3.5 bracket and \(H_C\) is the
   \(R_2\)-type correction from factors shared with \(q\).  Because every
   switched factor is at least \(N^{4/53}\),
   \[
   \sum_{l,q}|\lambda^+_{C,l}(q)|H_C(q)
   \ll_{\eta,J}N^{1-4/53+o(1)}.
   \]

4. **\(G_{11},G_{12}\) rough residual compiled.**  Outside explicit squareful
   and divisor-of-\(N\) branches, write
   \[
   N-b=p_1p_2p_3p_4r,\qquad r=1\ \text{or}\ P^-(r)\ge p_2.
   \]
   Put \(p_1\) in beta and \((p_2,p_3,p_4,r)\) in alpha.  Then
   \[
   |\beta|\le1,\qquad |\alpha(m)|\le\tau_4(m),
   \]
   so the same Lemma 3.5 interface applies.

5. **Coefficient genealogy retained.**  At \(z_C=Q_C^{1/2}\), \(F(2)=e^\gamma\)
   and the main normalization is
   \[
   \frac{4}{\theta_C-\delta},\qquad
   \theta_C=\frac{5(1-\nu_C)}9.
   \]
   As the declared loss tends to zero this gives
   \(36/[5(1-\nu_C)]\), equal to \(8\) at \(\nu_C=1/10\).

## What is not closed

- the fixed-multiple extension of Fouvry's residue range needs a fresh verifier;
- the boundary estimates, residual reductions and \(H_C\) correction need
  independent checking;
- the Buchstab mass asymptotics and numerical bounds for \(g_{11},g_{12}\)
  are outside this verdict;
- `A-GB-G7-0001` and `A-GB-ERR-0001` remain open;
- no whole-paper or binary-Goldbach conclusion is made.

## Files

- `source-lock.json` — exact source/version/locator and normalization record.
- `call-matrix.json` — thirteen requirements, three calls, derived lemmas and
  non-implication boundary.
- `progress.md` — append-only mathematical derivation through CP-0004.
- `attempt.json` — frozen artifact hashes and authority declaration.
- `check_call_matrix.py` — deterministic structural validator.

## Reproduction

```bash
python -S staging/preproject-goldbach/A-GB-L35-0001/check_call_matrix.py
```

A checker PASS proves package consistency only.
