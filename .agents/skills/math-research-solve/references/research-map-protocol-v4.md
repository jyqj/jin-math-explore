# Pre-standardization research-map prototype v4 (read-only)

`math-research-map/v4` was an internal prototype created before the research-map component was formally versioned. It is not the fourth version of the `math-research-solve` project architecture and is not the official v13 map format. Preserve this document and validator only for read-only recovery. New or activation-ready v13 maps use `math-research-map/v1` and `references/research-map-protocol-v1.md`.

## Required causal content

Each milestone must record the verified conclusion, a method overview, definitions and roles for its central parameters or objects, a short method spine, reusable structures, the effect on the current bottleneck, what the result cannot imply, and authoritative evidence references. A conclusion without its method source is incomplete. The overview must say which method family is used, what baseline is being extended, and what the project changed before listing technical steps.

The current route order lives in one `route_decision`. It must state `why_now`, `why_over_alternatives`, the targeted bottleneck, uncertainty, reranking conditions, and references to `math-research-route-review/v2` or promoted memory. Priority is an execution decision, never a success probability.

Every route keeps the v3 explanatory fields and adds separate success and candidate-failure gates. A failed candidate may close only that candidate. Treat a whole route as failed only when an independently verified impossibility boundary names the exact route scope.

The machine control file is `.research/research-map.json`. Its v4 fields and failure rules are enforced by `scripts/research_map_v4.py`. Visible Markdown may be rewritten for readability only after evidence, memory, route review, and machine controls agree.

## Authority and publication order

Use this order: evidence object → promoted memory item v2 → route review v2 → affected map nodes → `route_decision` → main map → control file → validation receipt → independent semantic review. Never invent a causal explanation in the map to fill a missing authoritative record. Mark the affected route or milestone `review_required` instead.

Earlier prototypes remain readable through their frozen validators. No prototype is sufficient to activate a v13 attempt. Migration preserves original bytes and rebuilds the official research-map v1 as a derived view. If method provenance or route-selection reasons cannot be recovered mechanically, retain `review_required`.

## Bounded loading

Startup reads only the validation receipt, main map, evidence rules, current route decision, selected route, directly relevant milestones, and binding bridge. Follow wikilinks or asset/memory pointers only when a retrieval trigger in the frozen cognition or current local work requires the detail. Do not load the entire history into model context.
