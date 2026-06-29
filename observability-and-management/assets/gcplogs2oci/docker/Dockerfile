# ─────────────────────────────────────────────────────────────
# Fluentd bridge: GCP Pub/Sub → OCI Streaming (Kafka interface)
#
# Build:
#   docker build -t gcp-oci-bridge:latest docker/
#
# Run locally (test):
#   docker run --rm \
#     -v /path/to/gcp-sa-key.json:/mnt/secrets/gcp-key.json:ro \
#     -e OCI_AUTH_TOKEN="<token>" \
#     gcp-oci-bridge:latest
#
# For OCI Container Instances the secrets are mounted via Vault.
# ─────────────────────────────────────────────────────────────

FROM fluent/fluentd:v1.16-debian-1

USER root

# Build deps for native Ruby gem extensions (Kafka SASL needs libsasl2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ruby-dev \
        libssl-dev \
        libsasl2-dev && \
    rm -rf /var/lib/apt/lists/*

# GCP Pub/Sub input plugin
RUN gem install fluent-plugin-gcloud-pubsub-custom --no-document

# Kafka output plugin (for OCI Streaming)
RUN gem install fluent-plugin-kafka --no-document

# Optional: prevents systemd-related warnings on startup
RUN gem install fluent-plugin-systemd --no-document

# Copy configuration
COPY fluent.conf /fluentd/etc/fluent.conf

USER fluent

CMD ["fluentd", "-c", "/fluentd/etc/fluent.conf"]
