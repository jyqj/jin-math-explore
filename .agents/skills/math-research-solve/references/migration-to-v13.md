# Migration and recovery v12 → v13

## Corrective v13 contract migration

The corrective v13 release does not rewrite a valid idle project. Startup validates the complete execution-head field set and current validated-map binding before new planning. A pre-corrective active v13 head that lacks closed prepare, activation, closing, verification, or reconciliation bindings is fail-closed: preserve its bytes, create an owner-scoped maintenance gate, and recover or close it from frozen evidence rather than synthesizing missing records. A migrated project still never enters genesis.

The terminal contract is narrowed without a project rewrite. Any already published `project_complete=true, pending_goal_update=true` head is permanently immutable; never apply the obsolete post-final acknowledgement or clear-pending wording. Retry only the same product Goal completion call. An incomplete project continues after Startup and receives no new head merely because this Skill revision was installed.

Migration is an external whole-directory transaction, never an in-place schema edit.

The reusable Skill contains only the common, hash-pinned adapter launcher. Project-specific memory transforms, route names, thresholds, constants, and map content live in a separately reviewed project-local adapter outside the Skill. Invoke `scripts/math_research_migrate_v12_to_v13.py` with the absolute adapter path and its exact SHA-256; any adapter-byte change invalidates review and requires a new transaction.

1. Run the source project's frozen Full Startup. Freeze project head, old objective hash, complete byte inventory, counters, active work and object-store integrity. Missing time/tool/cost fields remain `unknown`.
2. Build on the same volume outside the project. Content-address every source and map-input byte and write imported-tree manifests. Preserve project ID, original creation time, counters, memory IDs, evidence grades and unfinished work. Never fabricate an attempt or reduce a counter.
3. Extract the six objective fields without normalization and create the permanent commitment. Record the old objective hash as source identity; it need not equal the new six-field byte commitment.
4. Rebuild memory v2 and route review v2 only from preserved evidence. Migration may move or quote fields; it may not announce mathematical equivalence, strengthen scope/evidence, create missing proof objects, or infer route causality. Unresolved gaps create owner=`migration` scoped gates.
5. Build the official map from bound authority. Remove route decision, selected route and future commands. Freeze the complete migration-source and candidate-authority inventories, then run [map semantic review v1](map-semantic-review-v1.md): structural validation first, followed by a fresh `spawn_agent(fork_turns="none")` reviewer distinct from the migration author. `FAIL` or `INCONCLUSIVE` may be repaired by the author only through a new candidate/ticket/reviewer, for at most three rounds. Only a final exact-candidate `math-research-map-review-closure/v1` is accepted; no caller-supplied checklist, PASS word, nonempty pointer, or `single_agent_fallback` can complete migration.
6. Validate exact four-root layout, strict JSON, dual heads, archives, imported-tree recovery, 17/17 IDs or the source-specific expected count, map assets, result export, counters and Full Startup. A migrated project never uses genesis.
7. Fresh-check Goal. Obtain a named lock and journal, then exchange the whole staged directory with the source in one same-volume transaction. Move the original map-input tree into the same recovery transaction so there is one visible official map. On any partial failure, restore only the paths moved by this transaction.
8. Read back the new head and archives. Keep recovery queryable until retention policy explicitly retires it. Do not improvise manual deletion or repair.

An eligible migrated idle head is incomplete, has no pending Goal update, active window, attempt, queue, decision, cognition, capsule or portfolio, and has a current map plus zero project-level gates. If any gate remains, the execution head must truthfully expose maintenance/review ownership rather than masquerading as activation-eligible idle.

An older already-migrated incomplete idle project with only a thin semantic-review receipt remains byte-preserved and readable, but Startup reports `map_review_upgrade_required` and blocks `WINDOW_PLAN` until a maintenance review publishes a valid closure. A window already activated from its frozen source may finish without retroactive rewriting; its next map publication must use the closure. A completed project is immutable and is never upgraded in place.
