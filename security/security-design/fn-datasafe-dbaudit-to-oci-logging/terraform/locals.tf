###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

locals {
  ocir_docker_repository = join("", [lower(lookup(data.oci_identity_regions.oci_regions.regions[0], "key")), ".ocir.io"])
  ocir_namespace = lookup(data.oci_objectstorage_namespace.namespace, "namespace")
  
  namespace = lookup(data.oci_objectstorage_namespace.namespace, "namespace")
  compartment_name = lookup(data.oci_identity_compartment.compartment, "name")
  resource_nc = "-${var.deployment_name}-${var.region}-${var.purpose}-${random_id.tag.hex}"
  policy_displayname = "${var.PolicyNamePrefix}${local.resource_nc}"
  dynamicgroup_displayname = "${var.DynamicGroupNamePrefix}${local.resource_nc}"
  tracker_bucket_name = "${var.tracker-bucket}${local.resource_nc}"
  oci_repo_displayname = "${var.ocir_repo_name}${local.resource_nc}/${var.FunctionName}"
  functionapp_display_name = "${var.FunctionAppNamePrefix}${local.resource_nc}"
  function_display_name = "${var.FunctionNamePrefix}${local.resource_nc}"
  function_invoke_oci_logging_displayname = "${var.FunctionInvokeOCILoggingName}${local.resource_nc}"
  ocilogging_group_displayname="${var.LogGroupPrefix}${local.resource_nc}"
  ocilogging_dslog_displayname="${var.LogDataSafeAuditDBNamePrefix}${local.resource_nc}"
  notificationtopic_name = "${var.NotificationTopicNamePrefix}${local.resource_nc}"
  alarm_displayname = "${var.AlarmNamePrefix}${local.resource_nc}"
  fn_working_dir = "function/${var.FunctionName}"
  fn_registry = "${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}"
  fn_repository = "${local.fn_registry}/${var.FunctionName}"
  fn_image = "${local.fn_repository}:0.0.1"
}