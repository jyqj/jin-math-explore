#!/usr/bin/env python3
"""Run native v9/v10 engine tests used by thin Python entrypoint mappings."""

from __future__ import annotations

import unittest

from test_math_research_state_v9 import MathResearchV9Tests
from test_math_research_state_v10 import MathResearchV10Tests


EXCLUDED = {
    # These two cases validate the legacy shell delegation chain.  They are
    # intentionally excluded from the native-entrypoint receipt and remain
    # blocked in the platform parity manifest until that classifier is ported.
    (MathResearchV9Tests, "test_startup_v4_delegates_to_v3_with_legacy_parameter_name"),
    (MathResearchV10Tests, "test_startup_v5_delegates_to_v4_with_legacy_parameter_name"),
}


def suite() -> unittest.TestSuite:
    result = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for case in (MathResearchV9Tests, MathResearchV10Tests):
        for name in loader.getTestCaseNames(case):
            if (case, name) not in EXCLUDED:
                result.addTest(case(name))
    return result


if __name__ == "__main__":
    outcome = unittest.TextTestRunner(verbosity=2).run(suite())
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
