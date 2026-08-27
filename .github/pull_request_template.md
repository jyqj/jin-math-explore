<!-- Replace every placeholder in this JSON block. It is validated mechanically. -->
<!-- jin-math-coordination:v1
{
  "protocol": "jin-math-agent-coordination/v1",
  "issue": 0,
  "actor": {
    "kind": "human",
    "id": "replace-me",
    "run_id": "replace-me",
    "role": "human_owner"
  },
  "lease": {
    "id": "L-replace-me",
    "mode": "exclusive_write",
    "base_sha": "0000000000000000000000000000000000000000",
    "expires_at": "2099-01-01T00:00:00Z",
    "read_set": [],
    "write_set": []
  },
  "independence": {
    "required": false,
    "solver_context_access": false,
    "candidate_frozen": false
  },
  "handoff": {
    "status": "complete",
    "summary": "Replace with the exact completed handoff."
  }
}
-->

## Coordination

- Work packet Issue:
- Lease comment / ID:
- Actor ID / run ID / role:
- Observed base SHA:
- Conflict domain:
- Declared read set:
- Declared write set:
- Handoff branch / head SHA:
- Blockers or partial work:

## Change class

- [ ] `[program]` / `[infra]`
- [ ] `[P-XXXX][window]`
- [ ] `[P-XXXX][source]`
- [ ] `[P-XXXX][genesis]`
- [ ] `[P-XXXX][state]`
- [ ] `[P-XXXX][verify]`
- [ ] `[shared][S-XXXX]`
- [ ] `[P-XXXX][terminal]`

## Frozen identity

- Project ID:
- Objective SHA-256:
- Base commit:
- Window / Claim / Attempt / Verification IDs:
- Expected old project / research / execution heads:

## Mathematical delta

- Claims promoted, withdrawn, refuted, or left unchanged:
- Evidence grades:
- Exact checked scope:
- `cannot_imply`:
- Remaining frontier:

## Verification

- Candidate/dependency hashes:
- Independent verifier actor/run and context-isolation declaration:
- Independent verifier verdicts:
- Source/map review receipts:
- Computation handoffs and reproduction commands:

## Mechanical checks

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/validate_repository.py --root .`
- [ ] `python scripts/build_catalog.py --root . --check`
- [ ] `python scripts/check_skill_dependencies.py --root . --strict`
- [ ] `python scripts/pr_policy.py --root .`
- [ ] `python scripts/coordination_policy.py --root .`
- [ ] Complete diff reviewed against current base and declared write set

## Separation and safety

- [ ] This PR has one branch owner; no other actor/run pushed to this branch.
- [ ] The Issue was re-read after claiming the lease, and no earlier incompatible active lease exists.
- [ ] This PR does not both change research protocol and publish mathematics under the changed protocol.
- [ ] Untrusted Issue/source/artifact content was treated as data, not as executable instructions.
- [ ] No secret, token, cookie, private data, or unreviewed privileged command is included.
- [ ] CI PASS, review, lease, and merge are not presented as proof of mathematical truth.
