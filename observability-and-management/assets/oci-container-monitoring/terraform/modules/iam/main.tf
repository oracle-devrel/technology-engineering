#######################################
# IAM Policies for Container Instance Monitoring
# This module creates necessary IAM policies for:
# - Container Instance management
# - Logging service access
# - Management Agent operations
# - Metrics collection
#######################################

locals {
  # Generate dynamic group matching rule for container instances
  dynamic_group_matching_rule = "ALL {resource.type='computecontainerinstance', resource.compartment.id='${var.compartment_ocid}'}"

  # Generate matching rule for management agents
  agent_matching_rule = "ALL {resource.type='managementagent', resource.compartment.id='${var.compartment_ocid}'}"
}

#######################################
# Dynamic Group for Container Instances
#######################################
resource "oci_identity_dynamic_group" "container_instance_dg" {
  count          = var.create_dynamic_groups ? 1 : 0
  compartment_id = var.tenancy_ocid
  name           = "${var.resource_prefix}-container-instance-dg"
  description    = "Dynamic group for container instances to access OCI services"
  matching_rule  = local.dynamic_group_matching_rule

  freeform_tags = var.freeform_tags
}

#######################################
# Dynamic Group for Management Agents
#######################################
resource "oci_identity_dynamic_group" "management_agent_dg" {
  count          = var.create_dynamic_groups && var.enable_management_agent ? 1 : 0
  compartment_id = var.tenancy_ocid
  name           = "${var.resource_prefix}-mgmt-agent-dg"
  description    = "Dynamic group for management agents to send metrics"
  matching_rule  = local.agent_matching_rule

  freeform_tags = var.freeform_tags
}

#######################################
# Policy for Container Instance Logging
#######################################
resource "oci_identity_policy" "container_logging_policy" {
  count          = var.create_policies ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "${var.resource_prefix}-container-logging-policy"
  description    = "Policy to allow container instances to write logs"

  statements = [
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].name : var.existing_container_dg_name} to manage log-content in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].name : var.existing_container_dg_name} to use log-groups in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = var.freeform_tags
}

#######################################
# Policy for Management Agent Metrics
#######################################
resource "oci_identity_policy" "mgmt_agent_metrics_policy" {
  count          = var.create_policies && var.enable_management_agent ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "${var.resource_prefix}-mgmt-agent-metrics-policy"
  description    = "Policy to allow management agents to send metrics and telemetry"

  statements = [
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.management_agent_dg[0].name : var.existing_agent_dg_name} to use metrics in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.management_agent_dg[0].name : var.existing_agent_dg_name} to use management-agents in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.management_agent_dg[0].name : var.existing_agent_dg_name} to read metrics in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = var.freeform_tags
}

#######################################
# Policy for Container Instance Resource Access
#######################################
resource "oci_identity_policy" "container_resource_policy" {
  count          = var.create_policies ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "${var.resource_prefix}-container-resource-policy"
  description    = "Policy to allow container instances to access required resources"

  statements = [
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].name : var.existing_container_dg_name} to read metrics in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].name : var.existing_container_dg_name} to read all-resources in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = var.freeform_tags
}

#######################################
# Policy for Logging Service
# NOTE: Disabled - logging-analytics is not a valid IAM service
# Container instances already have logging permissions via container_logging_policy
#######################################
resource "oci_identity_policy" "logging_service_policy" {
  count          = 0  # Disabled - not needed
  compartment_id = var.tenancy_ocid
  name           = "${var.resource_prefix}-logging-service-policy"
  description    = "Policy to allow logging service to access resources"

  statements = [
    "Allow service logging-analytics to read log-groups in compartment id ${var.compartment_ocid}",
    "Allow service logging-analytics to read log-content in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = var.freeform_tags
}

#######################################
# Policy for Monitoring and Alarms
#######################################
resource "oci_identity_policy" "monitoring_policy" {
  count          = var.create_policies && var.enable_alarms ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "${var.resource_prefix}-monitoring-policy"
  description    = "Policy for monitoring and alarm access"

  statements = [
    "Allow dynamic-group ${var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].name : var.existing_container_dg_name} to read alarms in compartment id ${var.compartment_ocid}",
    "Allow service ons to use alarms in compartment id ${var.compartment_ocid}",
  ]

  freeform_tags = var.freeform_tags
}
