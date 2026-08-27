# Research assets and export v12

Preserve papers, source archives, code, datasets, computations, logs, and legacy trees as hash-addressed private objects with provenance and privacy/license metadata. Mathematical computation must retain tool/version, inputs, code, precision, outputs, residual/error checks, reproduction steps, and evidence grade.

Exports are generated artifacts, not alternate projects:

- `intermediate`: human-readable milestone material; allowed before or after completion.
- `final`: allowed only after `project_complete=true`, independent verification, and terminal audit.
- `full-private`: a recoverable private copy containing all objects and state; allowed at any time.

Every export binds the source project head and has its own file manifest. Public export must omit private/unlicensed source bytes and must not strengthen any memory statement.

When an export includes a standalone research result from the v13 research map, export the whole canonical Markdown note. That page must be self-contained: definitions and standing hypotheses may live in a setup section, the bound Obsidian theorem or proposition callout carries the concise core claim, separate corollary and remark callouts carry consequences and limitations, and a complete proof appears under the bound proof heading. Route pages, solver/verifier reports, code, and certificates remain provenance and audit attachments; they cannot replace the page-level mathematical package.

Run `scripts/validate_research_map.py <map-root> --for-result-export` before assembling such an export. Block the result when the note is missing, the expected callout or proof heading is absent, the core statement is empty or a placeholder, the proof is only a sketch or delegated link, or the result is not `verified` or `independently_verified`. Do not reject a correct concise theorem merely because it is short. Structural validation does not replace independent mathematical review.
