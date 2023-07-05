################################################################################
#Copyright (c) 2023 Oracle and/or its affiliates.
# 
#The Universal Permissive License (UPL), Version 1.0
# 
#Subject to the condition set forth below, permission is hereby granted to any
#person obtaining a copy of this software, associated documentation and/or data
#(collectively the "Software"), free of charge and under any and all copyright
#rights in the Software, and any and all patent rights owned or freely
#licensable by each licensor hereunder covering either (i) the unmodified
#Software as contributed to or provided by such licensor, or (ii) the Larger
#Works (as defined below), to deal in both
# 
#(a) the Software, and
#(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
#one is included with the Software (each a "Larger Work" to which the Software
#is contributed by such licensors),
 
#without restriction, including without limitation the rights to copy, create
#derivative works of, display, perform, and distribute the Software and make,
#use, sell, offer for sale, import, export, have made, and have sold the
#Software and the Larger Work(s), and to sublicense the foregoing rights on
#either these or other terms.
 
#This license is subject to the following condition:
#The above copyright notice and either this complete permission notice or at
#a minimum a reference to the UPL must be included in all copies or
#substantial portions of the Software.
 
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
################################################################################

resource "oci_functions_application" "DataSafeAuditDBtoLoggingApp" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.FunctionAppNamePrefix}-${var.deployment_name}-${random_id.tag.hex}"
  subnet_ids     = [var.create_network ? module.setup-network[0].fnsubnet_ocid : var.subnet_ocid] 
}

resource "oci_functions_function" "postauditlogs" {
  depends_on     = [null_resource.DataSafeAuditDBtoLoggingPush2OCIR]
  application_id = oci_functions_application.DataSafeAuditDBtoLoggingApp.id
  display_name   = "${var.FunctionNamePrefix}-${var.deployment_name}"
  #image          = "${local.ocir_docker_repository}/${local.namespace}/${var.ocir_repo_name}/${var.FunctionNamePrefix}:0.0.1"
  image          = "${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}/${var.FunctionNamePrefix}:0.0.1"
  memory_in_mbs  =  var.FunctionMemory
  timeout_in_seconds = var.FunctionTimeoutSec
  config = {
    "ociDataSafeCompartmentOCID" : "${var.tenancy_ocid}"
    "ociOSTrackerBucketName" : "${oci_objectstorage_bucket.tracker-bucket.name}",
    "ociLoggingLogOCID" : "${oci_logging_log.log_datadafe_auditdb.id}"
  }
  
}

resource "oci_logging_log" "log_on_fn_invoke" {
  display_name = "${var.FunctionInvokeOCILoggingName}-${var.deployment_name}-${random_id.tag.hex}"
  log_group_id = oci_logging_log_group.log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.DataSafeAuditDBtoLoggingApp.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled = true
  
}


