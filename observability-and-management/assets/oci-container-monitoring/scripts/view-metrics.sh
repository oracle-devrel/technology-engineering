#!/bin/bash
#######################################
# View Container Instance Metrics
# Quick script to query current metrics
#######################################

COMPARTMENT_ID="ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq"
RESOURCE_ID="ocid1.computecontainerinstance.oc1.eu-frankfurt-1.antheljrttkvkkiacab7ipegio4tna7phcxaanhzfxuwxeynbgggdyxtoqmq"

echo "==================================="
echo "Container Instance Metrics"
echo "==================================="
echo ""

# Query CPU Utilization (last 5 minutes)
echo "CPU Utilization (last 5 minutes):"
oci monitoring metric-data summarize-metrics-data \
  --namespace oci_computecontainerinstance \
  --query-text "CpuUtilization[1m].mean()" \
  --compartment-id "$COMPARTMENT_ID" \
  --start-time "$(date -u -v-5M +%Y-%m-%dT%H:%M:%S.000Z)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" \
  --query 'data[0]."aggregated-datapoints"[0].value' \
  --raw-output 2>/dev/null || echo "No data yet"

echo ""

# Query Memory Utilization
echo "Memory Utilization (last 5 minutes):"
oci monitoring metric-data summarize-metrics-data \
  --namespace oci_computecontainerinstance \
  --query-text "MemoryUtilization[1m].mean()" \
  --compartment-id "$COMPARTMENT_ID" \
  --start-time "$(date -u -v-5M +%Y-%m-%dT%H:%M:%S.000Z)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" \
  --query 'data[0]."aggregated-datapoints"[0].value' \
  --raw-output 2>/dev/null || echo "No data yet"

echo ""
echo "==================================="
echo "View all metrics in OCI Console:"
echo "https://cloud.oracle.com/monitoring/metrics"
echo "==================================="
