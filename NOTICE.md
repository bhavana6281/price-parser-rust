# Attribution

This project is a behavior-focused language port based on the public API,
implementation behavior, currency data, and test suite of
`scrapinghub/price-parser`, pinned at commit `ea535c0`.

The following upstream-derived materials are included:

- `tests/original/test_price_parsing.py`, copied unchanged and hashed;
- `tools/upstream_currencies.py`, copied from the pinned upstream source;
- `src/currency_data.rs`, generated from that pinned currency data;
- algorithmic behavior documented and reimplemented in Rust.

The upstream BSD-3-Clause license is preserved in `LICENSE-UPSTREAM`. The Rust
port's license is in `LICENSE`.
