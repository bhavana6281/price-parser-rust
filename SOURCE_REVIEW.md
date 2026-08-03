# Initial repository review

The starting repository was reconstructed from the public `main` branch of
`AshokGadde/price-parser-rust` because direct `git clone` was unavailable in the
analysis environment. The following high-impact issues were addressed in this
working copy:

- Replaced seven-case JSON parity claims with an untouched-test bootstrap.
- Replaced the fixed-input pseudo-fuzzer with Python-vs-Rust differential testing.
- Added the missing standalone CLI artifact.
- Added currency hints and explicit separator options.
- Fixed `Free`, percentage, apostrophe, leading-decimal, and euro-decimal cases.
- Replaced per-call regex construction with lazy statics.
- Replaced nondeterministic currency `HashSet` selection with ordered precedence.
- Generated the complete currency table from the exact pinned upstream source.
- Fixed the Rust edition/Docker mismatch.
- Added reproducible benchmark inputs instead of unsupported performance claims.
- Added CI, hash verification, honest status language, and submission gates.
