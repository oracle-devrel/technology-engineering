# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to define subnets to host MySQL.
# @author: Vijay Kokatnur

resource "oci_core_subnet" "snevndtmdb" {
  cidr_block                 = cidrsubnet(var.vcn_cidr, var.newbits, var.netnum)
  #cidr_block                 = var.subnet_cidr
  compartment_id             = var.compartment_id
  display_name               = var.label_prefix == "none" ? "snevndtmdb" : "${var.label_prefix}-snevndtmdb"
  dns_label                  = "snevndtmdb"
  freeform_tags              = var.freeform_tags
  prohibit_public_ip_on_vnic = false
  route_table_id             = var.ig_route_id
  security_list_ids          = [oci_core_security_list.slevndtmdb.id]
  vcn_id                     = var.vcn_id
}
