# Benchmark methodology

All measurements use the same committed `bench/corpus.jsonl`; record its SHA-256
from `bench/results.json` in the final report.

## Steady-state latency and throughput

`bench/run.py` starts one persistent Python oracle process and one persistent
Rust JSONL process. After warmup, it sends identical requests one at a time and
records end-to-end request latency. This intentionally includes the same JSONL
serialization boundary for both implementations while excluding cold startup.
It reports median, p95, p99, total elapsed time, and throughput.

## Cold startup

`bench/cold_start.py` starts a fresh process for each sample and performs one
parse. Python includes interpreter startup and package import; Rust includes
binary startup. Run at least 100 samples and report median, p95, and p99.

## Peak RSS

`bench/rss.sh` uses GNU `/usr/bin/time` on Linux. Python and Rust each parse the
full committed corpus in one process. The result is maximum resident set size in
KiB, saved to `bench/rss.json`.

## Reproduction

```bash
make bootstrap-upstream
make bench
```

`make bench` writes `results.json`, `cold_start.json`, `rss.json`, and the merged
`report.json`. Do not edit generated numbers manually. Record CPU model, OS,
Python version, Rust version, commit SHA, corpus hash, warmup count, and round
count in the submission and demo.
