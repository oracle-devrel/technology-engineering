# ─────────────────────────────────────────────────────────────
# outputs.tf – Values needed by the Azure Function and for
#              post-deploy validation
#
# Outputs work regardless of whether resources were created new
# or discovered as existing.
# ─────────────────────────────────────────────────────────────

output "stream_pool_id" {
  description = "OCID of the Stream Pool"
  value       = local.stream_pool_id
}

output "stream_id" {
  description = "OCID of the Stream (use as OCI_STREAM_OCID)"
  value       = local.stream_id
}

output "stream_messaging_endpoint" {
  description = "Stream messaging endpoint URL (use as OCI_MESSAGE_ENDPOINT)"
  value       = local.stream_messages_endpoint
}

output "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers (for alternative Kafka-based integrations)"
  value       = local.kafka_bootstrap_servers
}

output "log_group_id" {
  description = "OCID of the Log Analytics log group"
  value       = local.log_group_id
}

output "log_analytics_namespace" {
  description = "Log Analytics namespace"
  value       = local.la_namespace
}

output "service_connector_id" {
  description = "OCID of the Service Connector Hub"
  value       = local.sch_id
}

output "env_snippet" {
  description = "Ready-to-paste values for .env.local"
  value       = <<-EOT
    OCI_STREAM_OCID=${local.stream_id}
    OCI_STREAM_POOL_ID=${local.stream_pool_id}
    OCI_MESSAGE_ENDPOINT=${local.stream_messages_endpoint}
    OCI_LOG_ANALYTICS_NAMESPACE=${local.la_namespace}
  EOT
}

# ── Discovery Status ──────────────────────────────────────────

output "resources_discovered" {
  description = "Shows which resources were found existing vs created new"
  value = {
    stream_pool = local.create_stream_pool ? "CREATED" : "EXISTING"
    stream      = local.create_stream ? "CREATED" : "EXISTING"
    log_group   = local.create_log_group ? "CREATED" : "EXISTING"
    sch         = local.create_sch ? "CREATED" : "EXISTING"
  }
}
