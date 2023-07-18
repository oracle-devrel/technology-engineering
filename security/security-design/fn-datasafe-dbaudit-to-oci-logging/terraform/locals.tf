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
  oci_repo_displayname = "${var.ocir_repo_name}${local.resource_nc}"
  functionapp_display_name = "${var.FunctionAppNamePrefix}${local.resource_nc}"
  function_display_name = "${var.FunctionNamePrefix}${local.resource_nc}"
  function_invoke_oci_logging_displayname = "${var.FunctionInvokeOCILoggingName}${local.resource_nc}"
}