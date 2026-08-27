#!/usr/bin/env python3
"""Regression entry equivalent to test_math_research_cycle_ledger.ps1."""

from __future__ import annotations

import unittest

from test_math_research_cycle_ledger_native import CycleLedgerNativeTests


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CycleLedgerNativeTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures) + len(result.errors)
    print(f"RESULT passed={passed} failed={failed}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
