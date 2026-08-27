# Project layout v12

`math-research-project/v12` exposes exactly seven root entries:

```text
README.md
当前状态.md
已验证结论.md
障碍与失败.md
下一步路线.md
project.json
.research/
```

The five Markdown files are deterministic generated views. `project.json` is the compact head. `.research/` is authoritative and contains exactly `state/`, `memory/`, `runs/`, `evidence/`, `intakes/`, `imported-projects/`, and `objects/`.

Raw bytes live once at `.research/objects/sha256/<first-two>/<full-sha256>`. Imported trees contain ordered `(path, sha256, size)` records and a canonical tree hash. Reject absolute paths, `..`, duplicate/case-colliding paths, symlinks, Windows reparse points, missing objects, bad hashes, and unexpected archive files.

Startup v7 verifies the head pointers, immutable objective, state, memory index, archive manifest, object trees, exact root layout, and generated views. View mismatch yields `v12_view_drift`: reading remains possible, but publication is barred until `repair-views` under a fresh active Goal.

Legacy v3-v11 projects are read through their frozen Startup paths. A v12 writer never edits them in place.
