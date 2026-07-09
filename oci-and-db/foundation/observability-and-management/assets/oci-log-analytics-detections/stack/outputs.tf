output "la_namespace" {
  description = "Log Analytics namespace"
  value       = local.la_namespace
}

output "log_group_id" {
  description = "OCID of the created Log Analytics log group"
  value       = oci_log_analytics_log_analytics_log_group.soc_detection.id
}

output "compartment_id" {
  description = "Target compartment OCID"
  value       = var.compartment_id
}

output "stream_ids" {
  description = "Map of stream name to OCID"
  value       = { for k, v in oci_streaming_stream.soc_detection : k => v.id }
}

output "service_connector_ids" {
  description = "Map of service connector name to OCID"
  value       = { for k, v in oci_sch_service_connector.soc_detection : k => v.id }
}
