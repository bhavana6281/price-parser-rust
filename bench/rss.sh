#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
UPSTREAM=${UPSTREAM:-"$ROOT/.upstream/price-parser"}
RUST_BIN=${PRICE_PARSER_RUST_BIN:-"$ROOT/target/release/price-parser"}
CORPUS=${CORPUS:-"$ROOT/bench/corpus.jsonl"}
TIME_BIN=${TIME_BIN:-/usr/bin/time}

if [ ! -x "$TIME_BIN" ]; then
    echo "GNU time not found at $TIME_BIN" >&2
    exit 1
fi

PY_RSS=$(mktemp)
RS_RSS=$(mktemp)
trap 'rm -f "$PY_RSS" "$RS_RSS"' EXIT

PYTHONPATH="$UPSTREAM" "$TIME_BIN" -f '%M' -o "$PY_RSS" \
    python3 "$ROOT/bench/python_batch.py" "$CORPUS" >/dev/null
"$TIME_BIN" -f '%M' -o "$RS_RSS" \
    "$RUST_BIN" --jsonl < "$CORPUS" >/dev/null

python3 - "$PY_RSS" "$RS_RSS" "$ROOT/bench/rss.json" <<'PY'
import json, sys
from pathlib import Path
python_kib = int(Path(sys.argv[1]).read_text().strip())
rust_kib = int(Path(sys.argv[2]).read_text().strip())
report = {
    "methodology": "GNU time maximum resident set size over one full committed-corpus pass; values are KiB on Linux.",
    "python_peak_rss_kib": python_kib,
    "rust_peak_rss_kib": rust_kib,
    "reduction_fraction": 1 - rust_kib / python_kib if python_kib else None,
}
Path(sys.argv[3]).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
PY
