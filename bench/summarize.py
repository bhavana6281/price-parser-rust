#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parts = {}
for name in ("results", "cold_start", "rss"):
    path = ROOT / "bench" / f"{name}.json"
    parts[name] = json.loads(path.read_text(encoding="utf-8"))
summary = {
    "status": "complete",
    "steady_state": parts["results"],
    "cold_start": parts["cold_start"],
    "memory": parts["rss"],
}
path = ROOT / "bench" / "report.json"
path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(path)
