#!/usr/bin/env python3
"""Native migration success and fail-closed tests."""

from __future__ import annotations

import unittest

from test_math_research_migrate_v8_to_v10 import MigrationTests


if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for name in loader.getTestCaseNames(MigrationTests):
        if name != "test_official_v8_writer_rejects_freeze_marker":
            suite.addTest(MigrationTests(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
