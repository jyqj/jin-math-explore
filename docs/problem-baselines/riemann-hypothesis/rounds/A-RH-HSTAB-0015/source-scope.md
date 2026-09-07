# Source pins and recovery scope

Date: 2026-09-07. Solver: openai-chatgpt / run-20260907-rh-hole-stability-15.
Git base: main `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`, tree
`d6ac23dc843e26ba123ae167228e3a0c1ff6b750`.

## Frozen mathematical inputs

1. Immediate parent A-RH-DISP-0014 / PR #90 / Issue #86:
   commit `2f5bc3bf2ad050a363caa4cb08ea81d5679531bf`;
   `docs/problem-baselines/riemann-hypothesis/rounds/A-RH-DISP-0014/proof.md`;
   blob `5866044343f85fa6574bb18f42162927a5fe5c62`;
   SHA-256 `76967b81468b488faeb5d5b825672ef1e82af8529766938384b308ddee608b02`.
   Its exact equality classification and equation (28) were reread. The new
   central-row proof does not depend on the classification's correctness.
   Review queue #91 was reread and had no comments/receipt.
2. A-RH-LOC-0012 / PR #77:
   commit `e1042ef83ff3a468dc0faf2d82d19e07b1e5be87`;
   `docs/problem-baselines/riemann-hypothesis/rounds/A-RH-LOC-0012/proof.md`;
   blob `a39aa5e3b2d146d50b33d27dd21d7a711499d7b0`;
   SHA-256 `22d427c4cbbd4027224ca4ac19220671d4d6e7bd61522791af01d3c60b02552f`.
   The mixed-model bridge uses its signed localization and good-block mechanisms,
   whose formulas/proofs are reproduced explicitly in the new note. These are
   still candidate dependencies, not independent receipts.
3. A-RH-HOLE-0013 / PR #82:
   commit `d344b72c6c8f4e1d0057a295675f5b1637c5f5ce`;
   proof blob `802f8f01fd3d1178064b43109aa59b28ce5b0401`;
   SHA-256 `5009d7cece822f8506b6e946df6acaa1366804ab07cb032d1fd8757d40602270`.
   Historical comparison: it required a hole-depth variance hypothesis. That
   hypothesis is not reused here. No claim of re-executing its checker is made.

The current conversation contains the pinned round-12/13 proof text; this run
fresh-read main and the relevant round-14 text/queue. It did not acquire/hash
all predecessor bytes or rerun their complete packages. Parent hashes above
are their published pins, not claims of a new full-archive local hash audit.
No predecessor file is modified. This is a main-based additive archive, not a
stacked import of unmerged staging/knowledge/catalog files.

## External primary source

Y. Lamzouri, *A new proof that more than 2/3 of the zeros of the Riemann zeta
function are simple and on the critical line*, arXiv:2609.02882v1:
https://arxiv.org/html/2609.02882v1

The primary HTML was read in this run, in particular Proposition 2.1 and its
signed Hilbert-space setup, and the discussion preceding Lemma 3.2 about
removing the pair-correlation weight. The latter explicitly warns against
silently interchanging a variable test function with a fixed-test theorem.
The source is context, not a verification of this archive or an extraction
of the supplied periodic cell model. Only HTML was analyzed; no PDF analysis,
PDF hash, source-wide audit, Lean build or new source zero record is claimed.

A bounded search on Toeplitz projections/displacement structure did not find
a primary source establishing the exact new stability statement. Search
non-discovery is not a novelty proof. No literature-wide originality claim
is made; the central-row and projection inequalities are proved directly.

## Scope split

Standalone hole modulus: no common phase, no uniform depth cap, no operator
norm bound, and no exact-equality classification input. Finite paired model
and Toeplitz representation remain explicit.

Mixed-model theorem: supplied unit cells, marks 0/1/2, mean mass one and a
fixed finite depth cap. It uses the signed localization/good-block input.
No actual-zeta source transfer, arithmetic budgets, automatic taper change,
exceptional-energy control, unconditional zero proportion or RH proof follows.
No independent context was used. Mechanical CI and finite checks are not
mathematical verification. A future review may accept the standalone lemma
while returning a dependency-conditional verdict on the mixed consequence.
