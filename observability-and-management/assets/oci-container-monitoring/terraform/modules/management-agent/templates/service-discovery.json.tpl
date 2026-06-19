{
  "version": "1.0",
  "type": "oci_container_instance",
  "service_discovery": {
    "container_instance": {
      "ocid": "${container_instance_id}",
      "private_ip": "${container_ip}",
      "metrics_port": ${metrics_port},
      "compartment_ocid": "${compartment_ocid}"
    },
    "targets": [
      {
        "target": "${container_ip}:${metrics_port}",
        "labels": {
          "job": "container-metrics",
          "instance": "${container_instance_id}",
          "environment": "production"
        }
      }
    ],
    "scrape_config": {
      "interval": "60s",
      "timeout": "10s",
      "metrics_path": "/metrics"
    }
  }
}
