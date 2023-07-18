# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration to define required datasources.
# @author: Vijay Kokatnur

## Get a list of Availability Domains 
data "oci_identity_availability_domains" "test_availability_domains" {
    #Required
    compartment_id = var.tenancy_id
}

data "oci_identity_fault_domains" "test_fault_domains" {
    #Required
    availability_domain = data.oci_identity_availability_domains.test_availability_domains.availability_domains[0].name
    compartment_id = var.compartment_id
}

data "oci_core_volume_backup_policies" "default_backup_policies" {}
