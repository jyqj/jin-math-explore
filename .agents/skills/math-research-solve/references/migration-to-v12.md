# Migration to v12

Migration is a read-only prepare followed by a separately authorized atomic commit.

1. Run the source project's original Full Startup and freeze its path, head, lifecycle, objective, counters, evidence, and canonical tree hash.
2. Build a v12 project outside the source directory. Ingest every source byte into the content-addressed object store and bind an imported-tree manifest.
3. Rebuild memory from attempts, verifier reports, checkpoints, route records, and intakes. Re-evaluate every legacy `failure` label under the v12 taxonomy.
4. Preserve unfinished work as a `legacy_resume_capsule`; old Goal/Run bindings do not become current authority.
5. Run one non-counting migration review, preserving cumulative attempt counts and resetting only `attempts_since_route_review`.
6. Require Full Startup v7, old-tree restoration equality, generated-view checks, and an independent migration verifier.
7. Freeze a batch plan. A fresh active Goal is required immediately before the same-volume journaled directory exchange. All projects commit or all sources are restored.

Never rewrite imported proof, verifier, log, ZIP, `.git`, or computation bytes. Renames change only the active directory entry; provenance stays in the imported tree.
