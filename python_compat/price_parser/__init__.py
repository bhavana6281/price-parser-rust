"""Test-only Python compatibility surface for the Rust port.

This module intentionally contains no parsing logic. It forwards requests to the
standalone Rust JSONL process so the untouched upstream Python tests can exercise
the port through the original public API.
"""

from __future__ import annotations

import atexit
import json
import os
import subprocess
import threading
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional


class _RustClient:
    def __init__(self) -> None:
        configured = os.environ.get("PRICE_PARSER_RUST_BIN")
        binary = Path(configured) if configured else Path("target/release/price-parser")
        if not binary.exists():
            raise RuntimeError(
                f"Rust binary not found at {binary}. Run `cargo build --release --bin price-parser`."
            )
        self._process = subprocess.Popen(
            [str(binary), "--jsonl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._lock = threading.Lock()
        atexit.register(self.close)

    def parse(self, payload: dict[str, object]) -> dict[str, object]:
        if self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("Rust parser process has no pipes")
        with self._lock:
            self._process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._process.stdin.flush()
            line = self._process.stdout.readline()
        if not line:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            raise RuntimeError(f"Rust parser process exited unexpectedly: {stderr}")
        response = json.loads(line)
        if not response.get("ok"):
            raise ValueError(response.get("error", "unknown Rust parser error"))
        result = response["result"]
        assert isinstance(result, dict)
        return result

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()


_CLIENT: _RustClient | None = None
_CLIENT_LOCK = threading.Lock()


def _client() -> _RustClient:
    global _CLIENT
    with _CLIENT_LOCK:
        if _CLIENT is None:
            _CLIENT = _RustClient()
        return _CLIENT


@dataclass
class Price:
    amount: Optional[Decimal]
    currency: Optional[str]
    amount_text: Optional[str]

    @property
    def amount_float(self) -> Optional[float]:
        return float(self.amount) if self.amount is not None else None

    @classmethod
    def fromstring(
        cls,
        price: Optional[str],
        currency_hint: Optional[str] = None,
        decimal_separator: Optional[str] = None,
        digit_group_separator: Optional[str] = None,
    ) -> "Price":
        result = _client().parse(
            {
                "input": price,
                "currency_hint": currency_hint,
                "decimal_separator": decimal_separator,
                "digit_group_separator": digit_group_separator,
            }
        )
        amount_raw = result.get("amount")
        amount = Decimal(str(amount_raw)) if amount_raw is not None else None
        return cls(
            amount=amount,
            currency=result.get("currency"),
            amount_text=result.get("amount_text"),
        )


parse_price = Price.fromstring

__all__ = ["Price", "parse_price"]
