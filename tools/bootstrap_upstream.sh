#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
UPSTREAM="$ROOT/.upstream/price-parser"
COMMIT="ea535c0"

if [ ! -d "$UPSTREAM/.git" ]; then
    mkdir -p "$ROOT/.upstream"
    git clone https://github.com/scrapinghub/price-parser.git "$UPSTREAM"
fi

git -C "$UPSTREAM" fetch --all --tags

git -C "$UPSTREAM" checkout --detach "$COMMIT"

mkdir -p "$ROOT/tests/original"
cp "$UPSTREAM/tests/test_price_parsing.py" "$ROOT/tests/original/test_price_parsing.py"
python3 "$ROOT/tools/hash_original.py" write

printf 'Pinned upstream at %s\n' "$(git -C "$UPSTREAM" rev-parse HEAD)"
printf 'Original test hash written to tests/original.sha256\n'
