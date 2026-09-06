#!/usr/bin/env python3
"""Exact omitted-residue enumeration; standard library, no floating acceptance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from math import isqrt

CASES = ((38, 174), (38, 176), (39, 180), (39, 182), (40, 184), (40, 186))
SOURCE = (0, 2, 6, 12, 20, 26, 30, 32, 36, 42, 48, 50, 56, 60, 68, 72, 78, 86, 90, 92,
          98, 102, 110, 116, 120, 126, 132, 138, 140, 146, 152, 156, 158, 162,
          168, 170, 176, 180, 182, 186)


def primes(n: int) -> list[int]:
    return [p for p in range(2, n + 1) if all(p % d for d in range(2, isqrt(p) + 1))]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def layer(p: int, states: set[int]) -> dict:
    masks = [hex(s) for s in sorted(states)]
    return {"prime": p, "count": len(states), "maximum_size": max(map(int.bit_count, states), default=0),
            "sha256": hashlib.sha256(canonical(masks)).hexdigest()}


def enumerate_case(k: int, diameter: int) -> dict:
    if type(k) is not int or type(diameter) is not int or k < 2 or diameter < 0:
        raise ValueError("k>=2 and nonnegative integer diameter required")
    n = diameter // 2
    states = {(1 << (n + 1)) - 1} if n + 1 >= k else set()
    layers = [layer(2, states)]
    critical = []
    for p in primes(k)[1:]:
        remove = [sum(1 << j for j in range(r, n + 1, p)) for r in range(1, p)]
        states = {t for s in states for m in remove if (t := s & ~m).bit_count() >= k}
        layers.append(layer(p, states))
        if k == 40 and diameter == 184 and p == 17:
            critical = [hex(s) for s in sorted(states)]
    return {"k": k, "diameter": diameter, "layers": layers,
            "final_masks": [hex(s) for s in sorted(states)], "critical_after_17": critical}


def decode(mask: str) -> tuple[int, ...]:
    n = int(mask, 16)
    return tuple(2 * i for i in range(n.bit_length()) if (n >> i) & 1)


def summaries(cases: list[dict]) -> list[dict]:
    out = []
    for c in cases:
        if not c["final_masks"]:
            continue
        k, d = c["k"], c["diameter"]
        tuples = sorted(decode(m) for m in c["final_masks"])
        if any(len(t) != k or t[0] != 0 or t[-1] != d for t in tuples):
            raise ValueError("classification requires exact-size, full-span final states")
        reflection = lambda t: tuple(d - x for x in reversed(t))
        if any(reflection(t) not in tuples for t in tuples):
            raise ValueError("reflection closure failed")
        out.append({"k": k, "minimum_diameter_candidate": d, "normalized_minimizers": len(tuples),
                    "reflection_classes": len({min(t, reflection(t)) for t in tuples}),
                    "self_reflecting": sum(t == reflection(t) for t in tuples),
                    "lexicographic_first": list(tuples[0]),
                    "source_tuple_present": SOURCE in tuples})
    return out


def build() -> tuple[dict, dict]:
    cases = [enumerate_case(k, d) for k, d in CASES]
    cert = {"schema": "twin-tuple-certificate/v1", "case_order": [list(x) for x in CASES], "cases": cases}
    result = {"schema": "twin-tuple-results/v1", "status": "solver_candidate", "evidence": "exact_check",
              "summaries": summaries(cases), "endpoint_detector": {"formula": "m+a+b-1-a*b", "truth_table_states": 156, "target_max_gap": 184,
                                    "weighted_sufficient_condition": "sum(w*r)-sum(w)-sum(w*a*b)>0",
                                    "estimate_proved": False}, "independently_verified": False,
              "new_prime_gap_bound": False, "twin_prime_conjecture_proved": False,
              "cannot_imply": ["DHL[39,2] or DHL[38,2]", "a lower bound on actual prime gaps",
                               "a new prime-gap upper bound", "infinitely many twin primes"]}
    return cert, result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--list-tuples", action="store_true")
    args = ap.parse_args()
    cert, result = build()
    if args.list_tuples:
        print(json.dumps({f'{c["k"]}:{c["diameter"]}': [decode(m) for m in c["final_masks"]]
                          for c in cert["cases"]}, indent=2))
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (("certificate.json", cert), ("results.json", result)):
        (args.output_dir / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "cases": len(CASES), "summaries": result["summaries"]}, sort_keys=True))


if __name__ == "__main__":
    main()
