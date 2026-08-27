---
name: math-frontier-scout
description: Discover candidate hard mathematics research problems and missing lemmas for jin-math-explore. Use when scouting primary literature, extracting explicit open questions, identifying optimality or counterexample frontiers, or proposing candidates for independent source audit; never declare a problem open from search failure.
---

# Math Frontier Scout

## Contract

Produce candidates, not Project authority. Every candidate must be precise enough to falsify or audit.

## Workflow

1. Freeze the scouting domain, source date, language range, and allowed source types.
2. Prefer primary papers, official problem lists, monographs, and authoritative surveys. Preserve title, author, date, theorem/problem identifier, and stable locator.
3. Separate:
   - `known_open` only when a current authoritative source explicitly supports it;
   - `likely_open_needs_audit` when status remains uncertain;
   - internal frontiers, missing lemmas, generalizations, optimality questions, computational conjectures, and counterexample searches.
4. For every candidate record statement, domain, quantifier order, assumptions, known results, why the gap matters, smallest decisive subquestion, possible proof objects, source freshness, and uncertainty.
5. Search for equivalent formulations and obvious solved variants before proposing the candidate.
6. Submit a Problem Candidate Issue. Do not create a Project, freeze an objective, or label a claim novel/open without `$math-source-audit` PASS.

## Failure boundary

No result, poor search recall, model unfamiliarity, or lack of a quick proof is not evidence that a problem is open.
