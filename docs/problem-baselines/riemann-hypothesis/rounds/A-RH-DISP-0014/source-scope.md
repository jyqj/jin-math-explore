# Source scope and recovery map

## Frozen mathematical inputs actually read

The main ref was freshly read as `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`,
unchanged from the governance files read in this conversation. This round read
PR #82's metadata, both portions of the parent proof, and #83's comments;
PR #82 was open/unmerged and #83 had no comments or receipt at that read.
No status of an unread review queue is inferred.

- Immediate parent: `d344b72c6c8f4e1d0057a295675f5b1637c5f5ce`,
  `docs/problem-baselines/riemann-hypothesis/rounds/A-RH-HOLE-0013/proof.md`,
  blob `802f8f01fd3d1178064b43109aa59b28ce5b0401`.
  Parent result: common-depth energy comparison, conditional hole-depth
  variance criterion, real-model local floor, and variable-depth counterexample.
- Earlier operator input: `340d6c4a3f2101d2cd08834ee3fe9cc9aed8f202`,
  `staging/preproject-rh/A-RH-WTP-0004/README.md`,
  blob `49c16fe11d858345ecfbe1f351f694bb41a4d116`, especially sections 4-5.
  This already supplied moderate-depth exact-grid operator coercivity.
  Its relevant pages were reread; neither its whole checker nor upstream
  Lean code was rerun. This result is acknowledged, not claimed as new.
- Scalar comparison ancestor available in this conversation:
  `e1042ef83ff3a468dc0faf2d82d19e07b1e5be87`,
  `docs/problem-baselines/riemann-hypothesis/rounds/A-RH-LOC-0012/proof.md`,
  blob `a39aa5e3b2d146d50b33d27dd21d7a711499d7b0`.
  Its 286/189 scalar point is contrasted with the new exact-equality floor;
  the finite-to-uniform-stability gap is not suppressed.

These locators bind the mathematical dependencies. Reading a reported blob SHA
is not a claim that every parent archive file was locally downloaded and hashed.
Every dependency remains an unverified solver candidate. Same-run re-derivation
is not an independent receipt.

## Primary external context, freshly consulted

Youness Lamzouri, *A new proof that more than 2/3 of the zeros of the Riemann zeta
function are simple and on the critical line*, arXiv:2609.02882v1, submitted
2026-09-02. The abstract/version page and v1 HTML were consulted in this run:

- https://arxiv.org/abs/2609.02882
- https://arxiv.org/html/2609.02882v1

The displayed version history contained v1. Proposition 2.1 concerns a finite
conjugation-symmetric Hilbert-space inequality; it motivates the signed
framework, not the new cell representation, Dirichlet estimate or equality
classification. No new arithmetic theorem is imported, and the paper was not
independently rebuilt or source-audited in full. No PDF was analyzed.

A bounded search on Toeplitz idempotents/projections and circulants returned,
among other material, Kucerovsky, Mousavand and Sarraf, *On some properties of
Toeplitz matrices*, DOI 10.1080/23311835.2016.1154705. The publisher full-text
fetch failed. No theorem from that unread paper is used. The elementary
projection lemma is proved directly in this archive; the search is insufficient
to establish novelty or a complete prior-art assessment. Self-inversive and
Fourier/Newton arguments are not claimed as new mathematical techniques.

## Publication and evidence boundary

Git base and mathematical parent are deliberately different: this main-based
PR adds only the nine new files, without importing predecessor staging or the
unmerged knowledge/catalog baseline. It does not modify previous candidate
bytes, Project heads, registries, shared results, policies, CI or receipts.

New code was executed locally. Direct git transport was attempted and failed
DNS; GitHub connector reads/writes were used for persistence. Backend readiness
was checked through the actual local executable/imports; sage and wolframscript
were absent from PATH. The repository's bundled backend inventory/record runner
and full-repository local tests were not run. This is not a claim about all
possible MCP services or installations. No upstream Lean build, independent
verifier, actual zero enumeration or source moment computation was performed.
Remote CI is observed and reported in the PR separately, not predicted here.
