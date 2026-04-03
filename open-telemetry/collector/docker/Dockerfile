FROM debian:13-slim

ARG OTEL_COL_VERSION=0.148.0

RUN apt update && \
    apt install -y systemd wget vim curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTEL_COL_VERSION}/otelcol-contrib_${OTEL_COL_VERSION}_linux_amd64.tar.gz" && \
    tar -xzf "otelcol-contrib_${OTEL_COL_VERSION}_linux_amd64.tar.gz" && rm -f "otelcol-contrib_${OTEL_COL_VERSION}_linux_amd64.tar.gz"

COPY config.yml /etc/otelcol-contrib/config.yml

ENTRYPOINT ["/otelcol-contrib"]
CMD ["--config", "/etc/otelcol-contrib/config.yml"]

EXPOSE 4317 4318 55679
