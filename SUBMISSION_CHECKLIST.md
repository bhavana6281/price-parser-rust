# Submission evidence gate

Record the exact commit beside every result. Do not mark an item complete from a
previous commit.

- [ ] `cargo fmt --check` passes.
- [ ] `cargo clippy --all-targets --all-features -- -D warnings` passes.
- [ ] `cargo test --all-targets` passes.
- [ ] Docker builds from a clean checkout.
- [ ] `tests/original/test_price_parsing.py` is present and unmodified.
- [ ] `tests/original.sha256` verifies.
- [ ] `artifacts/original-tests.json` records exact passed/failed/xfailed counts.
- [ ] Full differential run lasts at least 60 seconds.
- [ ] Fuzz seed, case count, and all divergences are committed.
- [ ] Benchmark corpus hash is committed.
- [ ] Median, p95, p99, throughput, cold startup, and RSS are reported.
- [ ] `rg -n '\bunsafe\b' src` shows no unsafe code other than documentation.
- [ ] At least ten substantive decisions remain in `DECISIONS.md`.
- [ ] Five-minute demo reproduces tests, fuzzing, and one benchmark command.

## Final numbers

```text
Submission commit:
Upstream commit: ea535c0
Original tests passed:
Original tests failed:
Original tests xfailed:
Original-test pass rate:
Differential duration:
Differential cases:
Differential divergences:
First-party unsafe blocks: 0
Cold startup Python / Rust:
Median latency Python / Rust:
p99 latency Python / Rust:
Peak RSS Python / Rust:
```
