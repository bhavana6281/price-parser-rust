#!/usr/bin/env python3
"""Persistent JSONL server around the pinned Python oracle."""

from __future__ import annotations

import json
import sys
from price_parser import Price


def normalize(value: Price) -> dict[str, object]:
    return {
        "amount": str(value.amount) if value.amount is not None else None,
        "currency": value.currency,
        "amount_text": value.amount_text,
    }


for raw_line in sys.stdin:
    line = raw_line.strip()
    if not line:
        continue
    try:
        request = json.loads(line)
        result = Price.fromstring(
            request.get("input"),
            request.get("currency_hint"),
            request.get("decimal_separator"),
            request.get("digit_group_separator"),
        )
        response = {"ok": True, "result": normalize(result)}
    except Exception as exc:  # oracle exceptions are part of observable behavior
        response = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(response, ensure_ascii=False), flush=True)
