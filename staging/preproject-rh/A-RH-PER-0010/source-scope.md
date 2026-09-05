# Source, dependency and scope

Checked: 2026-09-06. Solver run: run-20260906-rh-periodic-rigidity-10.

## Read-only repository state

Parent: jyqj/jin-math-explore@a97c80778bda2c5a337be978ccc9afec36b750ea,
staging/preproject-rh/A-RH-SMP-0009/. All six SHA-256 pointers in its
supplied archive matched the bytes. Main was reread at
39002c5a6af8c7b7f093589e6a76cfd218fcbb99. Parent review queue #64 had no
comments or receipt at startup. The current run inherits solver conversation
context and is not an independent verifier.

Frozen ancestor A-RH-SRE-0007 supplies the signed Gram-decomposition idea;
A-RH-AOC-0008 supplies the two-channel positive correlation idea. The present
README re-derives each required estimate with its new one-cell Bessel input.
Ancestor status is not promoted or treated as a verified theorem.

## Primary external context

Youness Lamzouri, arXiv:2609.02882v1, submitted September 2, 2026,
*A new proof that more than 2/3 of the zeros of the Riemann zeta function
are simple and on the critical line*.

https://arxiv.org/abs/2609.02882
https://arxiv.org/html/2609.02882v1

The primary abstract and HTML, particularly Proposition 2.1 and its setup,
were reread. This supplies the finite signed-Hilbert context, not the current
periodic representation or a new arithmetic estimate. Its weighted/unweighted
source distinction is not resolved by computing a box-periodic limit here.
No paper verification, Lean rebuild or literature-wide novelty is claimed.

## Delta from the predecessor

The predecessor treats sparse interfaces or sublinear total variation.
This package treats exactly repeated finite patterns with arbitrarily dense
interfaces. Periodic moments have a finite exact spectral limit. At the
long scale this is exactly the norm of a Q-by-Q signed matrix. Vandermonde
independence classifies exact equality, including patterns with no simple
point. A quantitative all-center phase/depth bound uses a positive simple
fraction and degrades with Q; collisions are aggregated safely. Neither
exact repetition nor small Q-squared times defect is proved for actual zeros.

The direct Q-by-Q reconstruction was added after the first local full run;
the final checker was rerun with the new reconstruction and anchorless tests.
This is a scope-driven finalization rerun, not independent verification.
A preliminary 972-point grid explored the formula before the recorded run;
no global optimization or certificate is inferred from that finite grid.

Direct git access failed DNS. Publication uses the connected GitHub API.
Only package-local JSON/schema/path/hash checks were run; no full repository
CI, bundled inventory/record runner, source build or isolated verifier.
