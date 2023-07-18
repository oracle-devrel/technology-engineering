# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration to define required datasources.
# @author: Vijay Kokatnur

data "oci_identity_availability_domain" "ad" {
  compartment_id = var.tenancy_id
  ad_number      = var.availability_domain
}

data "oci_core_images" "autonomous_images" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Autonomous Linux"
  operating_system_version = var.os_version
  shape                    = lookup(var.shape, "shape", "VM.Standard.E2.2")
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

data "oci_core_shapes" "current_ad" {
  compartment_id      = var.compartment_id
  availability_domain = element(local.ADs, 0)
}

// Get all the Availability Domains for the region and default backup policies
data "oci_identity_availability_domains" "ad" {
  compartment_id = var.compartment_id
}

data "oci_core_volume_backup_policies" "default_backup_policies" {}

data "oci_identity_availability_domains" "test_availability_domains" {
    #Required
    compartment_id = var.tenancy_id
}

data "oci_identity_fault_domains" "test_fault_domains" {
    #Required
    availability_domain = data.oci_identity_availability_domains.test_availability_domains.availability_domains[0].name
    compartment_id = var.compartment_id
}
