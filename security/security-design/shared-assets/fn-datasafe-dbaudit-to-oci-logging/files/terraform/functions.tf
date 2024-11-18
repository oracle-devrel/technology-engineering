###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################


resource "oci_functions_application" "functionapp" {
  compartment_id = var.compartment_ocid
  display_name   = local.functionapp_display_name
  shape = var.functionappshape
  subnet_ids     = [var.create_network ? module.setup-network[0].subnet_ocid : var.subnet_ocid] 
}

resource "oci_functions_function" "fun1" {
  depends_on     = [null_resource.functionapp_push2ocir]
  application_id = oci_functions_application.functionapp.id
  display_name   = local.function_display_name
  image          = local.fn_image
  memory_in_mbs  =  var.functionmemory
  timeout_in_seconds = var.functiontimeoutsec
  config = {
    "ociDataSafeCompartmentOCID" : var.tenancy_ocid
    "ociOSTrackerBucketName" : local.tracker_bucket_name
    "ociLoggingLogOCID" : oci_logging_log.log_datadafe_auditdb.id
  }
  provisioner "local-exec" {
    command = "sleep 60"
  }
  
}

resource "oci_logging_log" "log_on_fn_invoke" {
  display_name = local.function_invoke_oci_logging_displayname
  log_group_id = oci_logging_log_group.log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.functionapp.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled = true
  
}


