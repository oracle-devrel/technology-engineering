# Target discovery intentionally searches DbmgmtManagedDatabase resources, rather
# than all Database resources. A result exists only after Database Management has
# been enabled. Database Management metrics are therefore conditional, but the
# baseline Database Service critical-event rule is not.
locals {
  tag_conditions = [
    for key, value in var.tags :
    "(freeformTags.key = '${replace(key, "'", "\\'")}' && freeformTags.value = '${replace(value, "'", "\\'")}')"
  ]

  target_query = var.compartment_id != null ? (
    "query DbmgmtManagedDatabase resources where compartmentId = '${var.compartment_id}'"
    ) : (
    "query DbmgmtManagedDatabase resources where ${join(" && ", local.tag_conditions)}"
  )
}

check "target_selector_is_present" {
  assert {
    condition     = var.compartment_id != null || length(var.tags) > 0
    error_message = "Set compartment_id, or provide at least one tags entry."
  }
}

data "oci_resource_search" "managed_databases" {
  query = local.target_query
}

locals {
  # OCI resource-search is region-scoped. Its identifier is the managed database
  # resource OCID, which is also the resourceId dimension used by these metrics.
  targets = {
    for database in data.oci_resource_search.managed_databases.results : database.identifier => {
      compartment_id = database.compartment_id
      display_name   = database.display_name
    }
  }

  target_compartments = toset([for database in values(local.targets) : database.compartment_id])

  # With compartment_id, an ONS topic and critical Database Service event rule
  # are always created, even if none of the optional observability services is
  # enabled. Tag-only targeting can determine a compartment only from a matched
  # managed database.
  baseline_compartments = var.compartment_id != null ? toset([var.compartment_id]) : local.target_compartments

  common_alarm_fields = {
    is_enabled                   = true
    message_format               = "ONS_OPTIMIZED"
    pending_duration             = "PT10M"
    repeat_notification_duration = "PT1H"
    resolution                   = "Database Management metrics are collected and alarms are evaluated only for databases that are enabled for Database Management."
    freeform_tags                = var.freeform_tags
  }
}

# Ops Insights is checked per selected database. A Database Insight in ENABLED
# status is the service-side indication that Ops Insights is active for it.
data "oci_opsi_database_insights" "target" {
  for_each = local.targets

  compartment_id = each.value.compartment_id
  database_id    = [each.key]
  status         = ["ENABLED"]
}

locals {
  opsi_enabled_targets = {
    for database_id, database in local.targets : database_id => database
    if length(try(data.oci_opsi_database_insights.target[database_id].database_insights_collection[0].items, [])) > 0
  }

  opsi_enabled_compartments = toset([for database in values(local.opsi_enabled_targets) : database.compartment_id])
}

# The Object Storage namespace is the Log Analytics namespace. GetNamespace
# reports whether the tenancy is onboarded; entities are queried only if it is.
data "oci_objectstorage_namespace" "target" {
  for_each       = local.target_compartments
  compartment_id = each.value
}

data "oci_log_analytics_namespace" "target" {
  for_each  = data.oci_objectstorage_namespace.target
  namespace = each.value.namespace
}

data "oci_log_analytics_log_analytics_entities" "target" {
  for_each = {
    for database_id, database in local.targets : database_id => database
    if try(data.oci_log_analytics_namespace.target[database.compartment_id].is_onboarded, false)
  }

  compartment_id                   = each.value.compartment_id
  namespace                        = data.oci_objectstorage_namespace.target[each.value.compartment_id].namespace
  cloud_resource_id                = each.key
  is_show_associated_sources_count = true
}

locals {
  # An active entity with a source association is the database-level Log
  # Analytics readiness check. No rule is created for an unassociated entity.
  log_analytics_targets = {
    for database_id, database in local.targets : database_id => merge(database, {
      entity_name = one([
        for entity in try(data.oci_log_analytics_log_analytics_entities.target[database_id].log_analytics_entity_collection[0].items, []) : entity.name
        if entity.state == "ACTIVE" && entity.associated_sources_count > 0
      ])
    })
    if length([
      for entity in try(data.oci_log_analytics_log_analytics_entities.target[database_id].log_analytics_entity_collection[0].items, []) : entity
      if entity.state == "ACTIVE" && entity.associated_sources_count > 0
    ]) == 1
  }
}

resource "oci_ons_notification_topic" "database_alerts" {
  for_each       = local.baseline_compartments
  compartment_id = each.value
  name           = "database-alerts"
  description    = "Database Service critical events and conditional database observability alerts"
  freeform_tags  = var.freeform_tags
}

# Database Service critical events are emitted through OCI Events and can notify
# the customer without Database Management, Ops Insights, or Log Analytics.
resource "oci_events_rule" "database_service_critical" {
  for_each       = oci_ons_notification_topic.database_alerts
  compartment_id = each.value.compartment_id
  display_name   = "database-service-critical-events"
  description    = "Routes Database, DB Node, and DB System critical events to the database-alerts notification topic."
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.databaseservice.database.critical",
      "com.oraclecloud.databaseservice.dbnode.critical",
      "com.oraclecloud.databaseservice.dbsystem.critical",
    ]
  })

  actions {
    action {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = each.value.id
    }
  }

  freeform_tags = var.freeform_tags
}

resource "oci_ons_subscription" "email" {
  for_each       = oci_ons_notification_topic.database_alerts
  compartment_id = each.value.compartment_id
  topic_id       = each.value.id
  protocol       = "EMAIL"
  endpoint       = var.email_endpoint
  freeform_tags  = var.freeform_tags
}

resource "oci_opsi_news_report" "weekly_capacity" {
  for_each = var.enable_ops_insights_reports ? local.opsi_enabled_compartments : toset([])

  compartment_id = each.value
  name           = "database-capacity-weekly"
  description    = "Weekly Operations Insights capacity and actionable-insights report for database targets."
  locale         = "en"
  news_frequency = "WEEKLY"
  day_of_week    = "MONDAY"
  ons_topic_id   = oci_ons_notification_topic.database_alerts[each.value].id
  status         = "ENABLED"
  freeform_tags  = var.freeform_tags

  content_types {
    capacity_planning_resources          = ["DATABASE"]
    actionable_insights_resources        = ["DATABASE"]
    sql_insights_top_databases_resources = ["DATABASE"]
  }
}

resource "oci_log_analytics_namespace_ingest_time_rule" "critical_database_events" {
  for_each = var.enable_log_analytics_alerts ? {
    for pair in setproduct(keys(local.log_analytics_targets), toset([
      "Abnormal Termination",
      "Data Corruption",
      "Internal Error",
      "Storage Error",
      "I/O Error",
      "Availability Error"
      ])) : "${pair[0]}:${pair[1]}" => {
      database_id = pair[0]
      label       = pair[1]
    }
  } : {}

  compartment_id = local.log_analytics_targets[each.value.database_id].compartment_id
  namespace      = data.oci_objectstorage_namespace.target[local.log_analytics_targets[each.value.database_id].compartment_id].namespace
  display_name   = "db-${local.log_analytics_targets[each.value.database_id].display_name}-${replace(lower(each.value.label), " ", "-")}-detection"
  description    = "Publishes a metric when ${each.value.label} is detected for the selected database entity."
  freeform_tags  = var.freeform_tags

  conditions {
    kind           = "FIELD"
    field_name     = "Label"
    field_operator = "EQUALS"
    field_value    = each.value.label

    additional_conditions {
      condition_field    = "Entity"
      condition_operator = "EQUALS"
      condition_value    = local.log_analytics_targets[each.value.database_id].entity_name
    }
  }

  actions {
    type           = "METRIC_EXTRACTION"
    compartment_id = local.log_analytics_targets[each.value.database_id].compartment_id
    namespace      = "database_log_analytics"
    metric_name    = "CriticalDatabaseEvent"
    dimensions     = ["Entity"]
  }
}

resource "oci_monitoring_alarm" "log_analytics_critical_event" {
  for_each = var.enable_log_analytics_alerts ? local.log_analytics_targets : {}

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-log-analytics-critical-event"
  namespace             = "database_log_analytics"
  query                 = "CriticalDatabaseEvent[1m]{Entity = \"${each.value.entity_name}\"}.sum() > 0"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Database Log Analytics event: ${each.value.display_name}"
  body                  = "Log Analytics detected a critical database label: Abnormal Termination, Data Corruption, Internal Error, Storage Error, I/O Error, or Availability Error."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = "PT1M"
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = "Open Log Analytics, filter by database entity and Label, and investigate the matching database alert or trace-log event."
  freeform_tags                = local.common_alarm_fields.freeform_tags

  depends_on = [oci_log_analytics_namespace_ingest_time_rule.critical_database_events]
}

resource "oci_monitoring_alarm" "monitoring_collection_failed" {
  for_each = local.targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-monitoring-collection-failed"
  namespace             = "oracle_oci_database"
  query                 = "MonitoringStatus[5m]{resourceId = \"${each.key}\", errorSeverity = \"ERROR\"}.count() > 0"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Database Management collection failed: ${each.value.display_name}"
  body                  = "Database Management is reporting a collection error. Investigate the management service, agent, credentials, and network path before relying on other alarms."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = local.common_alarm_fields.pending_duration
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = local.common_alarm_fields.resolution
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "cpu_critical" {
  for_each = local.targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-cpu-critical"
  namespace             = "oracle_oci_database"
  query                 = "CpuUtilization[5m]{resourceId = \"${each.key}\"}.mean() >= ${var.cpu_critical_percent}"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Database CPU utilization: ${each.value.display_name}"
  body                  = "CPU utilization has remained at or above ${var.cpu_critical_percent}% for ten minutes. Investigate workload, sessions, SQL, and host capacity."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = local.common_alarm_fields.pending_duration
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = local.common_alarm_fields.resolution
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "storage_critical" {
  for_each = local.targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-storage-critical"
  namespace             = "oracle_oci_database"
  query                 = "StorageUtilization[30m]{resourceId = \"${each.key}\"}.mean() >= ${var.storage_critical_percent}"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Database storage utilization: ${each.value.display_name}"
  body                  = "Database storage utilization is at or above ${var.storage_critical_percent}%. Review tablespace growth, archive logs, and capacity expansion options."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = "PT30M"
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = local.common_alarm_fields.resolution
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "fra_critical" {
  for_each = var.enable_full_management_alarms ? local.targets : {}

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-fra-critical"
  namespace             = "oracle_oci_database"
  query                 = "FRAUtilization[15m]{resourceId = \"${each.key}\"}.mean() >= ${var.fra_critical_percent}"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Flash Recovery Area utilization: ${each.value.display_name}"
  body                  = "Flash Recovery Area utilization is at or above ${var.fra_critical_percent}%. Free space or increase FRA capacity before archive logging blocks the database."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = "PT15M"
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = local.common_alarm_fields.resolution
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "dataguard_apply_lag_critical" {
  for_each = var.enable_full_management_alarms ? local.targets : {}

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [oci_ons_notification_topic.database_alerts[each.value.compartment_id].id]
  display_name          = "db-${each.value.display_name}-dataguard-apply-lag-critical"
  namespace             = "oracle_oci_database"
  resource_group        = "oracle_dataguard"
  query                 = "ApplyLag[5m]{resourceId = \"${each.key}\"}.mean() >= ${var.dataguard_apply_lag_critical_seconds}"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Data Guard apply lag: ${each.value.display_name}"
  body                  = "Data Guard apply lag is at or above ${var.dataguard_apply_lag_critical_seconds} seconds. Investigate redo transport, standby apply, and network health."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = local.common_alarm_fields.pending_duration
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  resolution                   = local.common_alarm_fields.resolution
  freeform_tags                = local.common_alarm_fields.freeform_tags
}
