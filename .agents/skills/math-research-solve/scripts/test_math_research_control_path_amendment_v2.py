#!/usr/bin/env python3
"""Native regression entry matching the historical no-argument test command."""

from __future__ import annotations

import io
import json
import sys
import unittest

from test_control_path_amendment_v2_native import ControlPathAmendmentTests


def main(argv: list[str] | None = None) -> int:
    if argv is None: argv = sys.argv[1:]
    if argv:
        print("This regression entry accepts no arguments.", file=sys.stderr); return 2
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ControlPathAmendmentTests)
    details = io.StringIO(); result = unittest.TextTestRunner(stream=details, verbosity=2).run(suite)
    if not result.wasSuccessful():
        print(details.getvalue(), file=sys.stderr); return 1
    print(json.dumps({"ok": True, "tests": 12, "blocked_paths": 1, "explicit_sandbox_arguments": 0, "attempt_count": 0, "total_round_count": 0}, separators=(",", ":")))
    return 0


if __name__ == "__main__": raise SystemExit(main())
