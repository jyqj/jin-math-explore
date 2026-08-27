#!/usr/bin/env python3
"""Regression entry equivalent to test_math_research_project_archive.ps1."""

import unittest
from test_math_research_project_archive_native import ProjectArchiveNativeTests


def main() -> int:
    result=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProjectArchiveNativeTests))
    passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped); failed=len(result.failures)+len(result.errors)
    print(f"RESULT passed={passed} failed={failed}")
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__": raise SystemExit(main())
