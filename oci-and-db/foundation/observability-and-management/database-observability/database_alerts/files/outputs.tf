output "database_management_not_enabled_warning" {
  description = "Warning emitted instead of creating alarms when the selection contains no Database Management managed databases."
  value = length(local.targets) == 0 ? (
    "WARNING: No Database Management managed databases matched the selection. No notification topic, subscription, or alarms were created. Enable Database Management on the database(s), then apply again."
  ) : null
}

output "selected_managed_databases" {
  description = "Managed database resources that passed the Database Management enablement check."
  value = {
    for id, database in local.targets : id => {
      display_name   = database.display_name
      compartment_id = database.compartment_id
    }
  }
}

output "notification_topic_ids" {
  description = "OCI Notifications topics created per target compartment."
  value       = { for compartment_id, topic in oci_ons_notification_topic.database_alerts : compartment_id => topic.id }
}

output "email_subscription_status" {
  description = "Email subscriptions created for test@acme.com. They remain PENDING until the recipient confirms OCI's email."
  value       = { for compartment_id, subscription in oci_ons_subscription.email : compartment_id => subscription.state }
}

output "service_preflight_report" {
  description = "Per-target service state used to decide whether optional Ops Insights reports and Log Analytics alerts are created. This configuration never enables services."
  value = {
    for database_id, database in local.targets : database_id => {
      database_name       = database.display_name
      database_management = "ENABLED"
      ops_insights        = contains(keys(local.opsi_enabled_targets), database_id) ? "ENABLED" : "NOT ENABLED - no Ops Insights report created"
      log_analytics       = contains(keys(local.log_analytics_targets), database_id) ? "ENABLED" : "NOT ENABLED OR NO ACTIVE ENTITY/SOURCE - no Log Analytics alert created"
    }
  }
}

output "ops_insights_news_report_ids" {
  description = "Weekly Ops Insights News Reports created only in compartments with an enabled selected Database Insight."
  value       = { for compartment_id, report in oci_opsi_news_report.weekly_capacity : compartment_id => report.id }
}

output "log_analytics_alert_database_ids" {
  description = "Selected database IDs for which Log Analytics detection rules and critical alarms were created."
  value       = keys(oci_monitoring_alarm.log_analytics_critical_event)
}
