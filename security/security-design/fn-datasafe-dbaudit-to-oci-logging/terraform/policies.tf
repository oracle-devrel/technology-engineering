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


# Functions Policies


resource "oci_identity_policy" "DataSafetoLoggingFunctionsPolicy" {
  provider = oci.homeregion
  depends_on     = [oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup]
  name = "${var.PolicyNamePrefix}-${local.compartment_name}-${random_id.tag.hex}"
  description = "${var.PolicyDescription}"
  compartment_id = var.tenancy_ocid
  count = var.setup_policies ? 1 : 0
  statements = ["Allow dynamic-group ${oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup[0].name} to use log-content in compartment id ${var.compartment_ocid} where target.loggroup.id=${oci_logging_log_group.log_group.id}", 
        "Allow dynamic-group ${oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup[0].name} to manage objects in compartment id ${var.compartment_ocid} where target.bucket.name=${oci_objectstorage_bucket.tracker-bucket.name}",
        "Allow dynamic-group ${oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup[0].name} to read objectstorage-namespaces in compartment id ${var.compartment_ocid} where target.bucket.name=${oci_objectstorage_bucket.tracker-bucket.name}", 
        "allow dynamic-group ${oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup[0].name} to read buckets in compartment id ${var.compartment_ocid} where target.bucket.name=${oci_objectstorage_bucket.tracker-bucket.name}",
        "Allow dynamic-group ${oci_identity_dynamic_group.DataSafetoLoggingFunctionsServiceDynamicGroup[0].name} to read data-safe-audit-events in tenancy"
        ]

  provisioner "local-exec" {
       command = "sleep 5"
  }
}

resource "oci_identity_dynamic_group" "DataSafetoLoggingFunctionsServiceDynamicGroup" {
  provider = oci.homeregion
  name           = "${var.DynamicGroupNamePrefix}-${local.compartment_name}-${random_id.tag.hex}"
  description    =  "${var.DynamicGroupDescription}"
  compartment_id = var.tenancy_ocid
  count = var.setup_policies ? 1 : 0
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  provisioner "local-exec" {
    command = "sleep 5"
  }
}
