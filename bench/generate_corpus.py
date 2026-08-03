#!/usr/bin/env python3
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "bench" / "corpus.jsonl"
SEED = 20260802
COUNT = 5000

currencies = ["$", "€", "£", "USD", "EUR", "GBP", "CHF", "SGD", "AED", "Kč", "₹", "Rp"]
amounts = ["1", "12.99", "12,99", "1,234.50", "1.234,50", "75 990,00", ".75", "140.000"]
templates = ["{c}{a}", "{a} {c}", "price: {c} {a}", "Now {a} {c}!", "SKU 123 / {c}{a}"]

rng = random.Random(SEED)
with OUTPUT.open("w", encoding="utf-8") as stream:
    for _ in range(COUNT):
        payload = {
            "input": rng.choice(templates).format(c=rng.choice(currencies), a=rng.choice(amounts)),
            "currency_hint": rng.choice([None, None, "USD", "GBP", "EUR"]),
            "decimal_separator": None,
            "digit_group_separator": None,
        }
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

print(f"wrote {COUNT} deterministic cases to {OUTPUT}")
