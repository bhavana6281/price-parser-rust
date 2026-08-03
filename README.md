# price-parser-rust

A behavior-focused Rust port of `scrapinghub/price-parser`, built for Port Mortem
Track D: Python to Rust.

The project separates the production implementation from the proof machinery:

- `src/`: standalone Rust library and `price-parser` binary;
- `python_compat/`: test-only bridge preserving the original Python `Price` API;
- `tests/original/`: untouched, pinned upstream test file and SHA-256;
- `fuzz/`: persistent Python-versus-Rust differential harness;
- `bench/`: shared-corpus latency, startup, throughput, and RSS measurements.

Implemented behavior includes:

- currency hints, explicit decimal separators, and digit-group separators;
- ordered currency precedence, including `SGD$` and `NZD$` before `$`;
- generated currency data from the pinned upstream source;
- Unicode whitespace, apostrophe groups, leading decimals, percentages, `Free`,
  and euro-as-decimal cases;
- decimal values represented with `rust_decimal::Decimal` rather than `f64`;
- first-party unsafe code prohibited by `#![forbid(unsafe_code)]`.

## Build and use

```bash
cargo build --release --bin price-parser
./target/release/price-parser 'Běžná cena 75 990,00 Kč'
```

Output:

```json
{
  "amount": "75990.00",
  "currency": "Kč",
  "amount_text": "75 990,00"
}
```

Persistent JSONL mode is the common boundary for tests, fuzzing, and steady-state
benchmarks:

```bash
printf '%s\n' '{"input":"SGD$4.90"}' | \
  ./target/release/price-parser --jsonl
```

## Verification sequence

Install Python test dependencies and pin the upstream oracle:

```bash
python3 -m pip install pytest attrs
make bootstrap-upstream
make verify-test-hashes
```

Run Rust quality checks and tests:

```bash
make test
```

Run the untouched upstream Python test file against the standalone Rust process:

```bash
make test-original
cat artifacts/original-tests.json
```

The pytest JUnit output and machine-readable pass/fail summary are written under
`artifacts/`.

Run the differential harness for at least 60 seconds:

```bash
make fuzz
```

Run the shared-corpus benchmark suite:

```bash
make bench
cat bench/report.json
```

Run the complete correctness gate:

```bash
make verify
```

`RUNBOOK.md` gives the failure-triage order, final benchmark procedure, and
five-minute demo script.

## Docker

```bash
docker build --no-cache -t price-parser-rust .
docker run --rm price-parser-rust '$1,299.95'
```

The final image contains a Rust binary and no Python runtime.

## Repository layout

```text
src/                         Rust library, generated currency data, and CLI
python_compat/price_parser/  test-only original API bridge
tests/original/              pinned untouched test file and recorded hash
tests/api.rs                 focused Rust regressions
artifacts/                    generated original-suite evidence
fuzz/                        Python-vs-Rust differential harness
bench/                       corpus and reproducible measurement scripts
tools/                       pinning, hashing, and data-generation scripts
DECISIONS.md                 architectural divergences and rationale
RUNBOOK.md                   ordered completion and demo procedure
STATUS.md                    completed versus unexecuted validation
SUBMISSION_CHECKLIST.md      evidence gate before making claims
```

## Source and license

Behavior is pinned to `scrapinghub/price-parser` commit `ea535c0`. Currency
constants are generated from the corresponding upstream `_currencies.py`; the
original safe-symbol ordering is preserved in generated output because it is observable.
The original and this port use BSD-3-Clause. See `NOTICE.md` for attribution.
