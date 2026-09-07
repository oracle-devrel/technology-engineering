# Database Management and native Database Service resources are discovered
# separately. This allows tag selection to target an Autonomous or Base Database
# even when Database Management has not been enabled for that database.
locals {
  tag_conditions = [
    for key, value in var.tags :
    "(freeformTags.key = '${replace(key, "'", "\\'")}' && freeformTags.value = '${replace(value, "'", "\\'")}')"
  ]

  autonomous_database_query = var.compartment_id != null ? (
    "query AutonomousDatabase resources where compartmentId = '${var.compartment_id}'"
    ) : (
    "query AutonomousDatabase resources where ${join(" && ", local.tag_conditions)}"
  )

  base_database_query = var.compartment_id != null ? (
    "query Database resources where compartmentId = '${var.compartment_id}'"
    ) : (
    "query Database resources where ${join(" && ", local.tag_conditions)}"
  )
}

check "target_selector_is_present" {
  assert {
    condition     = var.compartment_id != null || length(var.tags) > 0
    error_message = "Set compartment_id, or provide at least one tags entry."
  }
}

data "oci_resource_search" "autonomous_databases" {
  query = local.autonomous_database_query
}

data "oci_resource_search" "base_databases" {
  query = local.base_database_query
}

locals {
  # OCI resource-search is region-scoped. Its identifier is the managed database
  # resource OCID, which is also the resourceId dimension used by these metrics.
  service_targets = merge(
    {
      for database in data.oci_resource_search.autonomous_databases.results : database.identifier => {
        compartment_id = database.compartment_id
        display_name   = database.display_name
        target_type    = "autonomous"
      }
    },
    {
      for database in data.oci_resource_search.base_databases.results : database.identifier => {
        compartment_id = database.compartment_id
        display_name   = database.display_name
        target_type    = "base"
      }
    },
  )

  service_target_compartments = toset([for database in values(local.service_targets) : database.compartment_id])

  # Used for optional Ops Insights and Log Analytics preflight checks. The
  # managed targets remain separate so DB Management metrics are never applied
  # to a database that has not been enabled for Database Management.
  targets = merge(local.service_targets, local.managed_targets)

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
    freeform_tags                = var.freeform_tags
  }

  database_management_alerts = [
    "Database Management collection failure",
    "Sustained CPU utilization",
    "Database storage utilization",
    "Flash Recovery Area utilization",
    "Data Guard apply lag",
    "Tablespace utilization",
    "Data Guard transport lag",
    "Recovery-window breach",
    "Database Management job failure",
    "Session or process exhaustion",
    "Persistent blocking sessions",
    "Invalid objects or unusable indexes",
  ]

  ops_insights_alerts = [
    "Capacity and inventory digest",
    "Daily SQL performance degradation report",
  ]

  log_analytics_alerts = [
    "Database crash",
    "Internal Oracle incident",
    "Data corruption",
    "Storage or I/O error",
    "Database startup or availability failure",
    "Listener connection failure burst",
    "Database timeout burst",
    "Privileged login or audit-policy change",
  ]
}

# Database Management registrations do not inherit freeform tags from the
# underlying database. Discover them by the selected databases' compartments,
# then keep only registrations whose OCID belongs to the selected service targets.
data "oci_database_management_managed_databases" "managed_databases" {
  for_each = var.compartment_id != null ? toset([var.compartment_id]) : local.service_target_compartments

  compartment_id = each.value
}

locals {
  managed_targets = {
    for database in flatten([for result in values(data.oci_database_management_managed_databases.managed_databases) : result.managed_database_collection[0].items]) : database.id => {
      compartment_id = database.compartment_id
      display_name   = database.name
    }
    if contains(keys(local.service_targets), database.id) && anytrue([
      for feature in database.dbmgmt_feature_configs :
      feature.feature == "DIAGNOSTICS_AND_MANAGEMENT" && feature.feature_status == "ENABLED"
    ])
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

data "oci_ons_notification_topics" "existing_database_alerts" {
  for_each       = local.baseline_compartments
  compartment_id = each.value
  name           = var.notification_topic_name
  state          = "ACTIVE"
}

locals {
  existing_notification_topics = {
    for compartment_id, result in data.oci_ons_notification_topics.existing_database_alerts : compartment_id => one(result.notification_topics)
    if length(result.notification_topics) == 1
  }

  notification_topic_compartments_to_create = setsubtract(
    local.baseline_compartments,
    toset(keys(local.existing_notification_topics)),
  )
}

resource "oci_ons_notification_topic" "database_alerts" {
  for_each       = local.baseline_compartments
  compartment_id = each.value
  name           = var.notification_topic_name
  description    = "Database Service critical events and conditional database observability alerts"
  freeform_tags  = var.freeform_tags

  lifecycle {
    # A topic discovered before the first deployment is adopted by the import
    # block below. Preserve its existing metadata rather than changing it.
    ignore_changes = [description, freeform_tags, defined_tags]
  }
}

import {
  for_each = local.existing_notification_topics
  to       = oci_ons_notification_topic.database_alerts[each.key]
  id       = each.value.topic_id
}

locals {
  notification_topic_ids = merge(
    { for compartment_id, topic in oci_ons_notification_topic.database_alerts : compartment_id => topic.id },
    { for compartment_id, topic in local.existing_notification_topics : compartment_id => topic.topic_id },
  )
}

data "oci_ons_notification_topics" "existing_operations" {
  for_each       = var.enable_recommended_alarms || var.enable_ops_insights_sql_degradation_report ? local.baseline_compartments : toset([])
  compartment_id = each.value
  name           = var.operations_notification_topic_name
  state          = "ACTIVE"
}

locals {
  existing_operations_notification_topics = {
    for compartment_id, result in data.oci_ons_notification_topics.existing_operations : compartment_id => one(result.notification_topics)
    if length(result.notification_topics) == 1
  }

  operations_topic_compartments_to_create = setsubtract(
    var.enable_recommended_alarms || var.enable_ops_insights_sql_degradation_report ? local.baseline_compartments : toset([]),
    toset(keys(local.existing_operations_notification_topics)),
  )
}

resource "oci_ons_notification_topic" "operations" {
  for_each       = var.enable_recommended_alarms || var.enable_ops_insights_sql_degradation_report ? local.baseline_compartments : toset([])
  compartment_id = each.value
  name           = var.operations_notification_topic_name
  description    = "Database operational alerts, including backup failures"
  freeform_tags  = var.freeform_tags

  lifecycle {
    # Preserve metadata on a topic discovered and adopted from the target
    # compartment; only its existence and ID are needed for delivery.
    ignore_changes = [description, freeform_tags, defined_tags]
  }
}

import {
  for_each = local.existing_operations_notification_topics
  to       = oci_ons_notification_topic.operations[each.key]
  id       = each.value.topic_id
}

locals {
  operations_notification_topic_ids = merge(
    { for compartment_id, topic in oci_ons_notification_topic.operations : compartment_id => topic.id },
    { for compartment_id, topic in local.existing_operations_notification_topics : compartment_id => topic.topic_id },
  )
}

# Database Service critical events are emitted through OCI Events and can notify
# the customer without Database Management, Ops Insights, or Log Analytics.
resource "oci_events_rule" "database_service_critical" {
  for_each       = var.enable_database_service_event_rules ? local.service_targets : {}
  compartment_id = each.value.compartment_id
  display_name   = "db-${each.value.display_name}-critical-events"
  description    = "Routes critical Database Service events for the selected database to the database-alerts notification topic."
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.databaseservice.database.critical",
      "com.oraclecloud.databaseservice.dbnode.critical",
      "com.oraclecloud.databaseservice.dbsystem.critical",
    ]
    data = {
      resourceId = [each.key]
    }
  })

  actions {
    action {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = local.notification_topic_ids[each.value.compartment_id]
    }
  }

  freeform_tags = var.freeform_tags
}

# Backup failures are Database Service critical events. This rule does not use
# Database Management metrics and therefore remains available without it.
resource "oci_events_rule" "database_backup_failure" {
  for_each       = var.enable_recommended_alarms && var.enable_database_service_event_rules ? local.service_targets : {}
  compartment_id = each.value.compartment_id
  display_name   = "db-${each.value.display_name}-backup-failure-events"
  description    = "Routes Database Service backup failure events for the selected database to the db-prod-operations notification topic."
  is_enabled     = true

  condition = jsonencode({
    eventType = ["com.oraclecloud.databaseservice.database.critical"]
    data = {
      resourceId = [each.key]
      additionalDetails = {
        eventName = ["HEALTH.DB_CLUSTER.CDB.BACKUP_FAILURE"]
      }
    }
  })

  actions {
    action {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = local.operations_notification_topic_ids[each.value.compartment_id]
    }
  }

  freeform_tags = var.freeform_tags
}

resource "oci_ons_subscription" "email" {
  for_each       = local.notification_topic_ids
  compartment_id = each.key
  topic_id       = each.value
  protocol       = "EMAIL"
  endpoint       = var.email_endpoint
  freeform_tags  = var.freeform_tags
}

resource "oci_ons_subscription" "operations_email" {
  for_each       = local.operations_notification_topic_ids
  compartment_id = each.key
  topic_id       = each.value
  protocol       = "EMAIL"
  endpoint       = var.email_endpoint
  freeform_tags  = var.freeform_tags
}

resource "oci_opsi_news_report" "weekly_capacity" {
  for_each = var.enable_ops_insights_reports ? local.opsi_enabled_compartments : toset([])

  compartment_id = each.value
  name           = "database-capacity-weekly"
  description    = "Weekly Operations Insights capacity report for database targets."
  locale         = "EN"
  news_frequency = "WEEKLY"
  day_of_week    = "MONDAY"
  ons_topic_id   = local.notification_topic_ids[each.value]
  status         = "ENABLED"
  freeform_tags  = var.freeform_tags

  content_types {
    capacity_planning_resources = ["DATABASE"]
  }
}

resource "oci_opsi_news_report" "daily_sql_degradation" {
  for_each = var.enable_ops_insights_reports && var.enable_ops_insights_sql_degradation_report ? local.opsi_enabled_compartments : toset([])

  compartment_id = each.value
  name           = "database-sql-degradation-daily"
  description    = "Daily Operations Insights SQL performance-degradation report for database targets."
  locale         = "EN"
  news_frequency = "DAILY"
  ons_topic_id   = local.operations_notification_topic_ids[each.value]
  status         = "ENABLED"
  freeform_tags  = var.freeform_tags

  content_types {
    sql_insights_performance_degradation_resources = ["DATABASE"]
  }
}

resource "oci_log_analytics_namespace_ingest_time_rule" "critical_database_events" {
  for_each = var.enable_log_analytics_alerts ? {
    for pair in setproduct(toset([for target in values(local.log_analytics_targets) : target.compartment_id]), toset([
      "Abnormal Termination",
      "Data Corruption",
      "Internal Error",
      "Storage Error",
      "I/O Error",
      "Availability Error"
    ])) : "${pair[0]}:${pair[1]}" => { compartment_id = pair[0], label = pair[1] }
  } : {}

  compartment_id = each.value.compartment_id
  namespace      = data.oci_objectstorage_namespace.target[each.value.compartment_id].namespace
  display_name   = "db-${replace(replace(lower(each.value.label), " ", "-"), "/", "-")}-detection"
  description    = "Publishes a metric when ${each.value.label} is detected in database logs in this compartment."
  freeform_tags  = var.freeform_tags

  conditions {
    kind = "FIELD"
    # OCI Log Analytics ingest-time detection rules use the internal metric-tag
    # field as the mandatory base condition. The selected label is its value.
    field_name     = "mtag"
    field_operator = "EQUAL"
    field_value    = each.value.label

  }

  actions {
    type           = "METRIC_EXTRACTION"
    compartment_id = each.value.compartment_id
    namespace      = "database_log_analytics"
    metric_name    = "CriticalDatabaseEvent"
  }
}

resource "oci_monitoring_alarm" "log_analytics_critical_event" {
  for_each = var.enable_log_analytics_alerts ? toset([for target in values(local.log_analytics_targets) : target.compartment_id]) : toset([])

  compartment_id        = each.value
  metric_compartment_id = each.value
  destinations          = [local.notification_topic_ids[each.value]]
  display_name          = "db-log-analytics-critical-event"
  namespace             = "database_log_analytics"
  query                 = "CriticalDatabaseEvent[1m].sum() > 0"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] Database Log Analytics event"
  body                  = "Log Analytics detected a critical database label: Abnormal Termination, Data Corruption, Internal Error, Storage Error, I/O Error, or Availability Error."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = "PT1M"
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  freeform_tags                = local.common_alarm_fields.freeform_tags

  depends_on = [oci_log_analytics_namespace_ingest_time_rule.critical_database_events]
}

resource "oci_monitoring_alarm" "monitoring_collection_failed" {
  for_each = local.managed_targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
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
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "cpu_critical" {
  for_each = local.managed_targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
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
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "storage_critical" {
  for_each = local.managed_targets

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
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
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "fra_critical" {
  for_each = var.enable_full_management_alarms ? local.managed_targets : {}

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
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
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

resource "oci_monitoring_alarm" "dataguard_apply_lag_critical" {
  for_each = var.enable_full_management_alarms ? local.managed_targets : {}

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
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
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

# Native Database Service metrics are available independently of Database
# Management. These compartment-level alarms cover Base Database, Exadata VM
# Cluster, and Autonomous Database service namespaces when their metrics exist.
locals {
  database_service_metric_alarm_definitions = {
    database_cpu = {
      target_type      = "base"
      namespace        = "oci_database"
      metric           = "CpuUtilization"
      threshold        = var.cpu_critical_percent
      pending_duration = "PT10M"
      title            = "OCI Database CPU utilization"
    }
    database_storage = {
      target_type      = "base"
      namespace        = "oci_database"
      metric           = "StorageUtilization"
      threshold        = var.storage_critical_percent
      pending_duration = "PT30M"
      title            = "OCI Database storage utilization"
    }
    cluster_cpu = {
      target_type      = "cluster"
      namespace        = "oci_database_cluster"
      metric           = "CpuUtilization"
      threshold        = var.cpu_critical_percent
      pending_duration = "PT10M"
      title            = "OCI Database Cluster CPU utilization"
    }
    cluster_disk = {
      target_type      = "cluster"
      namespace        = "oci_database_cluster"
      metric           = "DiskUtilization"
      threshold        = var.storage_critical_percent
      pending_duration = "PT30M"
      title            = "OCI Database Cluster disk utilization"
    }
    autonomous_cpu = {
      target_type      = "autonomous"
      namespace        = "oci_autonomous_database"
      metric           = "CpuUtilization"
      threshold        = var.cpu_critical_percent
      pending_duration = "PT10M"
      title            = "OCI Autonomous Database CPU utilization"
    }
    autonomous_storage = {
      target_type      = "autonomous"
      namespace        = "oci_autonomous_database"
      metric           = "StorageUtilization"
      threshold        = var.storage_critical_percent
      pending_duration = "PT30M"
      title            = "OCI Autonomous Database storage utilization"
    }
  }

  database_service_metric_alarms = var.enable_database_service_metric_alarms ? {
    for pair in setproduct(keys(local.service_targets), keys(local.database_service_metric_alarm_definitions)) : "${pair[0]}:${pair[1]}" => merge(
      local.database_service_metric_alarm_definitions[pair[1]],
      local.service_targets[pair[0]],
      { database_id = pair[0], key = pair[1] },
    )
    if local.service_targets[pair[0]].target_type == local.database_service_metric_alarm_definitions[pair[1]].target_type
  } : {}
}

resource "oci_monitoring_alarm" "database_service_metrics" {
  for_each = local.database_service_metric_alarms

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
  display_name          = "db-${each.value.display_name}-${each.value.key}-critical"
  namespace             = each.value.namespace
  query                 = "${each.value.metric}[5m]{resourceId = \"${each.value.database_id}\"}.max() >= ${each.value.threshold}"
  severity              = "CRITICAL"
  notification_title    = "[CRITICAL] ${each.value.title}"
  body                  = "${each.value.title} reached ${each.value.threshold}% for ${each.value.display_name}. Identify the affected metric stream and investigate the database resource."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = each.value.pending_duration
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

# Additional Database Management recommendations. The rules are evaluated only
# for managed databases returned by the Database Management discovery query.
locals {
  recommended_database_management_alarm_definitions = {
    tablespace_warning = {
      metric           = "StorageUtilizationByTablespace"
      threshold        = var.tablespace_warning_percent
      severity         = "WARNING"
      pending_duration = "PT15M"
      title            = "Tablespace utilization warning"
    }
    tablespace_critical = {
      metric           = "StorageUtilizationByTablespace"
      threshold        = var.storage_critical_percent
      severity         = "CRITICAL"
      pending_duration = "PT15M"
      title            = "Tablespace utilization critical"
    }
    dataguard_transport_lag = {
      metric           = "TransportLag"
      threshold        = var.dataguard_apply_lag_critical_seconds
      severity         = "CRITICAL"
      pending_duration = "PT10M"
      title            = "Data Guard transport lag"
      resource_group   = "oracle_dataguard"
    }
    recovery_window_breach = {
      metric           = "RecoveryWindow"
      threshold        = 0
      severity         = "CRITICAL"
      pending_duration = "PT15M"
      title            = "Recovery window breach"
    }
    dbmgmt_job_failure = {
      metric           = "dbmgmtJobExecutionsCount"
      threshold        = 0
      severity         = "WARNING"
      pending_duration = "PT5M"
      title            = "Database Management job failure"
      status_filter    = ", status = \"Failed\""
    }
    session_warning = {
      metric           = "SessionLimitUtilization"
      threshold        = var.session_warning_percent
      severity         = "WARNING"
      pending_duration = "PT10M"
      title            = "Session utilization warning"
    }
    session_critical = {
      metric           = "SessionLimitUtilization"
      threshold        = var.storage_critical_percent
      severity         = "CRITICAL"
      pending_duration = "PT10M"
      title            = "Session utilization critical"
    }
    process_warning = {
      metric           = "ProcessLimitUtilization"
      threshold        = var.process_warning_percent
      severity         = "WARNING"
      pending_duration = "PT10M"
      title            = "Process utilization warning"
    }
    process_critical = {
      metric           = "ProcessLimitUtilization"
      threshold        = var.storage_critical_percent
      severity         = "CRITICAL"
      pending_duration = "PT10M"
      title            = "Process utilization critical"
    }
    blocking_sessions = {
      metric           = "BlockingSessions"
      threshold        = 0
      severity         = "WARNING"
      pending_duration = "PT15M"
      title            = "Persistent blocking sessions"
    }
    invalid_objects = {
      metric           = "InvalidObjects"
      threshold        = 0
      severity         = "WARNING"
      pending_duration = "PT15M"
      title            = "Invalid database objects"
    }
    unusable_indexes = {
      metric           = "UnusableIndexes"
      threshold        = 0
      severity         = "WARNING"
      pending_duration = "PT15M"
      title            = "Unusable indexes"
    }
  }

  recommended_database_management_alarms = var.enable_recommended_alarms ? {
    for pair in setproduct(keys(local.managed_targets), keys(local.recommended_database_management_alarm_definitions)) : "${pair[0]}:${pair[1]}" => merge(
      local.managed_targets[pair[0]],
      local.recommended_database_management_alarm_definitions[pair[1]],
      { database_id = pair[0] },
    )
  } : {}
}

resource "oci_monitoring_alarm" "recommended_database_management" {
  for_each = local.recommended_database_management_alarms

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
  display_name          = "db-${each.value.display_name}-${replace(each.value.title, " ", "-")}"
  namespace             = "oracle_oci_database"
  resource_group        = try(each.value.resource_group, null)
  query                 = "${each.value.metric}[5m]{resourceId = \"${each.value.database_id}\"${try(each.value.status_filter, "")}}.max() > ${each.value.threshold}"
  severity              = each.value.severity
  notification_title    = "[${each.value.severity}] ${each.value.title}: ${each.value.display_name}"
  body                  = "Database Management detected ${lower(each.value.title)} for ${each.value.display_name}. Review the database and remediate according to the operational runbook."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = each.value.pending_duration
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  freeform_tags                = local.common_alarm_fields.freeform_tags
}

# Warning and error Database Service events do not require Database Management.
resource "oci_events_rule" "database_service_operational" {
  for_each       = var.enable_recommended_alarms && var.enable_database_service_event_rules ? local.service_targets : {}
  compartment_id = each.value.compartment_id
  display_name   = "db-${each.value.display_name}-operational-events"
  description    = "Routes DB Node warning and error events for the selected database to the database-alerts notification topic."
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.databaseservice.dbnode.error",
      "com.oraclecloud.databaseservice.dbnode.warning",
    ]
    data = {
      resourceId = [each.key]
    }
  })

  actions {
    action {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = local.notification_topic_ids[each.value.compartment_id]
    }
  }

  freeform_tags = var.freeform_tags
}

locals {
  recommended_log_analytics_event_definitions = {
    connection_error = { label = "Connection Error", severity = "WARNING", title = "Listener connection failure burst" }
    timeout          = { label = "Timeout", severity = "WARNING", title = "Database timeout burst" }
    privileged_login = { label = "Privileged Login", severity = "WARNING", title = "Privileged login" }
    audit_policy     = { label = "Audit Policy Change", severity = "CRITICAL", title = "Audit policy change" }
  }

  recommended_log_analytics_events = var.enable_recommended_alarms && var.enable_log_analytics_alerts ? {
    for pair in setproduct(toset([for target in values(local.log_analytics_targets) : target.compartment_id]), keys(local.recommended_log_analytics_event_definitions)) : "${pair[0]}:${pair[1]}" => merge(
      { compartment_id = pair[0] },
      local.recommended_log_analytics_event_definitions[pair[1]],
      { rule_key = pair[1] },
    )
  } : {}
}

resource "oci_log_analytics_namespace_ingest_time_rule" "recommended_database_events" {
  for_each = local.recommended_log_analytics_events

  compartment_id = each.value.compartment_id
  namespace      = data.oci_objectstorage_namespace.target[each.value.compartment_id].namespace
  display_name   = "db-${each.value.rule_key}-detection"
  description    = "Publishes a metric when ${each.value.label} is detected in database logs in this compartment."
  freeform_tags  = var.freeform_tags

  conditions {
    kind = "FIELD"
    # OCI requires mtag as the base condition for label-based ingest-time rules.
    field_name     = "mtag"
    field_operator = "EQUAL"
    field_value    = each.value.label

  }

  actions {
    type           = "METRIC_EXTRACTION"
    compartment_id = each.value.compartment_id
    namespace      = "database_log_analytics"
    metric_name    = "RecommendedDatabaseEvent_${each.value.rule_key}"
  }
}

resource "oci_monitoring_alarm" "recommended_log_analytics_events" {
  for_each = local.recommended_log_analytics_events

  compartment_id        = each.value.compartment_id
  metric_compartment_id = each.value.compartment_id
  destinations          = [local.notification_topic_ids[each.value.compartment_id]]
  display_name          = "db-log-analytics-${each.value.rule_key}"
  namespace             = "database_log_analytics"
  query                 = "RecommendedDatabaseEvent_${each.value.rule_key}[5m].sum() > 0"
  severity              = each.value.severity
  notification_title    = "[${each.value.severity}] ${each.value.title}"
  body                  = "Log Analytics detected ${each.value.label}. Investigate the matching database log record."

  is_enabled                   = local.common_alarm_fields.is_enabled
  message_format               = local.common_alarm_fields.message_format
  pending_duration             = "PT5M"
  repeat_notification_duration = local.common_alarm_fields.repeat_notification_duration
  freeform_tags                = local.common_alarm_fields.freeform_tags

  depends_on = [oci_log_analytics_namespace_ingest_time_rule.recommended_database_events]
}
