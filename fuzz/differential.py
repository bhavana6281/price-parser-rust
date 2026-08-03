#!/usr/bin/env python3
"""Grammar-aware differential tester for Python versus Rust behavior."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class JsonlProcess:
    process: subprocess.Popen[str]

    @classmethod
    def start(cls, command: list[str], env: dict[str, str] | None = None) -> "JsonlProcess":
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        return cls(process)

    def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"process exited: {stderr}")
        return json.loads(line)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()


CURRENCIES = [
    "$", "€", "£", "US$", "A$", "R$", "CHF", "EUR", "GBP", "USD", "SGD", "NZD",
    "OMR", "AED", "Kč", "₽", "₹", "Rp", "تومان", "₪", "₿", "PTE", "DEM",
]
AMOUNTS = [
    "0", "1", "12.99", "12,99", "1,234", "1.234", "1 234,50", "1'049,95",
    ".75", "35€99", "1,235€99", "140.000", "34.992001", "1.11000000000000009770",
]
WRAPPERS = [
    "{c}{a}", "{c} {a}", "{a} {c}", "price: {c}{a}", "Now {a} {c}!", "({c} {a})",
    "was 99.00, now {c}{a}", "SKU 123 / {c}{a}",
]
HINTS = [None, "GBP", "USD", "EUR", "$", "SGD$", "price in CHF"]
SEPARATORS = [None, ".", ","]
GROUP_SEPARATORS = [None, ".", ",", " "]
SPECIALS = [
    "Free", "FREE SHIPPING", "50% OFF", "99,99 EUR (-30,00%) 69,99 EUR",
    "35€ 99", "35€ 999", "1,235€ 99", "$.75", "US$:12.99", "SGD$4.90",
    "", None,
]


def generate(rng: random.Random) -> dict[str, Any]:
    if rng.random() < 0.2:
        value = rng.choice(SPECIALS)
    else:
        amount = rng.choice(AMOUNTS)
        currency = rng.choice(CURRENCIES)
        value = rng.choice(WRAPPERS).format(a=amount, c=currency)
        if rng.random() < 0.2:
            value = "\u00a0".join(value.split(" "))
        if rng.random() < 0.1:
            value += rng.choice([" %", " + tax", " / Each", "\n"])
    return {
        "input": value,
        "currency_hint": rng.choice(HINTS),
        "decimal_separator": rng.choice(SEPARATORS) if rng.random() < 0.25 else None,
        "digit_group_separator": rng.choice(GROUP_SEPARATORS) if rng.random() < 0.15 else None,
    }


def differs(oracle: JsonlProcess, rust: JsonlProcess, case: dict[str, Any]) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    expected = oracle.call(case)
    actual = rust.call(case)
    return expected != actual, expected, actual


def minimize(oracle: JsonlProcess, rust: JsonlProcess, case: dict[str, Any]) -> dict[str, Any]:
    value = case.get("input")
    if not isinstance(value, str) or len(value) < 2:
        return case
    candidate = value
    changed = True
    while changed:
        changed = False
        for index in range(len(candidate)):
            trial = candidate[:index] + candidate[index + 1 :]
            trial_case = {**case, "input": trial}
            mismatch, _, _ = differs(oracle, rust, trial_case)
            if mismatch:
                candidate = trial
                changed = True
                break
    return {**case, "input": candidate}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--max-divergences", type=int, default=20)
    parser.add_argument("--log", default=str(ROOT / "fuzz" / "log.txt"))
    parser.add_argument("--upstream", default=str(ROOT / ".upstream" / "price-parser"))
    parser.add_argument("--rust-bin", default=str(ROOT / "target" / "release" / "price-parser"))
    args = parser.parse_args()

    upstream = Path(args.upstream)
    rust_bin = Path(args.rust_bin)
    if not upstream.exists():
        raise SystemExit("Pinned upstream checkout missing; run make bootstrap-upstream")
    if not rust_bin.exists():
        raise SystemExit("Rust binary missing; run cargo build --release --bin price-parser")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(upstream)
    oracle = JsonlProcess.start([sys.executable, str(ROOT / "fuzz" / "oracle_server.py")], env)
    rust = JsonlProcess.start([str(rust_bin), "--jsonl"])
    rng = random.Random(args.seed)
    started = time.monotonic()
    cases = 0
    divergences: list[dict[str, Any]] = []

    try:
        while time.monotonic() - started < args.duration:
            case = generate(rng)
            mismatch, expected, actual = differs(oracle, rust, case)
            cases += 1
            if mismatch:
                minimized = minimize(oracle, rust, case)
                _, min_expected, min_actual = differs(oracle, rust, minimized)
                divergences.append(
                    {
                        "case": case,
                        "expected": expected,
                        "actual": actual,
                        "minimized_case": minimized,
                        "minimized_expected": min_expected,
                        "minimized_actual": min_actual,
                    }
                )
                if len(divergences) >= args.max_divergences:
                    break
    finally:
        oracle.close()
        rust.close()

    report = {
        "seed": args.seed,
        "requested_duration_seconds": args.duration,
        "actual_duration_seconds": round(time.monotonic() - started, 3),
        "cases": cases,
        "divergence_count": len(divergences),
        "divergences": divergences,
    }
    Path(args.log).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "divergences"}, indent=2))
    return 1 if divergences else 0


if __name__ == "__main__":
    raise SystemExit(main())
