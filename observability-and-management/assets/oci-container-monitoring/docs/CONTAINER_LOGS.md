# Container Instance Logging Guide

## Overview

OCI Container Instances provide logs through the **Container Instance API**, not through the standard OCI Logging service. This document explains how to retrieve and monitor container logs.

## Retrieving Container Logs

### Using OCI CLI

```bash
# Get logs from a specific container
oci container-instances container retrieve-logs \
  --container-id <container-ocid>

# With time filters
oci container-instances container retrieve-logs \
  --container-id <container-ocid> \
  --time-start "2025-10-27T00:00:00Z" \
  --time-end "2025-10-27T23:59:59Z"

# Stream logs (tail -f equivalent)
oci container-instances container retrieve-logs \
  --container-id <container-ocid> \
  --is-follow true
```

### Using Terraform Data Source

```hcl
data "oci_container_instances_container" "app_container" {
  container_id = var.container_id
}

# Access logs via API calls in your automation
```

## Log Types Available

1. **stdout** - Standard output from the container
2. **stderr** - Standard error from the container

## Monitoring and Alerting

### Native Container Instance Metrics

OCI Container Instances automatically provide these metrics in OCI Monitoring:

- `CpuUtilization` - CPU usage percentage
- `MemoryUtilization` - Memory usage percentage
- `NetworkBytesIn` - Network ingress
- `NetworkBytesOut` - Network egress

### Custom Application Metrics

Use the Management Agent sidecar pattern to collect custom Prometheus metrics:

1. **Application Container**: Exposes Prometheus metrics on `/metrics`
2. **Agent Sidecar**: Scrapes and forwards to OCI Monitoring

## Log Analytics Integration (Optional)

For advanced log analysis, you can:

1. Enable **Log Analytics** service (separate from Logging)
2. Use custom scripts to forward container logs to Log Analytics
3. Configure IAM policies for Log Analytics access

### Required IAM Policy for Log Analytics

```hcl
Allow dynamic-group <your-dg> to use log-analytics in compartment <compartment-name>
```

## Best Practices

1. **Use structured logging** (JSON format) in your containers
2. **Set appropriate log retention** in your application
3. **Monitor container restarts** via OCI Monitoring metrics
4. **Implement health checks** to detect issues early
5. **Use labels and tags** for log organization

## Automation Script

Create a helper script to fetch and display logs:

```bash
#!/bin/bash
# fetch-container-logs.sh

CONTAINER_INSTANCE_ID="$1"

# Get all container IDs
CONTAINER_IDS=$(oci container-instances container list \
  --container-instance-id "$CONTAINER_INSTANCE_ID" \
  --compartment-id "$OCI_COMPARTMENT_OCID" \
  --query 'data[*].id' \
  --raw-output)

# Fetch logs from each container
for CONTAINER_ID in $CONTAINER_IDS; do
  CONTAINER_NAME=$(oci container-instances container get \
    --container-id "$CONTAINER_ID" \
    --query 'data."display-name"' \
    --raw-output)

  echo "=== Logs from $CONTAINER_NAME ==="
  oci container-instances container retrieve-logs \
    --container-id "$CONTAINER_ID"
  echo ""
done
```

## References

- [Container Instance API - Retrieve Logs](https://docs.oracle.com/en-us/iaas/api/#/en/container-instances/20210415/Container/RetrieveLogs)
- [Container Instance Metrics](https://docs.oracle.com/en-us/iaas/Content/container-instances/container-instance-metrics.htm)
- [Log Analytics IAM Policies](https://docs.oracle.com/en-us/iaas/log-analytics/doc/iam-policies-catalog-logging-analytics.html)
- [Management Agent for Prometheus](https://docs.oracle.com/en-us/iaas/management-agents/doc/set-management-agents-collect-prometheus-metrics.html)
