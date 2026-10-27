output "aws_ingest_bucket" {
  value       = oci_objectstorage_bucket.aws_focus.name
  description = "Private Object Storage bucket receiving AWS FOCUS reports."
}

output "oci_ingest_bucket" {
  value       = oci_objectstorage_bucket.oci_focus.name
  description = "Private Object Storage bucket receiving OCI FOCUS reports."
}

output "log_analytics_log_group_id" {
  value       = oci_log_analytics_log_analytics_log_group.finops.id
  description = "Log Analytics log group for the FOCUS data."
}

output "aws_object_collection_rule_id" {
  value       = oci_log_analytics_log_analytics_object_collection_rule.aws_focus.id
  description = "Live Object Storage collection rule for FOCUS_AWS."
}

output "oci_object_collection_rule_id" {
  value       = oci_log_analytics_log_analytics_object_collection_rule.oci_focus.id
  description = "Live Object Storage collection rule for FOCUS_OCI."
}
