output "database_management_not_enabled_warning" {
  description = "Warning emitted when the selection contains no Database Management managed databases. The baseline event rule and notification channel are still created when compartment_id is set."
  value = length(local.targets) == 0 ? (
    "WARNING: No Database Management managed databases matched the selection. Database Management metric alarms, Ops Insights reports, and Log Analytics rules were not created. The baseline Database Service critical-event rule and notification channel were created only when compartment_id was set."
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
  description = "OCI Notifications topics used per baseline compartment, including matching existing topics that Terraform reuses."
  value       = local.notification_topic_ids
}

output "reused_notification_topic_ids" {
  description = "Existing active topics with notification_topic_name that Terraform reused instead of creating."
  value       = { for compartment_id, topic in local.existing_notification_topics : compartment_id => topic.topic_id }
}

output "database_service_critical_event_rule_ids" {
  description = "Always-on OCI Events rules that route Database, DB Node, and DB System critical events to the Notifications topic."
  value       = { for compartment_id, rule in oci_events_rule.database_service_critical : compartment_id => rule.id }
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
