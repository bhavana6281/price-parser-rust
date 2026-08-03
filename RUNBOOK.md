# Completion runbook

Follow these gates in order. Do not optimize or record the demo before the test
suite is stable.

## Gate 1: compile and clean the code

```bash
rustup toolchain install 1.85.0 --component rustfmt clippy
rustup override set 1.85.0
python3 tools/generate_currency_data.py
cargo fmt
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
cargo generate-lockfile
git add Cargo.lock src/currency_data.rs
git commit -m "Make Rust port compile and lock dependencies"
```

Fix compiler errors first. Do not weaken `#![forbid(unsafe_code)]` or remove
assertions to make CI green.

## Gate 2: establish untouched-test parity

```bash
python3 -m pip install pytest attrs
make bootstrap-upstream
make verify-test-hashes
make test-original | tee original-tests.log
```

The pinned file contains 1,051 non-xfail parsing examples, 134 strict-xfail
parsing examples, two `amount_float` cases, and six explicit-separator cases.
Record pytest's actual passed/failed/xfailed totals; do not infer the final score
from those source counts.

For each failure, classify it as one of:

1. currency extraction or precedence;
2. amount-text extraction;
3. decimal-separator inference;
4. numeric conversion or decimal range;
5. compatibility-adapter behavior.

Add a focused Rust regression test before changing implementation code. Keep the
original Python test untouched.

## Gate 3: differential testing

During development:

```bash
cargo build --release --bin price-parser
python3 fuzz/differential.py --duration 10 --seed 20260802
```

For submission:

```bash
python3 fuzz/differential.py \
  --duration 120 \
  --seed 20260802 \
  --max-divergences 100 \
  --log fuzz/log.txt
```

A divergence is not automatically a failure. Minimize it, decide whether it is a
Rust bug, an intentional bounded-decimal difference, or a newly discovered
upstream bug, and document the result in `DECISIONS.md`.

## Gate 4: benchmark only a parity-qualified commit

```bash
make bench
cat bench/report.json
```

Run on an otherwise idle Linux machine. Record the commit, CPU, OS, Python and
Rust versions, corpus SHA-256, warmups, rounds, cold-start p99, steady-state p99,
throughput, and peak RSS. Repeat the complete run at least three times and use a
representative run rather than the best result.

## Gate 5: clean-build rehearsal

```bash
make verify
docker build --no-cache -t price-parser-rust .
docker run --rm price-parser-rust 'SGD$4.90'
rg -n '\bunsafe\b' src
```

Update `SUBMISSION_CHECKLIST.md` and README with the exact generated numbers.

## Five-minute demo order

1. Show the pinned commit and test SHA-256.
2. Run the untouched upstream suite against Rust.
3. Show `#![forbid(unsafe_code)]` and the first-party unsafe search.
4. Run a short differential session and open the published full-run log.
5. Parse three difficult inputs through the standalone binary.
6. Show `bench/report.json` and explain the methodology, including any regression.
7. Open three important entries in `DECISIONS.md` and defend them.
