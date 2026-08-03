.PHONY: build test bootstrap-upstream verify-test-hashes test-original fuzz bench verify clean

build:
	cargo build --release --bin price-parser

test:
	cargo fmt --check
	cargo clippy --all-targets --all-features -- -D warnings
	cargo test --all-targets

bootstrap-upstream:
	./tools/bootstrap_upstream.sh

verify-test-hashes:
	./tools/verify_original_hashes.sh

test-original: build verify-test-hashes
	./tools/run_original_tests.sh

fuzz: build
	python3 fuzz/differential.py --duration 60 --seed 20260802

bench: build
	./bench/run_all.sh

verify: test test-original fuzz

clean:
	cargo clean
	rm -f fuzz/log.txt
