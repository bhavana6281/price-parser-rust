#!/usr/bin/env python3
"""Parse a committed corpus in one Python process for peak-RSS measurement."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from price_parser import Price

corpus = Path(sys.argv[1])
count = 0
for line in corpus.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    request = json.loads(line)
    Price.fromstring(
        request.get("input"),
        request.get("currency_hint"),
        request.get("decimal_separator"),
        request.get("digit_group_separator"),
    )
    count += 1
print(count)
