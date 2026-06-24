# ─────────────────────────────────────────────────────────────
# outputs.tf – Values needed by the bridge and for validation
# ─────────────────────────────────────────────────────────────

output "stream_pool_id" {
  description = "OCID of the Stream Pool"
  value       = oci_streaming_stream_pool.gcp_pool.id
}

output "stream_id" {
  description = "OCID of the Stream (use as OCI_STREAM_OCID)"
  value       = oci_streaming_stream.gcp_stream.id
}

output "stream_messaging_endpoint" {
  description = "Stream messaging endpoint URL (use as OCI_MESSAGE_ENDPOINT)"
  value       = oci_streaming_stream.gcp_stream.messages_endpoint
}

output "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers for the Fluentd bridge path"
  value       = oci_streaming_stream_pool.gcp_pool.kafka_settings[0].bootstrap_servers
}

output "log_group_id" {
  description = "OCID of the Log Analytics log group"
  value       = oci_log_analytics_log_analytics_log_group.gcp_logs.id
}

output "log_analytics_namespace" {
  description = "Log Analytics namespace"
  value       = local.la_namespace
}

output "service_connector_id" {
  description = "OCID of the Connector Hub"
  value       = oci_sch_service_connector.gcp_bridge.id
}

output "env_local_snippet" {
  description = "Ready-to-paste values for .env.local"
  value = <<-EOT
    OCI_STREAM_OCID=${oci_streaming_stream.gcp_stream.id}
    OCI_STREAM_POOL_ID=${oci_streaming_stream_pool.gcp_pool.id}
    OCI_MESSAGE_ENDPOINT=${oci_streaming_stream.gcp_stream.messages_endpoint}
    OCI_LOG_ANALYTICS_NAMESPACE=${local.la_namespace}
  EOT
}
