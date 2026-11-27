FROM rust:1.88-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends libhdf5-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# The crates are part of the image as the solution is built and run without network access (cargo build --offline)
ENV CARGO_HOME=/opt/cargo
RUN cargo new /tmp/prefetch && cd /tmp/prefetch \
    && cargo add hdf5-metno@0.10 ndarray@0.16 rayon@1 serde_json@1 \
    && cargo build --release && rm -rf /tmp/prefetch \
    && chmod -R a+rwX /opt/cargo

COPY . /baseline
RUN cd /baseline && cargo build --release --offline && cp target/release/sisap2026 /usr/local/bin/sisap2026
