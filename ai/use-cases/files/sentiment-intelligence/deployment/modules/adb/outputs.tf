output "adb_id" {
  description = "OCID of the Autonomous Database"
  value       = oci_database_autonomous_database.adb.id
}

output "connection_string" {
  description = "Connection string for the Autonomous Database"
  value       = oci_database_autonomous_database.adb.connection_strings[0].profiles[0].value
}

output "connection_urls" {
  description = "Connection URLs for the Autonomous Database"
  value       = oci_database_autonomous_database.adb.connection_urls
}

output "db_name" {
  description = "Database name"
  value       = oci_database_autonomous_database.adb.db_name
}

output "wallet_content" {
  description = "Base64-encoded ADB wallet"
  value       = oci_database_autonomous_database_wallet.wallet.content
  sensitive   = true
}
