# Validation status

This file distinguishes completed code changes from evidence that still must be
generated on a machine with Rust and network access.

## Completed in this working copy

- Exact upstream test file pinned at commit `ea535c0` and SHA-256 recorded.
- Full upstream currency data converted into generated Rust constants: 208 codes
  and 300 non-safe symbols, plus the original ordered safe-symbol list.
- Rust library API, standalone JSONL CLI, Python compatibility adapter,
  differential harness, benchmark scripts, JUnit test reporting, Dockerfile, CI, decision log, and
  submission checklist added.
- Python support scripts pass syntax validation.
- A temporary Python model of the Rust algorithm matched all 1,051 non-xfail
  price-example records in the pinned test file. This is a preflight check only,
  not evidence that the Rust code compiles or passes the suite.

## Not executed in this environment

- `cargo fmt`, `cargo clippy`, compilation, and Rust tests.
- Untouched upstream pytest suite against the compiled Rust binary.
- Differential fuzz run.
- Performance and RSS benchmarks.
- Docker build.

Reason: this execution environment had no Rust or Docker toolchain and could not
reach package servers. The first GitHub Actions run or a local Rust installation
must produce the authoritative evidence.
