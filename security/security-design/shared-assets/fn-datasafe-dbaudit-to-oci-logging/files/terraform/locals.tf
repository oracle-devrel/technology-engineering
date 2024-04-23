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
  policy_displayname = "${var.policynameprefix}${local.resource_nc}"
  dynamicgroup_displayname = "${var.dynamicgroupnameprefix}${local.resource_nc}"
  tracker_bucket_name = "${var.tracker-bucket}${local.resource_nc}"
  oci_repo_displayname = "${var.ocir_repo_name}${local.resource_nc}/${var.functionname}"
  functionapp_display_name = "${var.functionappnameprefix}${local.resource_nc}"
  function_display_name = "${var.functionnameprefix}${local.resource_nc}"
  function_invoke_oci_logging_displayname = "${var.functioninvokeociloggingname}${local.resource_nc}"
  ocilogging_group_displayname="${var.loggrouprefix}${local.resource_nc}"
  ocilogging_dslog_displayname="${var.log_datafafeauditdbnameprefix}${local.resource_nc}"
  notificationtopic_name = "${var.notificationtopicnameprefix}${local.resource_nc}"
  alarm_displayname = "${var.alarmnameprefix}${local.resource_nc}"
  fn_working_dir = "function/${var.functionname}"
  fn_repository= "${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}"
  fn_image = "${local.fn_repository}:0.0.1"
  fn_image_app = "${oci_artifacts_container_repository.fn_container_repository.display_name}:0.0.1"
}