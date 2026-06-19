# Prometheus Sidecar Container
# Aggregates metrics from multiple sources and exposes unified endpoint

FROM prom/prometheus:latest

# Metadata
LABEL maintainer="DevSecOps Team"
LABEL description="Prometheus Sidecar for Metrics Aggregation"
LABEL version="1.0.0"

# Copy custom Prometheus configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Switch to root to create directories
USER root

# Create directories for shared volumes
RUN mkdir -p /metrics /logs && \
    chown -R nobody:nobody /metrics /logs && \
    chmod 755 /metrics /logs

# Volumes
VOLUME ["/metrics", "/logs", "/prometheus"]

# Expose Prometheus port
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1

# Run as prometheus user
USER nobody

ENTRYPOINT ["/bin/prometheus"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--web.enable-lifecycle"]
