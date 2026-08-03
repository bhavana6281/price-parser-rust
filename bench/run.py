#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class Server:
    def __init__(self, command: list[str], env: dict[str, str] | None = None) -> None:
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )

    def call(self, request: dict[str, Any]) -> dict[str, Any]:
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(stderr)
        return json.loads(line)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=2)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * fraction))
    return ordered[index]


def measure(server: Server, corpus: list[dict[str, Any]], warmups: int, rounds: int) -> dict[str, float]:
    for _ in range(warmups):
        for request in corpus[: min(500, len(corpus))]:
            server.call(request)

    latencies_ms: list[float] = []
    total_start = time.perf_counter()
    for _ in range(rounds):
        for request in corpus:
            start = time.perf_counter_ns()
            server.call(request)
            latencies_ms.append((time.perf_counter_ns() - start) / 1_000_000)
    elapsed = time.perf_counter() - total_start
    return {
        "requests": float(len(latencies_ms)),
        "elapsed_seconds": elapsed,
        "throughput_requests_per_second": len(latencies_ms) / elapsed,
        "latency_median_ms": statistics.median(latencies_ms),
        "latency_p95_ms": percentile(latencies_ms, 0.95),
        "latency_p99_ms": percentile(latencies_ms, 0.99),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=str(ROOT / "bench" / "corpus.jsonl"))
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--upstream", default=str(ROOT / ".upstream" / "price-parser"))
    parser.add_argument("--rust-bin", default=str(ROOT / "target" / "release" / "price-parser"))
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    corpus = [json.loads(line) for line in corpus_path.read_text().splitlines() if line.strip()]
    digest = hashlib.sha256(corpus_path.read_bytes()).hexdigest()

    env = os.environ.copy()
    env["PYTHONPATH"] = args.upstream
    python_server = Server([sys.executable, str(ROOT / "fuzz" / "oracle_server.py")], env)
    rust_server = Server([args.rust_bin, "--jsonl"])
    try:
        python_results = measure(python_server, corpus, args.warmups, args.rounds)
        rust_results = measure(rust_server, corpus, args.warmups, args.rounds)
    finally:
        python_server.close()
        rust_server.close()

    report = {
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "methodology": "Persistent JSONL process for each implementation; identical request corpus and serialization boundary.",
        "corpus_sha256": digest,
        "corpus_cases": len(corpus),
        "warmups": args.warmups,
        "rounds": args.rounds,
        "python": python_results,
        "rust": rust_results,
        "speedup": rust_results["throughput_requests_per_second"] / python_results["throughput_requests_per_second"],
    }
    output = ROOT / "bench" / "results.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
