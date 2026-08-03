#!/usr/bin/env python3
"""Generate Rust currency constants from the pinned upstream data file."""
from __future__ import annotations

import importlib.util
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "upstream_currencies.py"
TARGET = ROOT / "src" / "currency_data.rs"

# Must stay byte-for-byte semantically aligned with SAFE_CURRENCY_SYMBOLS in
# scrapinghub/price-parser parser.py at kickoff commit ea535c0.
SAFE = [
    "Bds$", "CUC$", "MOP$", "AR$", "AU$", "BN$", "BZ$", "CA$", "CL$", "CO$",
    "CV$", "HK$", "MX$", "NT$", "NZ$", "TT$", "RD$", "WS$", "US$", "$U", "C$",
    "J$", "N$", "R$", "S$", "T$", "Z$", "A$", "SY£", "LB£", "CN¥", "GH₵",
    "$", "€", "£", "zł", "Zł", "Kč", "₽", "¥", "￥", "฿", "դր.", "դր", "₦",
    "₴", "₱", "৳", "₭", "₪", "﷼", "៛", "₩", "₫", "₡", "টকা", "ƒ", "₲", "؋",
    "₮", "नेरू", "₨", "₶", "₾", "֏", "ރ", "৲", "૱", "௹", "₠", "₢", "₣", "₤",
    "₧", "₯", "₰", "₳", "₷", "₸", "₹", "₺", "₼", "₾", "₿", "ℳ", "ر.ق.\u200f",
    "د.ك.\u200f", "د.ع.\u200f", "ر.ع.\u200f", "ر.ي.\u200f", "ر.س.\u200f", "د.ج.\u200f",
    "د.م.\u200f", "د.إ.\u200f", "د.ت.\u200f", "د.ل.\u200f", "ل.س.\u200f", "د.ب.\u200f",
    "د.أ.\u200f", "ج.م.\u200f", "ل.ل.\u200f", " تومان", "تومان", "درهم", "ريال", "جنيه",
    "EUR", "euro", "eur", "CHF", "DKK", "Rp", "lei", "руб.", "руб", "грн.", "грн",
    "дин.", "Dinara", "динар", "лв.", "лв", "р.", "тңг", "тңг.", "ман.",
]


def load_source():
    spec = importlib.util.spec_from_file_location("upstream_currencies", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'


def emit_array(name: str, values: list[str]) -> str:
    lines = [f"pub static {name}: &[&str] = &["]
    lines.extend(f"    {rust_string(value)}," for value in values)
    lines.append("];\n")
    return "\n".join(lines)


def main() -> None:
    module = load_source()
    codes = list(module.CURRENCY_CODES)
    symbols = set(module.CURRENCY_SYMBOLS) | set(module.CURRENCY_NATIONAL_SYMBOLS) | {"р", "Р"}
    other = symbols | set(codes)
    other -= set(SAFE)
    other -= {"-", "XXX"}
    other -= set(string.ascii_uppercase)
    # The Python implementation sorts only by length. A lexical tiebreak makes
    # generated output reproducible without changing longest-match behavior.
    other_sorted = sorted(other, key=lambda value: (-len(value), value))

    content = """//! Generated from tools/upstream_currencies.py.\n//! Source commit: scrapinghub/price-parser ea535c0.\n//! Do not edit by hand; run `python3 tools/generate_currency_data.py`.\n\n"""
    content += emit_array("SAFE_CURRENCY_SYMBOLS", SAFE)
    content += emit_array("CURRENCY_CODES", codes)
    content += emit_array("OTHER_CURRENCY_SYMBOLS", other_sorted)
    TARGET.write_text(content, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}: {len(codes)} codes, {len(other_sorted)} other symbols")


if __name__ == "__main__":
    main()
