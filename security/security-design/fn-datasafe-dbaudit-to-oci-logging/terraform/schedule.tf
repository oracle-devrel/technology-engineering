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



resource "oci_ons_notification_topic" "schedule_ds_ocilogging_notification_topic" {
    #Required
    compartment_id = var.compartment_ocid
    name = "${var.NotificationTopicNamePrefix}-${var.deployment_name}-${random_id.tag.hex}"
}

resource "oci_ons_subscription" "schedule_ds_ocilogging_notification_subscription" {
    #Required
    compartment_id = var.compartment_ocid
    endpoint = oci_functions_function.postauditlogs.id
    protocol = "ORACLE_FUNCTIONS"
    topic_id = oci_ons_notification_topic.schedule_ds_ocilogging_notification_topic.id
}

resource "oci_monitoring_alarm" "schedule_ds_ocilogging_alarm" {
    #Required
    compartment_id = var.compartment_ocid
    destinations = [oci_ons_notification_topic.schedule_ds_ocilogging_notification_topic.id]
    display_name = "${var.AlarmNamePrefix}-${var.deployment_name}-${random_id.tag.hex}"
    is_enabled = "true"
    metric_compartment_id =  var.compartment_ocid
    namespace = "oci_faas"
    query = "FunctionInvocationCount[1d].count() >= 0"
    severity = "INFO"

    #Optional
    pending_duration = "PT1M"
    repeat_notification_duration = "PT1M"
}