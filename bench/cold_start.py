#!/usr/bin/env python3
"""Measure cold process startup plus one parse for Python and Rust."""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * fraction))
    return ordered[index]


def measure(command: list[str], rounds: int, env: dict[str, str] | None = None) -> dict[str, float]:
    samples: list[float] = []
    for _ in range(rounds):
        started = time.perf_counter_ns()
        completed = subprocess.run(
            command,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)
        samples.append(elapsed_ms)
    return {
        "rounds": float(rounds),
        "median_ms": statistics.median(samples),
        "p95_ms": percentile(samples, 0.95),
        "p99_ms": percentile(samples, 0.99),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=100)
    parser.add_argument("--upstream", default=str(ROOT / ".upstream" / "price-parser"))
    parser.add_argument("--rust-bin", default=str(ROOT / "target" / "release" / "price-parser"))
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = args.upstream
    python_code = "from price_parser import Price; Price.fromstring('$1,299.95')"
    report = {
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "methodology": "Fresh process for each sample; import/startup plus one parse; stdout discarded.",
        "python": measure([sys.executable, "-c", python_code], args.rounds, env),
        "rust": measure([args.rust_bin, "$1,299.95"], args.rounds),
    }
    output = ROOT / "bench" / "cold_start.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
