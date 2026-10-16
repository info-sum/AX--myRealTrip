#!/usr/bin/env python3
"""Analyze a synthetic trip disruption fixture and print an incident brief."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trip_graph_rescue import analyze_trip


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/analyze_trip.py <synthetic-fixture.json>", file=sys.stderr)
        return 2
    fixture_path = Path(sys.argv[1])
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    print(json.dumps(analyze_trip(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
