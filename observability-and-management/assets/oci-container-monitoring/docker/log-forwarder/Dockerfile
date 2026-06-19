# Log Forwarder Sidecar Container
# Forwards container logs from shared volumes to OCI Logging service

FROM oraclelinux:8-slim

# Metadata
LABEL maintainer="DevSecOps Team"
LABEL description="Log Forwarder Sidecar for OCI Logging"
LABEL version="1.0.0"

# Install required packages and build dependencies
RUN microdnf update -y && \
    microdnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        libffi-devel \
        openssl-devel \
        curl \
        jq && \
    microdnf clean all

# Upgrade pip and install OCI Python SDK
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    oci \
    watchdog \
    python-json-logger

# Create directories
RUN mkdir -p /app /logs /metrics

# Copy log forwarder script
COPY log-forwarder.py /app/
COPY config.json.template /app/

# Make script executable
RUN chmod +x /app/log-forwarder.py

# Set working directory
WORKDIR /app

# Environment variables
ENV LOG_MOUNT_PATH="/logs" \
    LOG_FILE="application.log" \
    LOG_OCID="" \
    LOG_HEADER="" \
    PYTHON_UNBUFFERED=1

# Volumes
VOLUME ["/logs", "/metrics"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Run log forwarder
CMD ["python3", "/app/log-forwarder.py"]
