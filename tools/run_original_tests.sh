#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if [ ! -f tests/original/test_price_parsing.py ]; then
    echo "Original tests are missing; run make bootstrap-upstream" >&2
    exit 1
fi

cargo build --release --bin price-parser
./tools/verify_original_hashes.sh
mkdir -p artifacts

set +e
PYTHONPATH="$ROOT/python_compat" \
PRICE_PARSER_RUST_BIN="$ROOT/target/release/price-parser" \
python3 -m pytest -q \
    --junitxml="$ROOT/artifacts/original-tests.xml" \
    tests/original/test_price_parsing.py "$@"
STATUS=$?
set -e

python3 tools/summarize_junit.py \
    artifacts/original-tests.xml \
    --output artifacts/original-tests.json
exit "$STATUS"
