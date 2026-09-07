locals {
  devops_log_name = try(trimspace(var.devops_log_name), "") == "" ? "${var.devops_log_group_name}_${local.devops_project_name}_log" : var.devops_log_name
}

resource "oci_ons_notification_topic" "devops_notification_topic" {
  compartment_id = local.devops_project_compartment_id
  name           = var.notification_topic_name
  description    = var.notification_topic_description
  count          = var.create_devops_project && var.create_notification_topic ? 1 : 0
}

resource "oci_devops_project" "devops_project" {
  count = var.create_devops_project ? 1 : 0

  compartment_id = local.devops_project_compartment_id
  name           = var.devops_project_name
  description    = var.devops_project_description

  notification_config {
    topic_id = var.create_notification_topic ? oci_ons_notification_topic.devops_notification_topic[0].id : var.notification_topic_id
  }
}

resource "oci_logging_log_group" "devops_log_group" {
  count = var.create_devops_project && var.devops_log_is_enabled ? 1 : 0

  compartment_id = local.devops_project_compartment_id
  display_name   = var.devops_log_group_name
  description    = var.devops_log_group_description
}

resource "oci_logging_log" "devops_log" {
  count = var.create_devops_project && var.devops_log_is_enabled ? 1 : 0

  display_name = local.devops_log_name
  log_group_id = oci_logging_log_group.devops_log_group[0].id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "all"
      resource    = local.devops_project_id
      service     = "devops"
      source_type = "OCISERVICE"
    }

    compartment_id = local.devops_project_compartment_id
  }

  is_enabled         = true
  retention_duration = var.devops_log_retention_period_in_days
}
