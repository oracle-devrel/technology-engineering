#!/bin/bash
# Generates sample Prometheus metrics for the application

METRICS_FILE="/metrics/app_metrics.prom"

while true; do
    cat > $METRICS_FILE <<EOF
# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
app_requests_total{method="GET",status="200"} $(( RANDOM % 1000 + 1000 ))
app_requests_total{method="POST",status="200"} $(( RANDOM % 500 + 500 ))
app_requests_total{method="GET",status="404"} $(( RANDOM % 50 ))

# HELP app_request_duration_seconds Request duration in seconds
# TYPE app_request_duration_seconds histogram
app_request_duration_seconds_sum $(( RANDOM % 100 + 50 ))
app_request_duration_seconds_count $(( RANDOM % 1000 + 500 ))

# HELP app_active_connections Current active connections
# TYPE app_active_connections gauge
app_active_connections $(( RANDOM % 100 + 10 ))
EOF
    sleep 15
done
