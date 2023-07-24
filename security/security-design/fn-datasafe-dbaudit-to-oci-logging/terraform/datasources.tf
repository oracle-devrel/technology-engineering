###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

data "oci_identity_region_subscriptions" "home_region_subscriptions" {
  tenancy_id = var.tenancy_ocid

  filter {
    name   = "is_home_region"
    values = [true]
  }
}

data "oci_identity_regions" "oci_regions" {

  filter {
    name   = "name"
    values = [var.region]
  }

}

data "oci_identity_tenancy" "oci_tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_objectstorage_namespace" "namespace" {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_compartment" "compartment" {
  id = var.compartment_ocid
}

data "oci_identity_users" "user" {
  compartment_id = var.tenancy_ocid
}

