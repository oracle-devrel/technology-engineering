output "database_management_not_enabled_warning" {
  description = "Warning emitted when the selection contains no Database Management managed databases. Tag-selected native Database Service alarms, event rules, and notification channels are still created for matching database resources."
  value = length(local.managed_targets) == 0 ? (
    "WARNING: No Database Management managed databases matched the selection. The following Database Management alerts were not created: ${join(", ", local.database_management_alerts)}. Native Database Service alarms, event rules, and notification channels were created only for matching database-service targets."
  ) : null
}

output "ops_insights_not_enabled_warnings" {
  description = "Per-database warnings listing Operations Insights alerts and reports not created because the Database Insight is not enabled."
  value = {
    for database_id, database in local.targets : database_id => "WARNING: Ops Insights is not enabled for ${database.display_name}. The following alerts or reports were not created: ${join(", ", local.ops_insights_alerts)}."
    if !contains(keys(local.opsi_enabled_targets), database_id)
  }
}

output "log_analytics_not_enabled_warnings" {
  description = "Per-database warnings listing Log Analytics alerts not created because the target has no active, associated Log Analytics entity."
  value = {
    for database_id, database in local.targets : database_id => "WARNING: Log Analytics is not enabled or has no active associated entity for ${database.display_name}. The following alerts were not created: ${join(", ", local.log_analytics_alerts)}."
    if !contains(keys(local.log_analytics_targets), database_id)
  }
}

output "selected_managed_databases" {
  description = "Managed database resources that passed the Database Management enablement check."
  value = {
    for id, database in local.managed_targets : id => {
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

output "operations_notification_topic_ids" {
  description = "OCI Notifications topics used for Backup Failure operational alerts, including matching existing topics that Terraform reuses."
  value       = local.operations_notification_topic_ids
}

output "database_service_critical_event_rule_ids" {
  description = "OCI Events rules that route critical events for each selected database resource to the Notifications topic."
  value       = { for database_id, rule in oci_events_rule.database_service_critical : database_id => rule.id }
}

output "database_backup_failure_event_rule_ids" {
  description = "Database Service backup-failure event rules for selected database resources, routed to db-prod-operations without requiring Database Management."
  value       = { for database_id, rule in oci_events_rule.database_backup_failure : database_id => rule.id }
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
      database_management = contains(keys(local.managed_targets), database_id) ? "ENABLED" : "NOT ENABLED - no Database Management alarm created"
      ops_insights        = contains(keys(local.opsi_enabled_targets), database_id) ? "ENABLED" : "NOT ENABLED - no Ops Insights report created"
      log_analytics       = contains(keys(local.log_analytics_targets), database_id) ? "ENABLED" : "NOT ENABLED OR NO ACTIVE ENTITY/SOURCE - no Log Analytics alert created"
      alerts_not_created = concat(
        contains(keys(local.managed_targets), database_id) ? [] : local.database_management_alerts,
        contains(keys(local.opsi_enabled_targets), database_id) ? [] : local.ops_insights_alerts,
        contains(keys(local.log_analytics_targets), database_id) ? [] : local.log_analytics_alerts,
      )
    }
  }
}

output "database_service_metric_alarm_ids" {
  description = "Native Database Service metric alarms created from the oci_database, oci_database_cluster, and oci_autonomous_database namespaces."
  value       = { for key, alarm in oci_monitoring_alarm.database_service_metrics : key => alarm.id }
}

output "ops_insights_news_report_ids" {
  description = "Weekly Ops Insights News Reports created only in compartments with an enabled selected Database Insight."
  value       = { for compartment_id, report in oci_opsi_news_report.weekly_capacity : compartment_id => report.id }
}

output "ops_insights_daily_sql_degradation_report_ids" {
  description = "Daily Operations Insights SQL performance-degradation News Reports routed to db-prod-operations."
  value       = { for compartment_id, report in oci_opsi_news_report.daily_sql_degradation : compartment_id => report.id }
}

output "log_analytics_alert_database_ids" {
  description = "Selected database IDs for which Log Analytics detection rules and critical alarms were created."
  value       = keys(oci_monitoring_alarm.log_analytics_critical_event)
}
