resource "oci_ons_notification_topic" "devops_notification_topic" {
  compartment_id = local.devops_project_compartment_id
  name           = var.notification_topic_name
  description    = var.notification_topic_description
  count          = var.create_devops_project && var.create_notification_topic ? 1 : 0
}

resource "oci_devops_project" "devops_project" {
  count = var.create_devops_project ? 1 : 0

  compartment_id = var.compartment_id
  name           = var.devops_project_name
  description    = var.devops_project_description
  notification_config {
    topic_id = var.create_notification_topic ? oci_ons_notification_topic.devops_notification_topic.0.id : var.notification_topic_id
  }
}

resource "oci_logging_log_group" "devops_log_group" {
  count = var.create_devops_project ? 1 : 0

  compartment_id = local.devops_project_compartment_id
  display_name   = var.devops_log_group_name
  description    = var.devops_log_group_description
}

resource "oci_logging_log" "devops_log" {
  count = var.create_devops_project ? 1 : 0

  #Required
  display_name = "${var.devops_log_group_name}_${local.devops_project_name}_log"
  log_group_id = oci_logging_log_group.devops_log_group[0].id
  log_type     = "SERVICE"

  #Optional
  configuration {
    #Required
    source {
      #Required
      category    = "all"
      resource    = local.devops_project_id
      service     = "devops"
      source_type = "OCISERVICE"
    }

    #Optional
    compartment_id = local.devops_project_compartment_id
  }

  is_enabled         = true
  retention_duration = var.devops_log_retention_period_in_days
}
