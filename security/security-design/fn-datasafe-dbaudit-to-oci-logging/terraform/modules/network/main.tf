###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################


resource "oci_core_virtual_network" "vcn" {
  cidr_block     = var.vcn_cidr
  dns_label      = local.vcn_dns_label
  compartment_id = var.compartment_ocid
  display_name   = local.vcn_displayname
}

data "oci_core_services" "service_gateway_all_oci_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "service_gw" {

  compartment_id = var.compartment_ocid
  vcn_id          = oci_core_virtual_network.vcn.id
  services {
        service_id = lookup(data.oci_core_services.service_gateway_all_oci_services.services[0], "id")
  }
  display_name = local.service_gw_displayname
}

resource "oci_core_route_table" "rt_fn_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = local.vcnnameroutingtable_displayname
  
  route_rules {
    destination       = lookup(data.oci_core_services.service_gateway_all_oci_services.services[0], "cidr_block")
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.service_gw.id
    description = var.vcnroutingtabledescriptionservicegw
  }
  
}

resource "oci_core_dhcp_options" "dhcpoptions1" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = local.dhcpoptions_displayname
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }  
}

resource "oci_core_subnet" "vcn_subnet" {
  cidr_block        = var.subnet-cidr
  display_name      = local.subnet_displayname
  dns_label         = local.subnet_dns_label
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_virtual_network.vcn.id
  route_table_id    = oci_core_route_table.rt_fn_subnet.id
  dhcp_options_id   = oci_core_dhcp_options.dhcpoptions1.id
  prohibit_internet_ingress = true
  prohibit_public_ip_on_vnic = true
  security_list_ids = [oci_core_security_list.vcn_security_list.id]
}

resource "oci_core_security_list" "vcn_security_list"{
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name = local.vcn_securitylist_displayname

  egress_security_rules {
      stateless = false
      destination = "0.0.0.0/0"
      destination_type = "CIDR_BLOCK"
      protocol = "all" 
  }

  ingress_security_rules { 
      stateless = false
      source = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      # Get protocol numbers from https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml ICMP is 1  
      protocol = "1"
  
      # For ICMP type and code see: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml
      icmp_options {
        type = 3
        code = 4
      } 
  }   
  
  ingress_security_rules { 
      stateless = false
      source = var.vcn_cidr
      source_type = "CIDR_BLOCK"
      # Get protocol numbers from https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml ICMP is 1  
      protocol = "1"
  
      # For ICMP type and code see: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml
      icmp_options {
        type = 3
      } 
  }

}
