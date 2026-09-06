#!/usr/bin/env python3
"""Separate finite-set replay and literal subset oracle; not an isolated reviewer."""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

CASES = ((38, 174), (38, 176), (39, 180), (39, 182), (40, 184), (40, 186))
SOURCE = (0, 2, 6, 12, 20, 26, 30, 32, 36, 42, 48, 50, 56, 60, 68, 72, 78, 86, 90, 92,
          98, 102, 110, 116, 120, 126, 132, 138, 140, 146, 152, 156, 158, 162,
          168, 170, 176, 180, 182, 186)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def primes(n: int) -> list[int]:
    # Trial division over all smaller integers is independent of the generator.
    return [p for p in range(2, n + 1) if not any(p % a == 0 for a in range(2, p))]


def encoded(states: set[frozenset[int]]) -> list[str]:
    return [hex(v) for v in sorted(sum(2 ** i for i in s) for s in states)]


def checkpoint(p: int, states: set[frozenset[int]]) -> dict:
    raw = json.dumps(encoded(states), separators=(",", ":")).encode("ascii")
    return {"prime": p, "count": len(states), "maximum_size": max(map(len, states), default=0),
            "sha256": hashlib.sha256(raw).hexdigest()}


def set_search(k: int, diameter: int) -> tuple[list[dict], set[frozenset[int]], list[str]]:
    whole = frozenset(range(diameter // 2 + 1))
    states = {whole} if len(whole) >= k else set()
    layers = [checkpoint(2, states)]
    critical = []
    for p in primes(k):
        if p == 2:
            continue
        following = set()
        for s in states:
            for r in range(1, p):
                t = frozenset(a for a in s if a % p != r)
                if len(t) >= k:
                    following.add(t)
        states = following
        layers.append(checkpoint(p, states))
        if (k, diameter, p) == (40, 184, 17):
            critical = encoded(states)
    return layers, states, critical


def admissible(t: tuple[int, ...]) -> bool:
    return len(set(t)) == len(t) and all(len({a % p for a in t}) < p for p in primes(len(t)))


def check_payload(cert: dict, result: dict, inp: dict) -> dict:
    expected_inputs = {"schema": "twin-tuple-input/v1", "attempt": "A-TP-TUPLE-0008",
                       "cases": [list(c) for c in CASES], "normalization": "min=0; shift=2*bit_index",
                       "source_tuple": list(SOURCE), "prime_cutoff": "all primes <= cardinality"}
    require(inp == expected_inputs, "input contract changed")
    require(set(cert) == {"schema", "case_order", "cases"}, "certificate fields")
    require(cert["schema"] == "twin-tuple-certificate/v1", "certificate schema")
    require(cert["case_order"] == [list(c) for c in CASES] and len(cert["cases"]) == 6, "case coverage")
    summaries, count, critical_count = [], 0, 0
    for c, (k, d) in zip(cert["cases"], CASES):
        require(set(c) == {"k", "diameter", "layers", "final_masks", "critical_after_17"}, "case fields")
        require((c["k"], c["diameter"]) == (k, d), "case identity")
        layers, states, critical = set_search(k, d)
        require(c["layers"] == layers, "layer replay mismatch")
        require(c["final_masks"] == encoded(states), "final states mismatch")
        require(c["critical_after_17"] == critical, "critical frontier mismatch")
        if critical:
            critical_count = len(critical)
            require(critical_count == 6, "critical count")
            for mask in critical:
                indices = {i for i in range(d // 2 + 1) if int(mask, 16) // (2 ** i) % 2}
                require(len(indices) == 40 and len({i % 19 for i in indices}) == 19, "p19 obstruction")
        if not states:
            require((k, d) in {(38, 174), (39, 180), (40, 184)}, "unexpected infeasibility")
            continue
        tuples = sorted(tuple(2 * a for a in sorted(s)) for s in states)
        require(all(len(t) == k and t[0] == 0 and t[-1] == d for t in tuples), "classification coverage")
        require(all(admissible(t) for t in tuples), "positive witness inadmissible")
        reflected = [tuple(sorted(d - a for a in t)) for t in tuples]
        require(set(tuples) == set(reflected), "reflection closure")
        summaries.append({"k": k, "minimum_diameter_candidate": d, "normalized_minimizers": len(tuples),
                          "reflection_classes": len({min(t, u) for t, u in zip(tuples, reflected)}),
                          "self_reflecting": sum(t == u for t, u in zip(tuples, reflected)),
                          "lexicographic_first": list(tuples[0]), "source_tuple_present": SOURCE in tuples})
        count += len(tuples)
    expected = {"schema": "twin-tuple-results/v1", "status": "solver_candidate", "evidence": "exact_check",
                "summaries": summaries, "endpoint_detector": {"formula": "m+a+b-1-a*b", "truth_table_states": 156, "target_max_gap": 184,
                                    "weighted_sufficient_condition": "sum(w*r)-sum(w)-sum(w*a*b)>0",
                                    "estimate_proved": False}, "independently_verified": False, "new_prime_gap_bound": False,
                "twin_prime_conjecture_proved": False,
                "cannot_imply": ["DHL[39,2] or DHL[38,2]", "a lower bound on actual prime gaps",
                                 "a new prime-gap upper bound", "infinitely many twin primes"]}
    require(result == expected, "result or authority boundary mismatch")
    return {"replayed_cases": 6, "checked_positive_tuples": count, "p17_critical_survivors": critical_count,
            "source_missing_residues": {str(p): min(set(range(p)) - {a % p for a in SOURCE}) for p in primes(40)}}


def endpoint_oracle() -> int:
    checked = 0
    for m in range(39):
        for a, b in itertools.product((0, 1), repeat=2):
            score = m + a + b - 1 - a * b
            good = m >= 2 or (m >= 1 and a + b >= 1)
            require((score > 0) == good, "endpoint exclusion truth table")
            checked += 1
    require(0 + 1 + 1 - 1 > 0, "missing-subtraction negative fixture")
    require(0 + 1 + 1 - 1 - 1 == 0, "endpoint-only pair must not pass")
    return checked


def small_oracle() -> dict:
    # Literal subsets contain odd and even shifts; no parity-reduction assumption here.
    cases, examined = 0, 0
    for k in range(2, 7):
        for d in range(0, 15):
            _, states, _ = set_search(k, d)
            by_states = set()
            for s in states:
                for choice in itertools.combinations(sorted(s - {0}), k - 1):
                    by_states.add((0,) + tuple(2 * a for a in choice))
            direct = set()
            for choice in itertools.combinations(range(1, d + 1), k - 1):
                examined += 1
                t = (0,) + choice
                if admissible(t):
                    direct.add(t)
            require(by_states == direct, f"literal oracle k={k},d={d}")
            cases += 1
    return {"literal_subset_cases": cases, "literal_subsets_examined": examined}


def negative_checks(cert: dict, result: dict, inp: dict) -> int:
    bad = []
    def add(target: str, mutate) -> None:
        payload = [copy.deepcopy(cert), copy.deepcopy(result), copy.deepcopy(inp)]
        mutate(payload[{"c": 0, "r": 1, "i": 2}[target]])
        bad.append(payload)
    add("c", lambda x: x["cases"].pop())
    add("c", lambda x: x["case_order"].reverse())
    add("c", lambda x: x["cases"][0]["layers"].pop())
    add("c", lambda x: x["cases"][0]["layers"][1].update(prime=4))
    add("c", lambda x: x["cases"][0]["layers"][1].update(count=999))
    add("c", lambda x: x["cases"][0]["layers"][1].update(sha256="0" * 64))
    add("c", lambda x: x["cases"][-1]["final_masks"].pop())
    add("c", lambda x: x["cases"][-1]["final_masks"].append(x["cases"][-1]["final_masks"][0]))
    add("c", lambda x: x["cases"][-1]["final_masks"].append(hex(1 << 100)))
    add("c", lambda x: x["cases"][4]["critical_after_17"].pop())
    add("c", lambda x: x["cases"][4].update(diameter=182))
    add("r", lambda x: x["summaries"][-1].update(reflection_classes=12))
    add("r", lambda x: x.update(independently_verified=True))
    add("r", lambda x: x.update(twin_prime_conjecture_proved=True))
    add("r", lambda x: x.update(new_prime_gap_bound=True))
    add("r", lambda x: x.update(cannot_imply=[]))
    add("i", lambda x: x["source_tuple"].__setitem__(1, 1))
    add("i", lambda x: x.update(prime_cutoff="only 17"))
    add("r", lambda x: x["endpoint_detector"].update(formula="m+a+b-1"))
    add("r", lambda x: x["endpoint_detector"].update(estimate_proved=True))
    for i, payload in enumerate(bad):
        try:
            check_payload(*payload)
        except (ValueError, KeyError, TypeError):
            continue
        raise ValueError(f"corruption {i} accepted")
    return len(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check-hashes", action="store_true")
    ap.add_argument("--require-global", action="store_true")
    args = ap.parse_args()
    try:
        if args.require_global:
            raise ValueError("refused: this package cannot certify a prime-gap theorem or twin primes")
        read = lambda name: json.loads((args.root / name).read_text(encoding="utf-8"))
        cert, result, inp = (read(n) for n in ("certificate.json", "results.json", "inputs.json"))
        report = check_payload(cert, result, inp)
        if args.self_test:
            report.update(small_oracle())
            report["endpoint_truth_table_states"] = endpoint_oracle()
            report["corruptions_rejected"] = negative_checks(cert, result, inp)
        if args.check_hashes:
            manifest = read("artifact-sha256.json")
            names = {"README.md", "proof.md", "enumerate_tuples.py", "verify_tuples.py", "inputs.json",
                     "certificate.json", "results.json", "source-lock.json", "computation-record.json",
                     "computation-handoff.json", "verification-ticket.md"}
            require(set(manifest) == names, "manifest exact scope")
            for name, expected in manifest.items():
                require(hashlib.sha256((args.root / name).read_bytes()).hexdigest() == expected, "hash: " + name)
            report["hashes_verified"] = len(manifest)
        report.update(ok=True, independently_verified=False, new_prime_gap_bound=False)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
