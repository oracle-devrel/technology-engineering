resource "oci_ons_notification_topic" "devops_notification_topic" {
  compartment_id = var.compartment_id
  name           = var.notification_topic_name
  description = var.notification_topic_description
  count = var.create_notification_topic ? 1 : 0
}

resource "oci_devops_project" "devops_project" {
  compartment_id = var.compartment_id
  name           = var.devops_project_name
  description = var.devops_project_description
  notification_config {
    topic_id = var.create_notification_topic? oci_ons_notification_topic.devops_notification_topic.0.id : var.notification_topic_id
  }
}

resource "oci_logging_log_group" "devops_log_group" {
  compartment_id = var.compartment_id
  display_name   = var.devops_log_group_name
  description = var.devops_log_group_description
}

resource "oci_logging_log" "devops_log" {
  #Required
  display_name = "${var.devops_log_group_name}_${var.devops_project_name}_log"
  log_group_id = oci_logging_log_group.devops_log_group.id
  log_type     = "SERVICE"

  #Optional
  configuration {
    #Required
    source {
      #Required
      category    = "all"
      resource    = oci_devops_project.devops_project.id
      service     = "devops"
      source_type = "OCISERVICE"
    }

    #Optional
    compartment_id = var.compartment_id
  }

  is_enabled         = true
  retention_duration = var.devops_log_retention_period_in_days
}