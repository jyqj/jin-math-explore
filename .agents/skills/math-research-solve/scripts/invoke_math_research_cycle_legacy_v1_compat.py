#!/usr/bin/env python3
"""Legacy-v1 compatibility entry for the native cycle-ledger CLI."""

from invoke_math_research_cycle_v2 import main


if __name__ == "__main__":
    raise SystemExit(main())
