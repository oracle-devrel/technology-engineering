# Sample Application with Prometheus Metrics
# Nginx-based app that exposes Prometheus metrics

FROM nginx:alpine

# Metadata
LABEL maintainer="DevSecOps Team"
LABEL description="Sample Application with Prometheus Metrics"
LABEL version="1.0.0"

# Install additional tools
RUN apk add --no-cache curl bash

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy application files
COPY html/ /usr/share/nginx/html/

# Create stub_status endpoint for nginx metrics
RUN mkdir -p /usr/share/nginx/html/stub_status

# Create directories for shared volumes
RUN mkdir -p /metrics /logs

# Copy metrics generator script (simulates application metrics)
COPY generate-metrics.sh /usr/local/bin/generate-metrics.sh
RUN chmod +x /usr/local/bin/generate-metrics.sh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Volumes
VOLUME ["/metrics", "/logs"]

# Expose ports
EXPOSE 80 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
