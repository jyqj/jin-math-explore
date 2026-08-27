# Frozen v10 to v11 compatibility

The former bundled merge utilities were a one-project transition and are retired from the reusable Skill. Existing v11 projects remain readable through the project-neutral Full Startup validator; that validator is read-only and reports `mutation_supported=false`.

Do not reconstruct a historical merge from remembered constants. A still-unmigrated project must first pass its frozen source Startup, then use the current v13 migration protocol with an owner-reviewed, project-local adapter whose exact file hash is pinned at invocation. The adapter lives outside the Skill, binds the complete source inventory and objective bytes, stages outside every source root, runs independent map semantic review, and retains its exact journal and recovery tree.

This compatibility change removes project examples and answer material from the installed Skill without rewriting any frozen v10 or v11 project byte. It narrows executable legacy support; it does not invalidate already published heads.
