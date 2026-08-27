---
name: math-research-solve
description: Build, continue, verify, map, migrate, and export rigorous long-lived mathematical research with one immutable objective, causal evidence memory, atomic three-attempt windows, independent verification, dual authority/execution heads, and fail-closed completion.
---

## Skill Run Observation

<!-- codex-skill-observer:v2 -->
- As the first execution action after selecting this Skill, run `& $env:CODEX_SKILL_OBSERVER_CLI begin --skill math-research-solve --quiet --fail-open; & $env:CODEX_SKILL_OBSERVER_CLI phase set --skill math-research-solve --phase workflow.startup --quiet --fail-open` when `CODEX_SKILL_OBSERVER_CLI` is available. On POSIX invoke the same executable through the active shell. Do not require PowerShell only for observation.
- At each actual workflow transition, append the matching fail-open `phase set --skill math-research-solve` call to the same shell invocation that starts the next business action. Use only `retrieve`, `verify_live`, `plan_change`, `mutate`, `validate`, `version_control`, and `final_response`; do not add a model-tool round trip only to mark a phase.
- In the final business-tool invocation, set `final_response`; then run `& $env:CODEX_SKILL_OBSERVER_CLI end --skill math-research-solve --status success --quiet --fail-open`. Use `failed` or `cancelled` when known.
- Observation is fail-open and silent: never ask the user to repair it, never expose routine telemetry, and never let observer failure block the Skill.
- Do not pass prompts, file contents, tool inputs, tool outputs, secrets, or personal data to the observer. Also do not pass paths, mathematical content, task content, or raw artifacts. Codex Stop and SessionEnd hooks close interrupted runs.

# Math Research Solve v13

Maintain one exact mathematical objective in one durable project. Product Goal is task authority, never mathematical truth. A finite search, failed attempt, consensus, heuristic, or local obstruction does not settle a wider quantifier without a proved coverage bridge.

New work uses v13. Unmigrated v12 and earlier projects are read-only except through their frozen Startup and the explicit migration Harness. Never mix legacy state rules into an active v13 head.

## Required references

Read only the references needed for the operation, but read each selected reference completely:

- [v13 persistence contract](references/persistence-contract-v13.md) before genesis, any authoritative commit, recovery, or completion publication.
- [v13 state machine](references/state-machine-v13.md) and its [closed transition schemas](references/transition-schemas-v13.md) before planning, activation, checkpoint, closing, verification, reconciliation, maintenance, suspension, or terminal audit.
- [v13 memory and intake](references/project-memory-and-intake-v13.md) before promotion, route review, byproduct classification, or source invalidation.
- [official research map](references/research-map-protocol-v1.md) before map construction, validation, activation, or result export.
- [map semantic review](references/map-semantic-review-v1.md) before preparing, reviewing, repairing, accepting, migrating, or publishing any research map or map receipt.
- [window efficiency preflight](references/window-efficiency-preflight-v13.md) before authoring live-bound window plans, worker outputs, reconciliation/map-review bundles, or `WINDOW_CLOSE` manifests.
- [project cognition](references/project-core-cognition-v13.md) before attempt preparation or context restoration.
- [migration and recovery](references/migration-to-v13.md) before any v12→v13 migration.
- [terminology](references/terminology.md) before introducing or changing a persistent concept.
- Frozen older references only when diagnosing or migrating an unmigrated project. They are not normative for v13.

## Permanent objective and control authority

`objective-core.json` has exactly six ordered fields: `statement`, `domain`, `quantifier_order`, `assumptions`, `evidence_standard`, `completion_standard`. Preserve strings and assumptions order exactly. Encode canonical compact JSON as UTF-8 without BOM, with LF and exactly one final LF. Do not normalize Unicode or strings. Its byte SHA-256 is the permanent `objective_commitment_sha256`; semantic change requires a new project or explicit fork.

<!-- Registry core-invariant match forms are intentionally retained together. -->
`project_objective` means exactly the immutable mathematical objective formed by `statement`, `domain`, `quantifier_order`, `assumptions`, `evidence_standard`, and `completion_standard`. It is not Product Goal, project metadata, a route, a task, a map, or a whole schema.

project_objective means exactly the immutable mathematical objective formed by statement, domain, quantifier_order, assumptions, evidence_standard, and completion_standard.

project_objective means exactly the immutable mathematical objective formed by statement, domain, quantifier_order, assumptions, evidence_standard, and completion_standard. It is not Product Goal, not project.json, not project metadata, and not a route, task, file, or whole project schema. Do not introduce a synonym, rename a canonical term, change its constitutive fields, or reuse a deprecated/reserved term unless [the terminology registry](references/terminology-registry.json), version history, and migration rules are updated first.

Freshly call `get_goal` before genesis, migration exchange, window activation, authoritative publication, pause/handoff, terminal audit, and Goal completion. Scripts accept a Goal-state argument only as a local fail-closed gate and never substitute for the Host call.

## Startup and bounded loading

The active root contains exactly `project.json`, `README.md`, `研究地图/`, and `.research/`. `project.json` is the sole CAS head and points to independent `research_authority_head` and `execution_state_head`. Run:

`python -B scripts/math_research_state_v13.py startup --project <root>`

Continue only on `v13_ready`. For planning, load the objective, both heads, complete memory index, latest route review, map receipt, main map, evidence rules, route landscape, and directly relevant nodes. Retrieve proof bodies, raw objects, and logs only on demand. Never expose archives, full logs, or raw intake bodies to a model unless the bounded task requires the specific bytes.

## Evidence and causal memory

Distinguish `verified_refutation`, `verified_impossibility_boundary`, `bounded_negative`, `unresolved_obstacle`, and `reproduction_blocked`. Only the first two authorize exclusion and only in their verifier-covered scope. External material enters as `external_intake`; preserve provenance and promote claims individually through registered, reproduced, independently verified, and promoted stages.

Memory v2 records method overview, parameter/object definitions, method spine, reusable structures, bottleneck effect, `cannot_imply`, and evidence refs. Unknown migration fields stay explicit; migration may preserve source prose but may not proclaim mathematical equivalence. Route review v2 records only the evidence landscape, comparisons, obstacles, failure boundaries, reopen and reranking conditions. It contains no selected route, `why_now`, or future portfolio and performs no new mathematics.

`review_required` is a gate, not a lifecycle state. Every gate has scope, owning lifecycle, blocked transition, dependency closure, release condition, and evidence refs. A project-level gate prevents false `window_idle` activation eligibility.

## Map and standalone results

The official `math-research-map/v1` is a closed authority view bound to the objective commitment and candidate authority manifest. A closed map has no `route_decision`, selected route, active decision, or next-window plan. Validate with:

- Treat every authoritative map update as a fresh project-wide synthesis, never as append-only catalog maintenance. Reconsider the complete promoted-memory inventory, prior map, latest route review, route archives, and affected evidence; reconstruct the historical development and decisive turns; rewrite the unified mathematical spine; reclassify routes by proof object, mechanism, and quantifier strategy; identify evidence-backed equivalences, similarities, shared obstructions, and cross-route invariants; and explain how the new evidence changes the global situation and remaining frontier. Preserve distinctions and negative knowledge instead of forcing a false unification. The main map must read as a self-contained research survey or textbook chapter from objective to frontier, while node pages and assets provide drill-down evidence.
- Publish `03-术语与记号.md` with every new or rebuilt research map. The main survey must still explain each central symbol and project-local term briefly before first substantive use; the glossary then gives the stable definition, its role in this project, and the nearest likely confusion. A glossary is a reading aid, not permission to write the main survey as unexplained shorthand. The publication Harness checks the glossary file, main-survey link, marker, entry structure, and minimum substance; independent semantic review checks whether the important mathematical notation and route vocabulary are actually covered.
- Preserve every registered `tracked_topic_section` in `01-主研究地图.md`. On each authoritative map update, reread the topic's bound evidence and refresh its **状态**, **进度**, and **排序** against the complete current authority inventory. Here **排序** is an evidence-maturity or map-placement comparison with an explicit basis, never a `route_decision`, selected route, `why_now`, or next-window plan. The publication Harness rejects a missing field, duplicate topic ID, marker outside a level-two section, or marker whose authority-manifest hash is stale; semantic review still decides whether the three values are truthful and globally consistent. See [the tracked-topic protocol](references/research-map-protocol-v1.md#tracked-topic-section-obligation).
- When the user explicitly registers a sufficient-condition or sufficient-proposition topic, also create one hash-bound `terminal_sufficient_condition_register`. Enumerate the non-equivalent terminal propositions, distinguish each proposition from its conjunctive premises, record implication/equivalence/incomparability, give every proposition a difficulty disposition under one named evidence basis, and preserve honest partial orders. Every current research path must be source-audited: each still-expandable branch gets a visible route-local terminal proposition containing its whole remaining closure, while historical/support routes map to that parent proposition and a route may map only to an exclusion when the authority shows it is terminally ineligible without changing route identity. For every new publication, render one hash-bound shared `definition` callout that fixes the topic's reusable objects, notation and standing conventions once; then render every registered proposition as its own descriptively titled `proposition` callout containing the complete route-specific hypotheses and explicit objective conclusion without re-expanding that shared card. The portable unit is the shared definition card plus any selected proposition callouts, matching ordinary mathematical “definitions first, propositions second” practice; a proposition copied without its referenced card is only an internal short form. Prose, a heading, or an external field list never substitutes for either callout. A general criterion or an intermediate success gate never substitutes for the route-local proposition. Criterion-layer propositions require an explicit `criterion_scale` rationale instead of being silently omitted from the difficulty analysis. Give every proposition, exclusion, and source-coverage record its own level-three title before its machine marker. Every visible exclusion and source record must link to a resolvable route page, actual result-or-obstacle evidence page, exact failure-boundary anchor, and terminal-proposition anchor; exclusions additionally name the excluded candidate or intermediate condition, delimit the exclusion scope, and say whether the complete route remains. Never turn a local insufficiency into whole-route exclusion. The structural Harness checks the closed register, definition-card hash, immediate visible placement, callout parity, route/source coverage, links and visible disposition binding; the `frontier`, `cross-route-structure`, and `authority-coverage` semantic checks judge whether the card is sufficient, the short propositions retain every route-specific obligation, linked evidence really supports the disposition, exclusion scope is honest, and the mathematical inventory and ranking remain complete and fair. Read [the terminal sufficient-condition protocol](references/research-map-protocol-v1.md#terminal-sufficient-condition-obligation) before authoring or reviewing such a topic.
- Before publishing any rebuilt or updated map, run the publication synthesis gate defined in [the official research-map protocol](references/research-map-protocol-v1.md). A structural PASS proves only that the required synthesis roles are present and substantive; an independent semantic review must still judge whether the classification, historical account, similarities, and claimed underlying patterns are complete, evidence-backed, and mathematically honest.
- Every new or changed research map is unpublished until the exact candidate has a valid `math-research-map-review-closure/v1`. The Host must dispatch each review with `spawn_agent(fork_turns="none")`; the reviewer must be a fresh principal, different from the author and every earlier reviewer, and may not write or repair the map. `FAIL` or `INCONCLUSIVE` invalidates publication; the author may repair and request a new ticket and fresh reviewer, for at most three rounds in one review cycle. Any map, protocol, inventory, authority manifest, or structural-receipt byte change invalidates every earlier result. Subagent unavailability fails closed: no `single_agent_fallback`, status word, or thin receipt may authorize a map. The closed protocol is normative in [map semantic review](references/map-semantic-review-v1.md).
- `python -B scripts/validate_research_map.py <研究地图> --for-publication`
- `python -B scripts/validate_research_map.py <研究地图> --for-v13-attempt`
- `python -B scripts/validate_research_map.py <研究地图> --for-result-export`

Every standalone result has a visible self-contained Markdown page with definitions, a theorem/proposition callout, full proof, exact scope, source/novelty boundary, relation to objective, reusable value, and `cannot_imply`. Structural validation does not replace independent mathematical review or Obsidian formula/wikilink checking.

## Atomic window lifecycle

Between windows the project is `window_idle`: no active window, queue, attempt, decision, cognition, capsule, or portfolio. A window freezes one validated-map source binding and exactly three distinct semantic fingerprints `(proof_object, mechanism_family, quantifier_strategy)`.

Materialize live-bound artifacts only when their owning phase is current; reusable builder code may be prepared earlier, but hashes, counters, tickets, packets, manifests, and provenance bindings may not. At the cheapest decisive checkpoint, run the source-sufficiency, output-root, package-shape, standalone-proof, map-wide consistency, artifact-class budget, review-digest, and close-manifest gates in [window efficiency preflight](references/window-efficiency-preflight-v13.md). Semantic checks remain reviewer work; deterministic violations must fail before consuming a verifier or map-review round.

1. Prepare planning objects against the expected old project/execution heads.
2. Prepare all three attempt bundles independently. Proposed attempt IDs are not authoritative.
3. If any prepare fails, write no attempt. Atomically activate all three with one `WINDOW_ACTIVATE` execution-head CAS. Superseded IDs are never reused.
4. Each attempt reads only its ticket, frozen cognition/rendering, route decision, and bounded evidence. Siblings do not share unverified output.
5. Checkpoints may update local position/questions only; they cannot change objective, source, cognition, route, semantic fingerprint, or evidence standard. Such change enters `attempt_closing` through semantic reset.
6. Before freezing candidate/outcome and dependencies, run the deterministic [attempt-package preflight](references/attempt-package-preflight-v13.md) in fresh same-volume staging. `ATTEMPT_CLOSE` and every repaired candidate must bind one PASS receipt over the exact final bytes; packaging remediation before freeze is not `LIMITED_REPAIR`. A window stranded with exactly three pre-corrective `verification_queued` attempts may use the one-time atomic `QUEUED_PREFLIGHT_REBIND`; partial, repeated, receipt-bound, repaired or non-queued use fails closed. Then issue fresh verifier tickets, queue independent mathematical verification and permit at most one verifier-directed repair with the identical semantic fingerprint.
7. `ATTEMPT_END` advances only execution state and emits one immutable reconciliation package. It does not promote memory or rebuild the map. Every source-valid bound PASS must carry nonempty `route_delta` or `result_proposals`; derive `promotion_eligible` from those proposals and the PASS instead of a solver recommendation.
8. Reconcile only when exactly three complete packages are present. Reconciliation validates and merges existing evidence; it performs no new mathematics. Conflict propagates at claim, route, or project scope. Failure advances no research authority. If any package is promotion-eligible, an unchanged research authority head is invalid: publish updated memory, route review, and map or fail closed.
9. On success publish memory/review/map and research authority, then close the execution head and clear every active pointer. A later window chooses afresh.

Use `math_research_state_v13.py prepare` for pure transition planning and `math_research_commit_v13.py` for validation/commit. Goal Host may serialize or parallelize workers; agent count never changes lifecycle semantics.

## Cognition and verification isolation

Generate attempt cognition from either `validated_map` or one one-time `genesis_objective`; a migrated project may only use `validated_map`. Cognition carries three independent route decisions and proposed attempt IDs during preparation, and honestly represents an empty verified spine at genesis. Bind every rendering, ticket, and capsule to its attempt-local cognition and source.

Prefer a verifier who did not generate the candidate. When unavailable, use a fresh context-isolated verifier ticket and record `single_agent_fallback`; never claim physical independence. If the objective requires a distinct identity, wait. Source-invalidated packages are never promotable. Late verification enters maintenance and never edits a closed window retroactively.

## Commit, migration, and recovery Harnesses

All authoritative transitions follow prepare → validate → commit. The commit Harness enforces strict JSON, duplicate-key rejection, path traversal/reparse/case-collision checks, full inventory, same-volume staging, named lock, expected-head and plan SHA, immutable objects first, `project.json` last, readback, journal, and conditional rollback. For closing attempts it also independently rehashes the bound attempt-package preflight receipt, manifest, candidate, dependencies, artifact refs and Markdown hash literals before accepting the plan. Candidate objects bind the expected old head and candidate manifest, never the same-generation final head.

Migration runs frozen source Startup, verifies old objective/head, archives both source and map-sample trees byte-for-byte in content-addressed objects, preserves counters/IDs and unfinished work, reconstructs memory/review/map without strengthening evidence, obtains independent review, and performs one journaled same-volume directory exchange after fresh Goal. Query recovery state rather than improvising filesystem repair.

## Maintenance, source integrity, and completion

Suspension/resume, late verification, source invalidation, and maintenance reconciliation are explicit transitions. Invalidation quarantines dependent claims/packages and propagates dependency closure. Coverage failure preserves sound local results; soundness failure quarantines affected authority.

Completion requires one immutable candidate covering all objective quantifiers plus three isolated PASS audits: quantifier/coverage, strategy/soundness, and tool/reproducibility. After freezing the terminal summary and publication plan, fresh-check Goal; only an active matching Goal permits one immutable final authority/execution pair with `project_complete=true` and `pending_goal_update=true`. Read it back, fresh-check Goal again, and call `update_goal(status=complete)`. The final project bytes are permanently closed: never clear the pending flag, publish an acknowledgement into the project, resume research, or rewrite the final head. If Goal completion fails, retry only that same Goal call. Never infer project completion from a partial result or Goal state alone.

## Reporting and privacy

Report only status, counts, IDs, hashes, gates, evidence grades, precise obstacle/failure scopes, limitations, and recovery/reopen conditions. Keep raw archives, object bodies, and complete journals local. Remote/model context is minimized to objective, bound map packet, attempt-local cognition/ticket, and compressed diagnostics.

## Skill Maintenance Note

- Update/rationale note: `AI工具/Math Research Solve/Math Research Solve：让数学研究能够真正接力.md`
