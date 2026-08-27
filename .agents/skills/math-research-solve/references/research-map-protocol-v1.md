# Research map protocol v1

`math-research-map/v1` is the first official research-map format introduced by the v13 project architecture. These are two different version axes: `v13` names the whole `math-research-solve` architecture; `v1` names only the research-map component. Earlier files labelled `math-research-map/v2`, `/v3`, or `/v4` were pre-standardization internal prototypes. Keep their validators only for read-only recovery; do not describe those numbers as Skill or project versions, and do not use those prototypes to activate a v13 attempt.

The research map is a bounded reading and navigation layer. It gives a first-time human or agent the project-wide causal picture without loading the full archive. It never replaces authoritative memory, evidence, route review, or the immutable project objective.

## Global synthesis obligation

Every authoritative map construction, reconciliation rebuild, maintenance rebuild, or other map update is a fresh global synthesis pass. Never implement it by appending a latest-results section, adding a few links, or preserving the old taxonomy without reconsideration. The updated map must be able to teach a first-time reader how the problem, objects, methods, evidence, failures, route changes, and present frontier fit together as one developing research program.

Before drafting, inspect the complete authoritative inventory: the objective, complete promoted-memory index, latest route review, every existing map node, route-local conclusions needed to explain the history, and every newly affected evidence record. This is an inventory-coverage requirement, not permission to load every raw body at once. Use bounded retrieval and hashes/pointers to identify the complete set, then open only the sections needed to reconstruct and verify the synthesis.

Rebuild `01-主研究地图.md` as continuous explanatory prose organized around mathematical causality rather than file chronology. It must perform all of these reasoning operations afresh:

1. Place the immutable objective in its mathematical and project-historical context, and define the central objects and exact terminal gap.
2. Present one unified method spine showing how constructions, identities, recurrences, arithmetic control, asymptotics, and the terminal criterion depend on one another; adapt the layers to the actual subject rather than copying this example mechanically.
3. Reconstruct the research history through decisive evidence and turning points: explain why a route was opened, redirected, split, merged, paused, or closed, and what changed the project's beliefs.
4. Reclassify the whole route landscape from the current evidence. Compare proof objects, mechanism families, quantifier strategies, dependencies, success gates, and failure scopes. Identify routes that are equivalent, specializations, dual formulations, shared subproblems, or only superficially similar. Preserve distinctions whenever equivalence is unproved.
5. Search across routes for reusable structures, recurring obstructions, conserved quantities, common reductions, dualities, monotonicity, valuation patterns, asymptotic regimes, or other underlying regularities. Label a newly inferred pattern as an inference or `review_required`; do not manufacture a theorem or upgrade its evidence grade inside the map.
6. State the current global situation after integrating all authoritative assets: what is proved, what is bounded evidence, what has been ruled out in an exact scope, what remains unknown, which bottleneck is now central, and how the latest evidence changed the overall assessment.
7. Reconstruct the frontier as missing logical bridges and coverage gaps, not as a command selecting the next route. Explain which gaps are shared across routes and which are route-specific.
8. Account for the complete authoritative inventory. Explain which bodies of work were absorbed into the synthesis, which remain route-local or archival, and why an omitted item does not alter the global account. An asset index is supporting audit material, not a substitute for this integration.

The main survey is the first reading path, so define every central symbol, parameter, named construction, project-local abbreviation, and nonstandard foreign term before its first substantive use. Give enough information to identify the mathematical object, understand why it appears, and see which proof obligation it serves. A later glossary entry does not excuse unexplained first use.

Place exactly one invisible role marker inside the corresponding level-two section of `01-主研究地图.md`; section titles remain free to use natural mathematical Chinese or another project language:

```markdown
<!-- research-map-synthesis:objective-context -->
<!-- research-map-synthesis:unified-method-spine -->
<!-- research-map-synthesis:historical-development -->
<!-- research-map-synthesis:route-genealogy -->
<!-- research-map-synthesis:cross-route-structure -->
<!-- research-map-synthesis:global-state -->
<!-- research-map-synthesis:frontier -->
<!-- research-map-synthesis:authority-coverage -->
```

Run `python -B scripts/validate_research_map.py <map-root> --for-publication` before issuing or accepting any new map validation receipt. The gate rejects a missing main survey, a missing or duplicated role, a marker outside a level-two section, placeholder prose, a materially empty role, or a main survey too small to carry the required synthesis. This structural gate deliberately does not judge whether a proposed equivalence is mathematically true, whether the historical narrative is fair, whether every important asset was actually understood, or whether the prose is genuinely deep. Independent semantic review must answer those questions against the complete inventory and record unresolved synthesis gaps as `review_required`; a structural PASS never closes this residual semantic gap.

The independent gate is the closed [map semantic review v1](map-semantic-review-v1.md). Freeze the complete authority inventory and exact candidate before dispatch. Each round uses a `spawn_agent(fork_turns="none")` reviewer who is neither the author nor an earlier reviewer and who cannot edit the map. `FAIL` or `INCONCLUSIVE` requires author-side repair or bounded evidence augmentation, new hashes, a new ticket, and a new reviewer. At most three rounds belong to one cycle. Only a `math-research-map-review-closure/v1` whose final PASS binds the exact candidate may serve as `semantic_review_receipt`; subagent unavailability and every fallback mode fail closed.

## Project glossary obligation

Every newly published or rebuilt official map contains `03-术语与记号.md` at the map root. Put exactly one `<!-- research-map-glossary:v1 -->` marker in that note and link it from `01-主研究地图.md` with an Obsidian wikilink. The glossary is project-specific: it explains the notation and technical language needed to read this research program, rather than copying a general mathematics dictionary.

Use one level-three heading per entry. Every entry contains all three fields:

```markdown
### $K$

- **定义：** 这个符号指什么对象，量词和取值范围是什么。
- **在本项目中的作用：** 它进入哪一步证明，为什么读者需要它。
- **不要混淆：** 它最容易与哪个相近符号、普通词义或证据状态混淆。
```

Add `首次出现` or a drill-down link when useful, but do not replace the three required fields with a bare cross-reference. Include at least the immutable objective's central notation, construction parameters, sequence indices, proof-object labels, route-local abbreviations, evidence/status terms that appear in mathematical prose, and foreign terms without a stable or already established Chinese equivalent. Prefer accepted Chinese terminology; retain an exact foreign term when translation would be misleading, and explain it on first use.

The publication Harness checks that the file exists, the marker appears exactly once, the main survey links to it, at least six substantive entries exist, and every entry carries the three required fields. It cannot determine whether the chosen entries cover all terms that would stop a first-time reader. Independent semantic review must therefore perform a terminology-coverage pass against the main survey, route landscape, milestones and visible results. Missing central terms are a publication failure or `review_required`, not a stylistic suggestion.

Already published v1 maps without a glossary remain readable and may remain frozen window sources. The glossary gate applies to new publication receipts; it does not retroactively rewrite closed history or invalidate a previously frozen window.

An already published v1 map remains readable and may remain a frozen source for its bound window. The strengthened publication gate applies whenever new map bytes or a new map receipt are proposed. Do not retroactively rewrite closed project history merely to add markers.

## Tracked topic section obligation

A project may register a `tracked_topic_section` when the user wants one named topic to remain visible across every future authoritative map update. The section lives in `01-主研究地图.md` under a level-two heading and contains exactly one marker of this form:

```markdown
<!-- research-map-tracked-topic:v1 {"topic_id":"stable-project-local-id","authority_manifest_sha256":"64-lowercase-hex"} -->
```

The marker registers a durable publication obligation, not a mathematical result or new lifecycle state. `topic_id` is unique inside the map and stable across later publications. `authority_manifest_sha256` equals the exact candidate map control's `authority_manifest_sha256`; this forces every new authority publication to revisit the section instead of carrying a silently stale marker.

Every registered section contains these three substantive fields:

```markdown
- **状态：** 当前证据等级、开放／受阻／封闭范围，以及不能推出什么。
- **进度：** 已闭合的逻辑桥、剩余缺口和最新证据对全局的改变。
- **排序：** 它在当前地图或证据成熟度比较中的相对位置，并明示排序依据。
```

At every map construction, reconciliation rebuild, maintenance rebuild, or other map update, inventory all registered topic IDs before drafting. For each topic, reread the complete affected authority slice, reconsider the three fields, update the manifest binding, and place the section where the current synthesis makes it easiest to understand. Do not preserve a prior status, progress statement, or order merely because no new file has the same topic name. A topic with no new mathematical evidence still needs an explicit current disposition such as provenance-only, exact duplicate, unchanged evidence boundary, or archival.

The **排序** field is descriptive, evidence-backed navigation. It may compare proof maturity, number and kind of missing logical bridges, scope closure, or map prominence. It must name its comparison basis and preserve incomparability when the evidence does not support a total order. It never carries `selected route`, `why_now`, a success probability, an active decision, or a next-window portfolio; those remain attempt-local execution authority.

`scripts/research_map_v1.py` checks marker syntax, unique topic IDs, level-two containment, all three substantive fields, and the exact authority-manifest binding. A structural PASS cannot prove that the stated status, progress, or ordering is mathematically fair. The fresh-subagent semantic reviewer must therefore compare every registered topic section with the complete authority inventory and fail publication when a field is stale, unsupported, overstated, or inconsistent with the global synthesis.

## Terminal sufficient-condition obligation

When the user explicitly asks a tracked topic to maintain sufficient conditions or sufficient propositions, register one `terminal_sufficient_condition_register`. This is a specialization of `tracked_topic_section`, not a requirement for unrelated topics. Put the ordinary `research-map-tracked-topic:v1` marker somewhere in the main survey and place exactly one additional marker inside the level-two section that visibly explains the sufficient-condition analysis:

```markdown
<!-- research-map-sufficient-condition-topic:v1 {"topic_id":"stable-project-local-id","authority_manifest_sha256":"64-lowercase-hex","register_path":".research/sufficient-conditions/stable-project-local-id.json","register_sha256":"64-lowercase-hex"} -->
```

The register path is fixed by `topic_id`. Its canonical compact UTF-8 JSON uses schema `math-research-sufficient-condition-register/v1` and exactly the root fields `schema, topic_id, project_id, project_objective_sha256, authority_manifest_sha256, coverage_claim, difficulty_basis, conditions, logical_relations, difficulty_relations, exclusions, candidate_source_coverage`. It binds the same objective and authority manifest as the candidate map.

Each `conditions` row has exactly `condition_id, statement, objective_implication, terminality, kind, closed_prerequisites, open_obligations, route_ids, evidence_refs, difficulty_disposition`:

- `condition_id` and exclusion `candidate_id` are stable ASCII alphanumeric/hyphen identifiers; case is significant so an established project-local label remains exact.

- `terminality` is `direct` when the proposition itself implies the project objective, or `via_registered_condition` when a registered implication path reaches a direct proposition. A premise that must be conjoined with other unregistered premises is not terminal.
- `kind` is `criterion` for an upper-level criterion or `actionable` for a concrete research program. A criterion uses `difficulty_disposition.status=criterion_scale`; an actionable proposition uses `ranked`. Both require a substantive rationale, so criterion nodes cannot disappear from the difficulty analysis.
- `closed_prerequisites` and `open_obligations` describe the proposition's own proof burden. `route_ids` may be empty only when the proposition is genuinely route-independent. Evidence references retain their ordinary authority grades.

Every still-expandable research branch gets at least one `kind=actionable` route-local condition. Its statement conjoins the remaining bridges needed for that branch to reach a direct criterion; a general criterion, route maturity sentence, or intermediate route success gate cannot replace it. Historical or support routes may share their parent branch condition by appearing in that condition's `route_ids`. Map a route only to an exclusion when the authority establishes that completing the route under its current mathematical identity still cannot reach the objective; a merely incomplete route is not terminally ineligible.

`logical_relations` rows have exactly `source_id, relation, target_id, rationale, evidence_refs`, where `relation` is `implies`, `equivalent_to`, or `incomparable_with`. `difficulty_relations` rows have exactly `source_id, relation, target_id, basis, evidence_refs`, where `relation` is `easier_than`, `harder_than`, or `incomparable_with`. Difficulty applies only to actionable propositions, uses the one named `difficulty_basis`, preserves partial orders, and never means success probability or route selection. Every actionable proposition in a multi-proposition register must occur in at least one difficulty relation. Directed implication and difficulty cycles fail publication.

`exclusions` rows have exactly `candidate_id, description, exclusion_reason, evidence_refs`. Use them for local lemmas, individual premises, source recovery, one contour identity, raw decay, finite computation, or any other object that does not by itself close a registered implication path to the objective. An empty list is allowed only when the authority inventory supports no material near-miss requiring clarification.

`candidate_source_coverage` is the fail-closed source-by-source audit that prevents a terminal proposition in a route review or success gate from being compressed into a broader criterion and disappearing. Each row has exactly `source_id, source_kind, candidate_summary, disposition, target_ids, route_ids, evidence_refs, rationale`. `source_kind` is `route_success_gate`, `route_review`, `authority_claim`, or `visible_map_claim`; `disposition` is `condition`, `equivalent_to_condition`, or `exclusion`. Every route record in the candidate map must occur in at least one row. A route review or success-gate row mapped to a condition must target an actionable condition carrying that same route ID. Every material candidate in one source gets its own row even when several candidates share a route or source document. Structural validation proves that declared rows resolve and cover routes; the semantic reviewer still compares the ledger with the complete route-review, route-record, visible-map and authority inventories to detect omitted rows.

Every new publication of a registered sufficient-condition topic contains exactly one shared definition card immediately after the topic marker:

```markdown
<!-- research-map-sufficient-condition-definitions:v1 {"topic_id":"stable-project-local-id","definition_id":"stable-definition-id","definition_sha256":"64-lowercase-hex"} -->
> [!definition] Descriptive shared notation title
> Define the reusable objects, notation, quantifier domains, orientations, branches, normalizations and standing conventions used by the propositions below.
```

The card contains only shared constitutive definitions and conventions; route-specific open hypotheses remain inside the corresponding proposition. `definition_sha256` is SHA-256 of UTF-8 bytes formed by the whitespace-normalized visible callout title, one LF, the visible body after removing the Markdown quote prefix from each line and trimming its outer whitespace, and one final LF. Hidden HTML or Obsidian comments are forbidden. The marker and callout must be immediate, uniquely present, visibly substantive and hash-matched. A previously published map without this card remains readable as legacy map history, but its next publication must add the card and obtain a fresh structural receipt and semantic-review closure.

The visible level-two section contains substantive `充分命题清单`, `逻辑关系`, `难度排序`, `排除项`, and `来源覆盖` fields. Each visible record owns one immediately preceding level-three title; put its marker after that title, never at the end of the preceding record. A proposition title begins with its exact condition ID, an exclusion title is exactly `排除：<candidate_id>`, and a source title is exactly `来源：<source_id>`. Bind every visible proposition with `<!-- research-map-sufficient-condition-entry:v1 {"condition_id":"..."} -->`, every visible exclusion with `<!-- research-map-sufficient-condition-exclusion:v1 {"candidate_id":"..."} -->`, and every source-candidate row with `<!-- research-map-sufficient-condition-source:v1 {"source_id":"..."} -->`; the visible IDs must equal the register exactly.

Immediately after each proposition marker, with no heading or prose in between, render exactly one `> [!proposition] <descriptive title>` callout. The callout itself, not surrounding bullets, HTML comments, or Obsidian `%%...%%` comments, must visibly contain the register's complete route-specific hypothesis statement and objective implication and write the final objective conclusion explicitly. It may use objects and symbols fixed by the shared definition card instead of re-expanding them. The self-contained portable unit is that hash-bound card plus one or more selected proposition callouts; if only the proposition is copied, label it as an internal short form rather than pretending it is context-free. Put closed prerequisites, open obligations, evidence, route IDs, and difficulty commentary after the callout. Group route-local propositions by path or show their route IDs so a reader can start a future branch directly from the map.

Every exclusion visibly supplies the fields `被排除候选`, `排除范围`, `路线保留`, `路线`, `证据`, `失败边界`, and `对应终端命题`. `被排除候选` names its exact `candidate_id`; `排除范围` says which candidate or intermediate condition fails rather than asserting that the whole route fails; `路线保留` begins with an explicit yes/no and explains whether the complete route remains available. Every source-coverage record visibly supplies `路线`, `证据`, `失败边界`, `对应终端命题`, and `登记处置`; the last field must reproduce its register disposition and target IDs. The four link fields use parseable Obsidian wikilinks. Route links resolve to route-explanation notes, evidence links to actual result or obstacle notes, failure-boundary links include an existing heading or block anchor, and terminal-proposition links include the exact proposition-heading anchor. A missing or ambiguous target, missing anchor, route page that does not name the declared route ID, or visible disposition/terminal link inconsistent with the register fails publication.

The Harness fail-closes a missing or placeholder title, misplaced marker, non-immediate callout, hidden-comment payload, statement/implication mismatch, missing or stale definition card, incomplete definition-plus-proposition package, missing link field, dangling proposition link, unresolved or ambiguous link, missing anchor, missing exclusion scope or route-retention declaration, and visible disposition mismatch. It permits short descriptive Chinese titles and leaves mathematical title accuracy, definition sufficiency, truth of linked support, and honesty of exclusion scope to semantic review. These structural checks prove declared parity, not mathematical terminality, portable-unit self-containment, source completeness, or fair ranking; semantic review remains mandatory.

For an update, pass the prior official map root to `validate_research_map.py --for-publication --previous-map-root <prior-map-root>`. The downgrade gate rejects removal of a previously registered sufficient-condition topic. Genesis has no prior root. Existing ordinary tracked-topic v1 sections remain compatible and need no register unless the user explicitly adds this obligation.

The fresh-subagent semantic reviewer receives the exact register and bounded linked-evidence summaries as a minimized candidate document. Under `frontier`, verify that the inventory is complete, every row is terminal under its declared path, conjunctive premises are not counted as separate terminal propositions, every expandable route has a usable route-local terminal proposition, and each exclusion honestly identifies a local candidate or intermediate condition without silently excluding a viable whole route. Under `cross-route-structure`, verify implication/equivalence/incomparability and the evidence basis for the difficulty partial order. Under `authority-coverage`, compare every route review, route success gate, authority claim and visible candidate with `candidate_source_coverage`; follow the declared route/evidence/failure/proposition links, fail when evidence does not support the disposition or boundary, and fail when a narrower or intermediate terminal proposition was silently absorbed into a broader criterion. Structural validation cannot prove these mathematical judgments.

## Visible directory layout

Keep the map root as a small reading entrance. Store typed research assets in fixed category folders:

```text
map-root/
├─ 00-研究地图契约.md
├─ 01-主研究地图.md
├─ 02-阅读说明与证据规则.md
├─ 03-术语与记号.md
├─ 40-路线景观与重排条件.md
├─ 90-资产索引.md
├─ 里程碑/
├─ 研究成果/
├─ 路线/
├─ 实验/
├─ 桥梁/
└─ .research/
```

The five category folders are semantic containers, not new node types or version axes. A folder may be absent until it has a node. Inside a category folder, use the mathematical subject as the filename; do not repeat the category prefix merely to simulate grouping. Numeric prefixes remain optional ordering aids for the small set of root entrance notes, not authority or lifecycle state.

When migrating an existing flat map, prepare all destination paths first, then move same-category notes, rewrite every relative wikilink and machine-controlled path, validate the complete staged tree, and publish the tree as one guarded change. Do not leave compatibility duplicates at the old paths: duplicate visible notes create two apparent authorities. Preserve old bytes in the project object archive when archival recovery is required.

The official validator rejects result notes outside `研究成果/` and recognizes flat root filenames such as `研究成果-*`, `*-里程碑-*`, `*-路线-*`, `*-实验-*`, and `*-桥梁-*` as layout debt. Such a map remains readable for migration, but it cannot pass current v13 activation or result export until the paths are grouped and rebound. This layout rule does not change `math-research-map/v1` because it constrains the visible file organization, not the machine control schema.

## What belongs in the map

The map separates four things that must not be conflated.

- A **milestone** is a verified conclusion that changed the global project situation: it moved the best known bound, changed the central bottleneck, opened or closed a route class, or altered route ordering.
- A **standalone research result** is a rigorous and reusable mathematical result that remains worth knowing even if it did not change the global project situation or solve the terminal objective. Examples include a new structural theorem, exact recurrence, integrality theorem, reusable estimate, or precisely scoped impossibility boundary.
- A **route-local conclusion** is useful only for understanding one route's execution history. Keep it in authoritative memory and the route archive; do not create a separate map node merely to preserve every local observation.
- An **experiment or obstacle record** preserves finite computations, bounded negatives, missing bridges, and failure boundaries without promoting them into general theorems.

Do not discard a verified byproduct because the terminal objective remains open. After independent verification, promote it to authoritative memory and classify it. Put it in `milestones` if it changed the project-wide picture, in `results` if it has independent reuse value, or only in the relevant route archive when its value is local. One conclusion may be both globally decisive and independently reusable, but the visible map should avoid duplicate prose: make the milestone the primary node and link a separate result node only when it provides a genuinely reusable theorem statement or method package.

## Required causal content

Each milestone records its verified conclusion, method overview, central parameter or object definitions, short method spine, reusable structures, effect on the bottleneck, non-implication boundary, status, and authoritative references. The overview says which method family is used, what baseline is extended, what the project changed, and why that change can affect the target before technical steps appear.

Each standalone result records:

- `note_path`: the dedicated visible Markdown note, relative to the map root;
- `theorem_callout_type`: `theorem` or `proposition`, matching the note's Obsidian callout;
- `proof_heading`: the level-two heading under which the complete proof appears;
- `statement`: the exact mathematical conclusion;
- `scope`: assumptions, domain, and quantifier range;
- `method_overview`, `parameter_definitions`, and `method_spine`;
- `novelty_and_source`: what is new inside this project and where the authority comes from, without making an unsupported literature-priority claim;
- `relation_to_objective`: how it helps, fails to help, or remains neutral toward the terminal objective;
- `reusable_value`: what future routes or other work can reuse;
- `cannot_imply`: the precise boundary against overclaiming;
- `evidence_refs` and a verification status.

The dedicated result note is the human-readable canonical result package. Self-containment is a property of the whole note, not of one oversized theorem box. Put notation, object definitions, and standing hypotheses in a setup section when useful; write the bound theorem or proposition callout as the concise core claim; put immediate consequences in separate corollary callouts and scope limitations in remarks. The same note must contain the complete proof under its bound level-two proof heading. A proof outline, finite check, verifier verdict, asset pointer, or link to a route archive is supporting evidence, not a substitute for the proof. Keep route history and raw certificates linked for audit after the self-contained setup, statement, and proof.

The machine validator checks the note path, expected callout type, nonempty non-placeholder core statement, proof heading, substantial proof body, and common placeholder or delegated-proof phrases. It deliberately does not impose a minimum theorem length: verbosity is not mathematical completeness. It cannot decide by syntax alone whether the setup defines every symbol, the statement is well scoped and concise, every proof step is correct, or the result is publishable; independent mathematical verification remains mandatory. This residual semantic gap must never be hidden behind a structural PASS.

The map records the evidence-backed route landscape, current bottlenecks, obstacles, failure boundaries, and reranking conditions. It does not select the next route. A `route_decision` is created only at window start for one portfolio member/attempt and states `why_now`, comparison with alternatives, targeted bottleneck, uncertainty, gates, and authoritative references. Priority is an execution decision, never a success probability.

Every route keeps separate success and candidate-failure gates. A failed candidate closes only that candidate. Treat a whole route as failed only when an independently verified impossibility boundary names the exact route scope.

The machine control file is `.research/research-map.json`. Its official v1 fields and failure rules are enforced by `scripts/research_map_v1.py`. Visible Markdown may be reorganized for readability only after evidence, memory, route review, and machine controls agree. Directory names and numeric filename prefixes are human navigation aids, not node types, IDs, authority, or lifecycle state.

Before an export that contains standalone results, run `scripts/validate_research_map.py <map-root> --for-result-export`. The export gate also requires every included result to have status `verified` or `independently_verified`. Do not export a `conditional` or `review_required` node as an established research result.

## Authority and publication order

Use this order inside `window_reconciliation`: evidence object → independent verification → promotion decision → promoted memory item → result classification → scoped route-delta application → route review → complete authority inventory → global synthesis and reclassification → affected node pages → rewritten main survey → control file → publication synthesis gate → validation receipt → fresh-subagent semantic-review loop → closure validation → project-head publication. Do not create a `route_decision` here. Never invent a causal explanation, route equivalence, cross-route law, or standalone theorem in the map to fill a missing authoritative record. Mark the affected node `review_required` instead.

The pre-standardization map prototypes remain readable through their frozen validators. Migration preserves their original bytes and rebuilds an official v1 map as a derived view. If method provenance, result scope, verification state, or route-selection reasons cannot be recovered, retain `review_required`.

## Bounded loading

Window planning reads only the validation receipt, main map, evidence rules, route landscape/review, directly relevant milestones or standalone results, obstacles, and the binding bridge. It then creates fresh proposals, portfolio, and attempt-local route decisions. A standalone result is loaded when a proposal may reuse it, frozen cognition names it, or a retrieval trigger requests its detail; the existence of a result registry does not authorize loading every result body. Follow wikilinks or asset and memory pointers only when the current work requires the detail. Do not load the entire history into model context.
