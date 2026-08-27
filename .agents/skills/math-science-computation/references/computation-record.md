# Computation record

Use `computation-record.json` for program delivery, long calculations, and any task for which the user requests files or reproducibility evidence.

## Required content

- the task file and its SHA-256;
- the mathematical object and requested deliverables;
- assumptions, domain or coefficient field, and precision policy;
- targeted Mathematica, SageMath, and Python candidate implementations, including existence and local-availability evidence;
- the selected backend, version, interface, selection reason, and a nonempty fallback reason or `not-required`;
- exact input, command, or code entry point;
- relative paths and SHA-256 hashes for at least one code artifact and one result artifact;
- a completed result summary;
- one or more verification methods, an evidence level, residual or error information when the precision mode is numerical, and known limitations.

The five evidence levels are:

- `proof-certificate`: the artifact is a checkable certificate whose mathematical sufficiency is explained;
- `formal-verification`: an identified formal system checked the stated theorem under recorded assumptions;
- `exact-check`: exact computation verifies a specified identity, object, or finite certificate;
- `bounded-check`: exhaustive or exact verification covers only the recorded finite range;
- `numerical-evidence`: floating-point, sampled, simulated, or approximate evidence.

The label reports the strongest justified status of the computation, not the importance of the result.

## Artifact paths

Keep artifact paths relative to the record directory or the explicit `--base-dir`. The validator rejects absolute paths and paths that escape that directory. Hash the final files after all edits.

Do not include `computation-record.json` as one of its own hashed artifacts. That would create a circular hash dependency.

## Validator scope

`computation_record.py validate` checks schema fields, safe relative paths, file existence, and hashes. It does not execute code, inspect mathematical semantics, or prove that the chosen evidence level is correct. Review those claims separately.
