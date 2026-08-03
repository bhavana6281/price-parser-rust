#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "tests" / "original" / "test_price_parsing.py"
HASH_FILE = ROOT / "tests" / "original.sha256"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["write", "verify"])
    args = parser.parse_args()
    if not TEST_FILE.exists():
        raise SystemExit(f"missing {TEST_FILE}; run make bootstrap-upstream")
    actual = digest(TEST_FILE)
    if args.mode == "write":
        HASH_FILE.write_text(f"{actual}  tests/original/test_price_parsing.py\n")
        print(f"wrote {HASH_FILE}")
        return 0
    if not HASH_FILE.exists():
        raise SystemExit(f"missing {HASH_FILE}; run make bootstrap-upstream")
    expected = HASH_FILE.read_text().split()[0]
    if actual != expected:
        raise SystemExit(f"hash mismatch: expected {expected}, got {actual}")
    print(f"OK {TEST_FILE}: {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
