# OCI Management Agent Sidecar Container
# This container runs the OCI Management Agent with Prometheus plugin
# to collect metrics from local Prometheus endpoints and send to OCI Monitoring

FROM container-registry.oracle.com/os/oraclelinux:8

# Metadata
LABEL maintainer="DevSecOps Team"
LABEL description="OCI Management Agent Sidecar with Prometheus Plugin"
LABEL version="1.0.0"

# Install required packages for Management Agent
RUN yum update -y && \
    yum install -y \
    java-11-openjdk-headless \
    wget \
    curl \
    unzip \
    cpio \
    procps-ng \
    net-tools \
    openssl \
    sudo \
    hostname \
    && yum clean all \
    && rm -rf /var/cache/yum

# Create agent directory
RUN mkdir -p /opt/oracle/mgmt_agent /metrics /logs

# Download Management Agent (will be replaced with actual installation during container startup)
# The agent will be installed at runtime using the install key

# Create startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create Prometheus plugin configuration template
COPY prometheus-plugin-config.json.template /opt/oracle/prometheus-plugin-config.json.template

# Environment variables (will be overridden at runtime)
ENV MGMT_AGENT_INSTALL_KEY="" \
    OCI_REGION="us-ashburn-1" \
    PROMETHEUS_SCRAPE_INTERVAL="60s" \
    PROMETHEUS_SCRAPE_TIMEOUT="30s" \
    METRICS_NAMESPACE="container_monitoring"

# Volumes
VOLUME ["/metrics", "/logs", "/opt/oracle/mgmt_agent"]

# Expose no ports (internal communication only)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD /opt/oracle/mgmt_agent/agent_inst/bin/agentcore status || exit 1

# Run as oracle user (will be created by agent installation)
# USER oracle

ENTRYPOINT ["/entrypoint.sh"]
CMD ["agent"]
