###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################


resource "oci_functions_application" "FunctionApp" {
  compartment_id = var.compartment_ocid
  display_name   = local.functionapp_display_name
  subnet_ids     = [var.create_network ? module.setup-network[0].subnet_ocid : var.subnet_ocid] 
}

resource "oci_functions_function" "fun1" {
  depends_on     = [null_resource.FunctionAppPush2OCIR]
  application_id = oci_functions_application.FunctionApp.id
  display_name   = local.function_display_name
  #image          = "${local.ocir_docker_repository}/${local.namespace}/${var.ocir_repo_name}/${var.FunctionNamePrefix}:0.0.1"
  image          = local.fn_image
  memory_in_mbs  =  var.FunctionMemory
  timeout_in_seconds = var.FunctionTimeoutSec
  config = {
    "ociDataSafeCompartmentOCID" : var.tenancy_ocid
    "ociOSTrackerBucketName" : local.tracker_bucket_name
    "ociLoggingLogOCID" : oci_logging_log.log_datadafe_auditdb.id
  }
  
}

resource "oci_logging_log" "log_on_fn_invoke" {
  display_name = local.function_invoke_oci_logging_displayname
  log_group_id = oci_logging_log_group.log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.FunctionApp.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled = true
  
}


