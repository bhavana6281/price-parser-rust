#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
[ -d .upstream/price-parser ] || ./tools/bootstrap_upstream.sh
[ -f bench/corpus.jsonl ] || python3 bench/generate_corpus.py
[ -x target/release/price-parser ] || cargo build --release --bin price-parser
python3 bench/run.py
python3 bench/cold_start.py
./bench/rss.sh
python3 bench/summarize.py
