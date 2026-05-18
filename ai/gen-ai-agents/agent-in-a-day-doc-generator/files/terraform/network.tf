# --- VCN + Public Subnet for MCP Server ---

locals {
  cidr_vcn            = "10.1.0.0/16"
  cidr_subnet         = "10.1.1.0/24"
  cidr_private_subnet = "10.1.2.0/24"
}

resource "oci_core_vcn" "mcp_vcn" {
  cidr_block     = local.cidr_vcn
  compartment_id = var.compartment_ocid
  display_name   = "${var.prefix}-vcn"
  dns_label      = "${var.prefix}vcn"
  freeform_tags  = local.freeform_tags
}

resource "oci_core_internet_gateway" "mcp_igw" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.prefix}-igw"
  vcn_id         = oci_core_vcn.mcp_vcn.id
  freeform_tags  = local.freeform_tags
}

resource "oci_core_default_route_table" "default_rt" {
  manage_default_resource_id = oci_core_vcn.mcp_vcn.default_route_table_id
  display_name               = "${var.prefix}-default-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.mcp_igw.id
  }
  freeform_tags = local.freeform_tags
}

resource "oci_core_security_list" "mcp_seclist" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn.id
  display_name   = "${var.prefix}-seclist"

  # SSH
  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false
    tcp_options {
      min = 22
      max = 22
    }
  }

  # MCP server (port 8000)
  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false
    tcp_options {
      min = 8000
      max = 8000
    }
  }

  # HTTPS for API Gateway (port 443)
  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false
    tcp_options {
      min = 443
      max = 443
    }
  }

  # DNS resolution (required by OCI Agent API endpoint tool)
  ingress_security_rules {
    protocol  = "17"
    source    = "0.0.0.0/0"
    stateless = false
    udp_options {
      min = 53
      max = 53
    }
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }

  freeform_tags = local.freeform_tags
}

# --- NAT Gateway + Private Subnet for OCI Agent PE ---

resource "oci_core_nat_gateway" "mcp_natgw" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.prefix}-natgw"
  vcn_id         = oci_core_vcn.mcp_vcn.id
  freeform_tags  = local.freeform_tags
}

resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mcp_vcn.id
  display_name   = "${var.prefix}-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.mcp_natgw.id
  }
  freeform_tags = local.freeform_tags
}

resource "oci_core_subnet" "agent_private_subnet" {
  cidr_block                 = local.cidr_private_subnet
  display_name               = "${var.prefix}-agent-subnet"
  dns_label                  = "${var.prefix}agt"
  prohibit_public_ip_on_vnic = true
  security_list_ids          = [oci_core_vcn.mcp_vcn.default_security_list_id, oci_core_security_list.mcp_seclist.id]
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.mcp_vcn.id
  route_table_id             = oci_core_route_table.private_rt.id
  dhcp_options_id            = oci_core_vcn.mcp_vcn.default_dhcp_options_id
  freeform_tags              = local.freeform_tags
}

resource "oci_core_subnet" "mcp_subnet" {
  cidr_block        = local.cidr_subnet
  display_name      = "${var.prefix}-subnet"
  dns_label         = "${var.prefix}sub"
  security_list_ids = [oci_core_vcn.mcp_vcn.default_security_list_id, oci_core_security_list.mcp_seclist.id]
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.mcp_vcn.id
  route_table_id    = oci_core_vcn.mcp_vcn.default_route_table_id
  dhcp_options_id   = oci_core_vcn.mcp_vcn.default_dhcp_options_id
  freeform_tags     = local.freeform_tags
}
