# Architectural decisions and migration log

This log records observable divergences and the reasoning behind them. The
behavioral reference is `scrapinghub/price-parser` commit `ea535c0`.

## 1. Decimal values use `rust_decimal::Decimal`

Python returns `decimal.Decimal`, including meaningful scale such as
`Decimal("140.000")`. Binary floating point would lose that representation and
introduce rounding differences. The Rust public model therefore stores
`Option<Decimal>` and the JSON protocol transmits decimal strings.

## 2. The parser is a standalone Rust library

All currency, extraction, separator, and number logic lives in `src/`. The
production artifact does not embed Python, invoke Python, or link to CPython.

## 3. The Python layer is a test adapter, not the implementation

The untouched upstream tests import `price_parser.Price`. The adapter preserves
that interface and sends JSONL requests to the Rust binary. It converts returned
decimal strings to Python `Decimal`; it contains no parsing decisions.

## 4. The original five-function contract is preserved

The Rust library exposes equivalents of `extract_currency_symbol`,
`extract_price_text`, `get_decimal_separator`, `parse_number`, and `parse_price`.
This makes parity failures attributable to one stage instead of a monolithic
translation.

## 5. Parse options are explicit

`ParseOptions` models `currency_hint`, `decimal_separator`, and
`digit_group_separator`. `parse_price` accepts `Option<&str>` so Python `None`
remains distinct from an empty string.

## 6. Regexes are compiled once

The Python module compiles its expressions at import. Rust uses
`once_cell::sync::Lazy`, avoiding compilation on every parse while retaining a
clear correspondence with the original expressions.

## 7. Euro conditional regex behavior is explicit

The Python implementation uses a conditional regex feature unavailable in
Rust's linear-time `regex` crate. The port uses separate spaced and unspaced euro
patterns and then joins captures. This avoids a backtracking regex engine while
preserving cases such as `35€ 99`, `35€ 999`, and `1,235€99`.

## 8. Currency search is ordered, not hash-based

Currency choice is observable. Dollar ISO codes beat `$`; the main price beats
the hint; safe symbols beat the wider symbol set. Ordered slices and earliest-
position matching replace the initial port's nondeterministic `HashSet`
iteration.

## 9. Currency data is generated from the pinned upstream source

`tools/generate_currency_data.py` imports the exact pinned `_currencies.py` and
writes committed Rust arrays. The generated file currently contains 208 codes
and 300 non-safe symbols. The safe-symbol list is emitted in its original order because regex-alternative
precedence is observable. CI regenerates the file and
fails if committed output is stale.

## 10. Unicode whitespace is normalized before extraction

Python's `re.sub(r"\s+", " ", value)` handles non-breaking and repeated
whitespace. Rust performs a Unicode-aware single pass before applying extraction
patterns.

## 11. Apostrophes are removed only from extracted amount text

The original accepts values such as `CHF 1'049,95` and returns amount text
`1049,95`. The port mirrors that stage rather than globally rewriting the input,
which could affect currency matching.

## 12. JSONL is the common proof boundary

A persistent line-delimited protocol lets original tests, fuzzing, and
benchmarks exercise the same release binary without measuring a process spawn
per case. Both Python and Rust benchmark targets use the same protocol.

## 13. First-party unsafe code is prohibited

The crate root contains `#![forbid(unsafe_code)]`. Dependency unsafe usage is
reported separately and must not be represented as first-party code.

## 14. Performance claims require generated evidence

The repository ships a benchmark runner and an explicit `not_run` result rather
than fabricated numbers. README claims may be updated only from a committed
corpus, raw methodology, and submission-machine results.

## 15. Known numeric range difference is measured honestly

Python `Decimal` is arbitrary precision; `rust_decimal` has a bounded 96-bit
coefficient. The upstream corpus fits this representation. Differential fuzzing
must retain any overflow divergence, and the final report must document it
instead of silently truncating values.
