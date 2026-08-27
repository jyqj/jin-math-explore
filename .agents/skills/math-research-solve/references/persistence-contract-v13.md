# Persistence contract v13

## Canonical objective

`.research/identity/objective-core.json` contains exactly six ordered fields: `statement`, `domain`, `quantifier_order`, `assumptions`, `evidence_standard`, and `completion_standard`. Encode compact JSON in UTF-8 without BOM or CRLF, preserve non-ASCII and every string byte without normalization, preserve assumptions order, and end with one LF. Its SHA-256 is the permanent objective commitment. Metadata, paths, Runs, maps, and schema migrations cannot change it; changing any of the six field bytes creates a different commitment.

## Sole CAS head and hash graph

`project.json` is canonical compact JSON and the only project CAS head. It preserves stable project ID and original creation time and points to the objective, a research-authority head, and an execution-state head. Research authority owns promoted memory, route review, map and source integrity. Execution state owns windows, attempts, queues, verification, closing, suspension and audit. Execution-only commits never advance research authority.

The hash graph is directed. Candidate objects and manifests bind the expected old project/head hashes. A final head may point to them; no candidate may point back to the same-generation final head. This prevents circular hash definitions.

## Commit protocol

Every mutation is prepare → validate → commit. Preparation is non-authoritative and may use proposed IDs. Validation checks strict JSON including duplicate keys; bounded POSIX-relative paths; traversal, symlink/reparse and case collisions; complete staging inventory; same volume; expected head and plan SHA; closed schemas and dependency hashes. Commit obtains a named lock, writes immutable objects first, replaces `project.json` last, reads every byte back, appends a journal, and conditionally restores only writes applied by that plan.

An identical-hash retry is idempotent. Any different candidate after CAS failure requires a new prepare and plan. A script's Goal-state flag is only a local gate; the Host must fresh-check Goal before authority changes.

## Completion publication pair

After all three terminal audits pass on the same immutable candidate, freeze the terminal summary and completion plan and fresh-check the matching Goal. Only while it remains active may the Host publish one permanently closed head with `project_complete=true`, the terminal receipt, and `pending_goal_update=true`. Read back that head, fresh-check Goal again, then call `update_goal(status=complete)`. The project bytes never change again: `pending_goal_update` is a durable record of the required control-plane action, not a mutable queue bit. If Goal completion fails, retry only the same Goal call; never clear the flag, write an acknowledgement, rerun mathematics, change the candidate, or reopen the final head.
