# Sources, historical recovery and evidence scope

## Primary mathematical inputs actually read

[L] Youness Lamzouri, *A new proof that more than 2/3 of the zeros of the
Riemann zeta function are simple and on the critical line*,
[arXiv:2609.02882v1](https://arxiv.org/html/2609.02882v1), dated 2026-09-02.
The v1 HTML and abstract were reread on 2026-09-07. Proposition 2.1 supplies
related signed-Hilbert context; Lemma 3.1 states the fixed-test unconditional
pair-correlation input PC, citing Baluyot--Goldston--Suriajaya--Turnage-Butterbaugh.
The fixed-test deweighting in Lemma 3.2 is relevant. The introduction states
the zero-count asymptotic and critical-strip conventions used here.

Theorem 1.1 states the STRONGER existing benchmark
`3/2-cot(1/sqrt(2))/sqrt(2)=0.672500703679...`. This benchmark is explicitly
reported to prevent presenting the weaker round-18 rectangular deduction as
a new record. No claim is made to have independently audited the whole paper,
its external PC input, its formal certificates, or the best literature bound
outside this directly inspected reference. No PDF was analyzed or hashed.

[D] NIST Digital Library of Mathematical Functions,
[section 4.22, equation 4.22.4](https://dlmf.nist.gov/4.22#E4),
`csc(z)^2=sum_(k in Z)(z-k pi)^(-2)`. The HTML equation was read on 2026-09-07.
This classical identity is an explicit external elementary input to the alias
bound, not a claimed new discovery. The two attempted TeX endpoints did not
return usable text; the displayed HTML equation is the source actually used.

## Frozen repository recovery

Historical predecessor: [PR #110](https://github.com/jyqj/jin-math-explore/pull/110),
A-RH-MATCH-0017 at `3be6e0543aee9f26180a90a6ceac5ca288c3bd51`;
proof blob `16eba095fcf5c94a39a07d77355a2d3202236a48`.
Its proof, current PR metadata and review queue #111 were actually read.
The PR was open/unmerged and #111 had no comments/receipt at this read.
No claim is made to have rerun its optimizer or checked every parent file hash.

The earlier mechanisms are pinned, acknowledged and re-derived as needed:

- A-RH-HSTAB-0015 at `bea93a0308a7ddfd6bacc35c547ffd4ab6d5cee9`,
  proof blob `3daba85264af382ae65dbae2924be4e1d74f9160`: central-row counting
  and signed slack. Their relevant full text is in the inherited conversation;
  the new mixed-row proof does not assume its cell-model theorem.
- A-RH-SOURCE-0016 at `02e081262c0f1cadc1ad87043915bd7a2c65c27c`,
  proof blob `93b456345071bd34a794511ff29e620fee6d1ae5`: fixed-bandwidth
  rectangular moment. The relevant proof is in the inherited conversation;
  proof.md section 6 re-derives its sandwich from the newly reread primary PC.

The new finite row and sampling lemmas do NOT depend on accepting the
round-17 optimizer, its Hall bounds, the older good-block Bessel constants,
or the periodized cell-model authority. They are independently stated solver
candidates with proofs, not independent-verifier receipts. The source corollary
does depend on PC and the stated classical facts.

## Computational and publication boundary

The actual local backend and library imports were checked. Direct git transport
failed DNS; the connected GitHub API is used for publication. No source or
private data is sent to any separate worker. The local checker uses only finite
synthetic lists, not measured/certified zeta zeros. Numerical comparisons are
not interval certificates, and SVD range diagnostics do not establish rank.
The rational scalar checks prove only their stated finite inequalities.

The standalone prototype had 150 models; one six-sample development run preceded
one final 120-sample checker run. These are one solver's tests, not independent
verification. The bundled backend-inventory/record runner, full-repository local
test suite and upstream Lean build were not run. Remote CI is reported only
when actually observed in the PR. All earlier files and mathematical authority
are unchanged. No literature-wide novelty, RH proof, or new best proportion is
asserted. The surviving next task is smooth-profile extension plus isolated audit,
not silently returning to an assumed small matching cost.
