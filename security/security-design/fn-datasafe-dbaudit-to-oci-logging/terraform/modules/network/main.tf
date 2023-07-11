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

resource "oci_core_virtual_network" "vcn" {
  cidr_block     = var.VCN-CIDR
  dns_label      = "${var.fnvcndnslabelprefix}${random_id.tag.hex}"
  compartment_id = var.compartment_ocid
  display_name   = "${var.fnvcnnameprefix}-${random_id.tag.hex}"
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
  display_name = "${var.fnvcnnameservicegatewayprefix}-${random_id.tag.hex}"
}

resource "oci_core_route_table" "rt_fn_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "${var.fnvcnnameroutingtableprefix}-${random_id.tag.hex}"
  
  route_rules {
    destination       = lookup(data.oci_core_services.service_gateway_all_oci_services.services[0], "cidr_block")
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.service_gw.id
    description = "${var.fnvcnroutingtabledescriptionervicegw}-${random_id.tag.hex}"
  }
  
}



resource "oci_core_dhcp_options" "dhcpoptions1" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "${var.fnvcnnamedhcpopitonsprefix}-${random_id.tag.hex}"
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }  
}

resource "oci_core_subnet" "function_ds_log_vcn" {
  cidr_block        = var.fnsubnet-CIDR
  display_name      = "${var.fnsubnetnameprefix}-${random_id.tag.hex}"
  dns_label         = "${var.fnsubnetdnslabelprefix}${random_id.tag.hex}"
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
  display_name = "${var.fnvcnnamesecuritylistprefix}-${random_id.tag.hex}"

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
      source = "10.0.0.0/16"
      source_type = "CIDR_BLOCK"
      # Get protocol numbers from https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml ICMP is 1  
      protocol = "1"
  
      # For ICMP type and code see: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml
      icmp_options {
        type = 3
      } 
  }

}
