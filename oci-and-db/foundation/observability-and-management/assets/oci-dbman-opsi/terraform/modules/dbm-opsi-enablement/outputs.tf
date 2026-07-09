output "dbm_feature_ids" {
  description = "Database Management feature-management resource IDs, keyed by target."
  value       = { for k, r in oci_database_management_database_dbm_features_management.dbm : k => r.id }
}

output "named_credential_ids" {
  description = "Named credential OCIDs, keyed by target."
  value       = { for k, r in oci_database_management_named_credential.dbsnmp : k => r.id }
}

output "ops_insights_ids" {
  description = "Operations Insights Database Insight OCIDs, keyed by target."
  value       = { for k, r in oci_opsi_database_insight.insight : k => r.id }
}

output "data_safe_target_ids" {
  description = "Data Safe target-database OCIDs, keyed by target."
  value       = { for k, r in oci_data_safe_target_database.target : k => r.id }
}
