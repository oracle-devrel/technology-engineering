module "vcn" {
  source  = "oracle-terraform-modules/vcn/oci"
  #version = "3.6.0" # Use the latest version available on the Registry

  tenancy_id                = var.tenancy_ocid
  compartment_id            = local.compartment.id
  region                    = var.region           # e.g., "eu-frankfurt-1"
  vcn_name                  = var.vcn_name
  create_internet_gateway   = true
  create_nat_gateway        = true
  create_service_gateway    = true
  lockdown_default_seclist  = false

  # Optional: customize CIDR or DNS label
  vcn_cidrs     = ["10.0.0.0/16"]
  vcn_dns_label = "osmh"
}

#output "vcn" {
#  value = module.vcn
#}

resource "oci_core_subnet" "public_subnet" {
  compartment_id   = local.compartment.id
  vcn_id           = module.vcn.vcn_id
  display_name     = var.public_subnet_name
  cidr_block       = "10.0.0.0/24"

  # Route table and security list are outputs from the VCN module
  route_table_id      = module.vcn.ig_route_id
  security_list_ids   = [module.vcn.default_security_list_id]
  #dhcp_options_id     = module.vcn.default_dhcp_options_id
  prohibit_public_ip_on_vnic = false
}

resource "oci_core_network_security_group" "http_network_security_group" {
  #Required
  compartment_id   = local.compartment.id
  vcn_id           = module.vcn.vcn_id

  #Optional
  display_name = "HTTP"
}

resource "oci_core_network_security_group_security_rule" "http_network_security_group_security_rule" {
  network_security_group_id = oci_core_network_security_group.http_network_security_group.id
  protocol                  = "6"
  direction                 = "INGRESS"
  source                    = "0.0.0.0/0"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 80
      max = 80
    }
  }
}

resource "oci_core_network_security_group" "et_network_security_group" {
  #Required
  compartment_id   = local.compartment.id
  vcn_id           = module.vcn.vcn_id

  #Optional
  display_name = "EternalTerminal"
}

resource "oci_core_network_security_group_security_rule" "et_network_security_group_security_rule" {
  network_security_group_id = oci_core_network_security_group.et_network_security_group.id
  protocol                  = "6"
  direction                 = "INGRESS"
  source                    = "0.0.0.0/0"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 2022
      max = 2022
    }
  }
}

resource "oci_core_security_list" "default_security_list" {
  compartment_id = local.compartment.id
  vcn_id         = module.vcn.vcn_id
  display_name   = "default_security_list"

  // allow outbound tcp traffic on all ports
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "6"
  }

  // allow inbound ssh traffic from a specific port
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      // These values correspond to the destination port range.
      min = 22
      max = 22
    }
  }

  // allow inbound icmp traffic of a specific type
  ingress_security_rules {
    description = ""
    protocol    = 1
    source      = "0.0.0.0/0"
    stateless   = true

    icmp_options {
      type = 3
      code = 4
    }
  }
}
