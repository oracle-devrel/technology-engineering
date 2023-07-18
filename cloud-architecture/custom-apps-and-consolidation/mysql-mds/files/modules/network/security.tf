# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to define security lists for MySQL ports - 3306, 33060
# @author: Vijay Kokatnur

resource "oci_core_security_list" "slevndtmdb" {
  compartment_id = var.compartment_id  
  vcn_id = var.vcn_id
  display_name   = var.label_prefix == "none" ? "slevndtmdb" : "${var.label_prefix}-slevndtmdb"
  freeform_tags  = var.freeform_tags

  egress_security_rules {
    protocol    = local.all_protocols
    destination = local.anywhere
  }

  ingress_security_rules {
    #Required
    protocol = local.tcp_protocol
    source = "0.0.0.0/0"

    #Optional
    description = "ingress port 22 for SSH"
    source_type = "CIDR_BLOCK"
    stateless = false
    tcp_options {
        #Optional
        max = local.ssh_port
        min = local.ssh_port
    }
  }

  ingress_security_rules {
    #Required
    protocol = local.tcp_protocol
    source = "0.0.0.0/0"

    #Optional
    description = "ingress port 3306 for MySQL DB"
    source_type = "CIDR_BLOCK"
    stateless = false
    tcp_options {
        #Optional
        max = "3306"
        min = "3306"
    }
  }

  ingress_security_rules {
    #Required
    protocol = local.tcp_protocol
    source = "0.0.0.0/0"

    #Optional
    description = "ingress port 33060 for MySQL DB"
    source_type = "CIDR_BLOCK"
    stateless = false
    tcp_options {
        #Optional
        max = "33060"
        min = "33060"
    }
  }

  lifecycle {
    ignore_changes = [
      egress_security_rules, ingress_security_rules
    ]
  }
}
