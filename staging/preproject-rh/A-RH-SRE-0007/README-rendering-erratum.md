# Rendering-only erratum for README equation (0.1)

Date: 2026-09-05. Issue #54. No mathematical or computational change.
Frozen candidate commit: 9715ec125e7dd357a464b5e2156e799017c75e8d.
Frozen README Git blob: ed255b1d98072e4f273ea9436d00b72fdaac6ab1.

The subscript in the summary equation on README line 28 contains a U+000D
control character introduced by string escaping. Read the intended formula as:

```text
sum_{i != j; i,j retained} sinc(x_i-x_j)^2 <= 7D.
```

The retained subfamily, ordered-pair convention and bound are already stated
in the surrounding prose and proved in README Section 4. This erratum does
not change any claim, hypothesis, proof, code, test result or hash pointer.
All seven originally frozen files remain byte-for-byte unchanged. The eighth
file is an additive rendering clarification to be read with the candidate.
