###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################


#  Policies

resource "oci_identity_policy" "functionpolicy" {
  provider = oci.homeregion
  depends_on     = [oci_identity_dynamic_group.functionsservicedynamicgroup]
  name = local.policy_displayname
  description = var.PolicyDescription
  compartment_id = var.tenancy_ocid
  count = var.setup_policies ? 1 : 0
  statements = ["Allow dynamic-group ${oci_identity_dynamic_group.functionsservicedynamicgroup[0].name} to use log-content in compartment id ${var.compartment_ocid}", 
        "Allow dynamic-group ${oci_identity_dynamic_group.functionsservicedynamicgroup[0].name} to manage objects in compartment id ${var.compartment_ocid}",
        "Allow dynamic-group ${oci_identity_dynamic_group.functionsservicedynamicgroup[0].name} to read objectstorage-namespaces in compartment id ${var.compartment_ocid}", 
        "allow dynamic-group ${oci_identity_dynamic_group.functionsservicedynamicgroup[0].name} to read buckets in compartment id ${var.compartment_ocid}",
        "Allow dynamic-group ${oci_identity_dynamic_group.functionsservicedynamicgroup[0].name} to read data-safe-audit-events in tenancy"
        ]

  provisioner "local-exec" {
       command = "sleep 5"
  }
}

resource "oci_identity_dynamic_group" "functionsservicedynamicgroup" {
  provider = oci.homeregion
  name           = local.dynamicgroup_displayname
  description    =  var.dynamicgroupdescription
  compartment_id = var.tenancy_ocid
  count = var.setup_policies ? 1 : 0
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  provisioner "local-exec" {
    command = "sleep 5"
  }
}