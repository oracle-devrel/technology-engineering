#!/bin/bash

# SYNOPSIS: Installs the OpenTelemetry Collector (contrib) on Linux as a systemd
#           service. It scrapes a Prometheus /federate endpoint (or any Prometheus
#           target) and forwards everything as OTEL metrics (OTLP/HTTP) and/or via
#           Prometheus remote_write to the user's collector / Prometheus / Grafana
#           / 3rd-party tool.
# USAGE:    sudo ./install-otel-collector.sh \
#               --prometheus-url http://localhost:9090 \
#               [--otlp-endpoint http://collector:4318] \
#               [--remote-write http://prom:9090/api/v1/write] \
#               [--insecure]

set -e

VERSION="0.154.0"
USER="otelcol"
PROM_URL="http://localhost:9090"
OTLP_ENDPOINT=""
REMOTE_WRITE=""
INSECURE="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prometheus-url) PROM_URL="$2"; shift 2;;
        --otlp-endpoint)  OTLP_ENDPOINT="$2"; shift 2;;
        --remote-write)   REMOTE_WRITE="$2"; shift 2;;
        --insecure)       INSECURE="true"; shift;;
        --version)        VERSION="$2"; shift 2;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

if [ "$EUID" -ne 0 ]; then echo "Please run as root"; exit 1; fi
if [ -z "$OTLP_ENDPOINT" ] && [ -z "$REMOTE_WRITE" ]; then
    echo "Provide at least one of --otlp-endpoint or --remote-write"; exit 1
fi

PROM_HOSTPORT="${PROM_URL#http://}"; PROM_HOSTPORT="${PROM_HOSTPORT#https://}"

echo "Installing OpenTelemetry Collector (contrib) v$VERSION..."
if ! id "$USER" &>/dev/null; then useradd --no-create-home --shell /bin/false "$USER"; fi

ARCH=$(uname -m)
case $ARCH in
    x86_64) BIN_ARCH="amd64" ;;
    aarch64) BIN_ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

URL="https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v$VERSION/otelcol-contrib_${VERSION}_linux_${BIN_ARCH}.tar.gz"
echo "Downloading $URL..."
curl -fL "$URL" -o /tmp/otelcol.tar.gz
mkdir -p /opt/otelcol
tar xzf /tmp/otelcol.tar.gz -C /opt/otelcol otelcol-contrib
chown "$USER":"$USER" /opt/otelcol/otelcol-contrib
rm -f /tmp/otelcol.tar.gz

# Build exporters block
EXPORTERS=""
PIPELINE_EXP=""
if [ -n "$OTLP_ENDPOINT" ]; then
    EXPORTERS+="  otlphttp:
    endpoint: \"$OTLP_ENDPOINT\"
    tls:
      insecure: $INSECURE
"
    PIPELINE_EXP="otlphttp"
fi
if [ -n "$REMOTE_WRITE" ]; then
    EXPORTERS+="  prometheusremotewrite:
    endpoint: \"$REMOTE_WRITE\"
    tls:
      insecure: $INSECURE
"
    [ -n "$PIPELINE_EXP" ] && PIPELINE_EXP="$PIPELINE_EXP, prometheusremotewrite" || PIPELINE_EXP="prometheusremotewrite"
fi

mkdir -p /etc/otelcol
cat > /etc/otelcol/config.yaml <<EOF
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-federate'
          honor_labels: true
          metrics_path: /federate
          params:
            'match[]': ['{job=~".+"}']
          scrape_interval: 30s
          static_configs:
            - targets: ['$PROM_HOSTPORT']
processors:
  batch: {}
exporters:
$EXPORTERS
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      processors: [batch]
      exporters: [$PIPELINE_EXP]
EOF
chown -R "$USER":"$USER" /etc/otelcol

cat > /etc/systemd/system/otelcol.service <<EOF
[Unit]
Description=OpenTelemetry Collector (contrib)
After=network.target

[Service]
User=$USER
Group=$USER
Type=simple
ExecStart=/opt/otelcol/otelcol-contrib --config=/etc/otelcol/config.yaml

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable otelcol
systemctl restart otelcol

echo "OpenTelemetry Collector installed."
echo "  scraping: $PROM_URL/federate"
[ -n "$OTLP_ENDPOINT" ] && echo "  OTLP/HTTP -> $OTLP_ENDPOINT"
[ -n "$REMOTE_WRITE" ] && echo "  remote_write -> $REMOTE_WRITE"
