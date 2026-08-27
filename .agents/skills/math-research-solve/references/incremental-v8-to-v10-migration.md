# Nonterminal v8 to v10 incremental migration

Use this protocol only when the user explicitly asks to upgrade a live, nonterminal
`math-research-project/v8` archive.  It is a schema upgrade, not a new mathematical
attempt.  It consumes no attempt, audit, or total-round count.

## Invariants

- Never rewrite the v8 `project.json`, generation files, tickets, evidence, route
  closures, audit records, or asset package.  The v10 project is a separate sibling
  directory with the same `project_id` and a fresh `run_id`.
- Inherit cumulative counters exactly.  The v10 run-local counters begin at zero and
  its budgets are the v8 frozen ceilings minus the cumulative counts.  Migration
  never refreshes a budget.
- Hash every regular predecessor file.  The migration manifest keeps a complete
  byte inventory plus machine indexes for attempts, audits, routes, evidence,
  assets, staging, and unreferenced recovery candidates.  Recovery candidates are
  preserved but never promoted into current mathematical evidence.
- Copy and validate the current asset-index closure without changing its bytes.
  The v10 state points to that inherited index from generation 1.
- Freeze before commit.  The exact staged `math-research-v8-freeze/v10` record is
  installed create-new as `state/migration-freeze-v10.json` in v8 before the v10
  plan is committed.  Official v8 startup then returns `v8_migrated_frozen`, and
  the v8 head publisher refuses every later commit.
- A freeze is fail-closed and recoverable.  If v10 publication is interrupted after
  the marker is written, preserve the exact plan and retry it; do not delete or
  rewrite the marker and do not resume v8.
- Every migrated v10 `ATTEMPT_START` independently reopens the sibling v8 marker,
  checks its hash against the internal freeze record, and checks that the v8 head
  still equals the migrated head.  A missing/moved/changed predecessor blocks the
  attempt before counters change.

## Host sequence

1. Run Startup v5 `Full` on v8 and perform a fresh Goal check.  Migration requires
   the current Goal to authorize the same target and the schema upgrade; helpers do
   not own or query Goal state.
2. Run `inspect` and freeze the reported head, counters, remaining budgets, envelope
   hashes, current lifecycle, and asset index into the bootstrap.
3. Prepare a v10 bootstrap containing exactly one new planned ticket, capsule, route
   card, and the explicit predecessor files that ticket needs.  The new route must
   respect every inherited route closure and reopen condition.
4. Run `prepare` in an empty temporary staging directory.  Review its plan hash,
   predecessor head, candidate head, inherited counters/budgets, asset pointer,
   inventory count, and recovery-candidate count.
5. Freshly check Goal again, then run `freeze`.  Read back Startup v5 on v8 and
   require `v8_migrated_frozen`.  If the v8 head changed, discard the uncommitted
   plan and restart inspection; never force the marker.
6. Freshly check Goal again, commit the exact v10 transition plan with the ordinary
   v10 commit helper, and run Startup v5 `Full` on the successor.
7. Run `verify`.  Require the original v8 head hash, freeze hash, exact v10 candidate
   head hash, cumulative counters, remaining budgets, asset index, and full-manifest
   audit to match.  Then perform the real consumer-principal recursive readback.
8. Only after all checks pass may the v10 planned ticket enter the ordinary
   round-trip topology preflight and `ATTEMPT_START`.

The two project directories form one migration boundary.  They must be plain,
non-reparse siblings.  Use one controlled process rooted at their canonical parent
for read-only planning, or separate exact-root processes for the v8 freeze and v10
publication.  Generic elevation is not a substitute for a proven readable/writable
topology.

## Entrypoints

Windows:

```powershell
scripts/invoke_math_research_migrate_v8_to_v10.ps1 -Action inspect -PredecessorProject OLD
scripts/invoke_math_research_migrate_v8_to_v10.ps1 -Action prepare -PredecessorProject OLD -SuccessorProject NEW -Bootstrap BOOTSTRAP -Output STAGE
scripts/invoke_math_research_migrate_v8_to_v10.ps1 -Action freeze -PredecessorProject OLD -Plan PLAN
scripts/invoke_math_research_migrate_v8_to_v10.ps1 -Action verify -PredecessorProject OLD -SuccessorProject NEW -Plan PLAN
```

Linux/macOS:

```sh
sh scripts/math_research.sh migrate-v8-to-v10 inspect --predecessor OLD
sh scripts/math_research.sh migrate-v8-to-v10 prepare --predecessor OLD --successor NEW --bootstrap BOOTSTRAP --output STAGE
sh scripts/math_research.sh migrate-v8-to-v10 freeze --predecessor OLD --plan PLAN
sh scripts/math_research.sh migrate-v8-to-v10 verify --predecessor OLD --successor NEW --plan PLAN
```

## Fail-closed codes

`predecessor_not_v8`, `v8_head_invalid`, `v8_contract_hash_mismatch`,
`migration_reparse_forbidden`, `migration_path_invalid`, `successor_exists`,
`stage_not_empty`, `migration_input_hash_mismatch`, `migration_target_collision`,
`cas_conflict`, `freeze_conflict`, `freeze_readback_failed`,
`v8_migrated_frozen`, `predecessor_not_frozen`,
`predecessor_changed_after_migration`, and `successor_not_committed` are operational
failures.  Before `ATTEMPT_START` they do not consume research counters and must not
be recorded as a negative mathematical route result.
