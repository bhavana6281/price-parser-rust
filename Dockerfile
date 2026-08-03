FROM rust:1.85-slim AS builder
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release --bin price-parser

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/price-parser /usr/local/bin/price-parser
ENTRYPOINT ["price-parser"]
