# Attempt-package preflight v13

## Purpose and boundary

`attempt_package_preflight_receipt` separates deterministic byte closure from independent mathematical verification. A solver output directory is non-authoritative raw material. The finalizer copies it into a fresh same-volume staging directory, canonicalizes and closes every package-local reference, generates the manifest, and only then writes the receipt. `ATTEMPT_CLOSE`, `SEMANTIC_RESET`, and every `LIMITED_REPAIR` candidate must bind the PASS receipt before any verifier receives the candidate.

Mechanical finalization before candidate freeze is not `LIMITED_REPAIR` and does not consume an attempt, verification, repair, or authority transition. The receipt proves only package closure. It cannot establish source fidelity, proof correctness, scope, quantifier coverage, evidence grade, verifier independence, promotion eligibility, or project completion.

## Deterministic order

1. Preserve the raw solver directory and require a new absent staging destination.
2. Reject reparse points, non-regular items, path traversal and case collisions.
3. Parse JSON with duplicate-key rejection and build package-local `path`/`sha256` dependencies.
4. Reject self-reference and every dependency cycle. Finalize referenced leaves before their referrers.
5. Canonicalize each JSON object once after its dependencies are final; replace package-local `sha256` and existing `bytes`/`size` fields from the final target bytes.
6. Check every Markdown SHA-256 literal against a finalized package file. Prefer artifact IDs and relative paths in human prose; stale or unexplained literals fail closed.
7. Generate `artifact-manifest.json` over every content file, excluding the manifest and receipt themselves.
8. Generate the manifest, then compute the package inventory including that manifest but excluding the receipt.
9. Generate `attempt-package-preflight.json` last. The receipt is excluded from its own inventory and binds its maximum total-byte budget; the checker includes the actual receipt bytes when enforcing that budget.
10. Independently reread and validate the final directory. Any later byte change invalidates the inventory or pointer binding.

Neither the manifest nor any content file may reference the receipt. Content files may not reference the manifest. The directed hash graph therefore has no same-generation reverse edge.

## Receipt schema

`math-research-attempt-package-preflight/v1` has exactly:

- `schema, attempt_id, status, package_root, candidate, dependencies`;
- `artifact_refs_sha256, package_inventory_sha256, artifact_manifest`;
- `file_count_excluding_receipt, total_bytes_excluding_receipt, max_total_bytes, finalizer_version`.

`status` is exactly `PASS`. `package_root` is a POSIX-relative immutable package directory in the project. `candidate` is null or one exact pointer. `dependencies` is the ordered closing dependency pointer list. `artifact_refs_sha256` binds the ordered closing artifact refs excluding the receipt itself. `package_inventory_sha256` binds canonical rows `path,size,sha256` for every package file except the receipt. The manifest pointer must occur in the closing artifact refs.

The transition planner checks the required receipt pointer structurally. The commit Harness resolves both staged and already committed targets, verifies every pointer against exact bytes, reconstructs the complete package directory, and reruns the independent checker. A receipt generated for another attempt, candidate, dependency order, artifact list, inventory, package prefix or byte budget fails closed.

## Commands

Create fresh finalized staging:

```powershell
python -B scripts/finalize_attempt_package_v13.py --source <raw-dir> --staging <fresh-dir> --attempt-id <id> --package-root <project-relative-prefix> --candidate-path <package-relative-file> --dependency-path <package-relative-file> --project-root <project>
```

Independently reread it:

```powershell
python -B scripts/validate_attempt_package_v13.py --package <fresh-dir> --project-root <project>
```

The finalizer emits the exact `candidate`, `dependencies`, and `artifact_refs` pointers to copy into the closing payload. External dependencies or artifacts use explicit `PROJECT/PATH=SHA256` arguments and require `--project-root` so the finalizer can verify the referenced bytes.

## Compatibility and recovery

This corrective rule does not rewrite existing project objects or closed attempts. An idle v13 project uses it for every future attempt. An attempt already executing when the corrected Harness is installed must finalize its still-raw output and bind a new receipt before its first closing commit; no counter or repair moves during that preparation. An attempt already in closing under the older validator must return to non-authoritative package staging and produce the receipt before `VERIFICATION_QUEUE` or `ATTEMPT_END`; the mathematical candidate and semantic fingerprint remain unchanged.

If one active window was already atomically committed with exactly three attempts in `verification_queued` before this corrective rule was installed, use the public one-time `QUEUED_PREFLIGHT_REBIND` transition. First finalize and independently validate all three packages. Then one closed payload must bind the current execution head, all three old candidate/dependency/verifier-ticket lineages, all frozen semantics, and all three new candidate/dependency/artifact closures. The transition returns all three attempts to `closing`, removes all three stale verifier queue items, and preserves counters and repair counts. Commit must stage all three package roots together so the commit Harness can validate every receipt against the candidate execution head. Issue three fresh verifier tickets afterward.

The compatibility transition refuses a subset, a second invocation, any already receipt-bound attempt, any prior repair, any verification result, any package-ready attempt, a changed frozen semantic field, a stale head, or a window with other than the exact three legacy queue items. It does not rewrite prior objects, infer mathematical validity, reuse old verifier tickets, or consume `LIMITED_REPAIR`.

Do not install the corrected Harness while another live controller may load production scripts from disk unless that controller is already prepared to supply the new receipt and `LIMITED_REPAIR.new_artifact_refs`. Prefer an idle-window installation boundary. A missing raw package or unreconstructable dependency is a mechanical close blocker, not verifier evidence and not a mathematical failure.
