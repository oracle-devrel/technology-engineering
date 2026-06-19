FROM grafana/grafana:latest

USER root

# Install OCI Logs datasource plugin
RUN grafana-cli plugins install oci-logs-datasource

# Copy provisioning configurations
COPY provisioning/datasources/ /etc/grafana/provisioning/datasources/
COPY provisioning/dashboards/ /etc/grafana/provisioning/dashboards/

# Configure Grafana to use Resource Principal authentication for OCI
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SERVER_HTTP_PORT=3000
ENV GF_PATHS_PROVISIONING=/etc/grafana/provisioning
ENV GF_INSTALL_PLUGINS=oci-logs-datasource

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/api/health || exit 1

USER grafana

EXPOSE 3000
