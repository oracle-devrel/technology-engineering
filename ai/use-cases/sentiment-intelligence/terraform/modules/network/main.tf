# =============================================================================
# Networking Module — VCN, Subnets, Security Lists, Gateways, Route Tables
# =============================================================================

# ---------- VCN ----------
resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.resource_prefix}-vcn"
  cidr_blocks    = [var.vcn_cidr_block]
  dns_label      = replace(var.resource_prefix, "-", "")
  freeform_tags  = var.freeform_tags
}

# ---------- Internet Gateway ----------
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-igw"
  enabled        = true
  freeform_tags  = var.freeform_tags
}

# ---------- NAT Gateway ----------
resource "oci_core_nat_gateway" "natgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-natgw"
  freeform_tags  = var.freeform_tags
}

# ---------- Service Gateway ----------
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "sgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-sgw"
  freeform_tags  = var.freeform_tags

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }
}

# ---------- Route Tables ----------
resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-public-rt"
  freeform_tags  = var.freeform_tags

  route_rules {
    network_entity_id = oci_core_internet_gateway.igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-private-rt"
  freeform_tags  = var.freeform_tags

  route_rules {
    network_entity_id = oci_core_nat_gateway.natgw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }

  route_rules {
    network_entity_id = oci_core_service_gateway.sgw.id
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}

# ---------- Security Lists ----------
resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-public-sl"
  freeform_tags  = var.freeform_tags

  # Allow inbound HTTP
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 80
      max = 80
    }
  }

  # Allow inbound HTTPS
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 443
      max = 443
    }
  }

  # Allow inbound Kubernetes API
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_security_list" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-private-sl"
  freeform_tags  = var.freeform_tags

  # Allow inbound from VCN
  ingress_security_rules {
    protocol    = "all"
    source      = var.vcn_cidr_block
    source_type = "CIDR_BLOCK"
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_security_list" "db" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-db-sl"
  freeform_tags  = var.freeform_tags

  # Allow inbound from private subnet (worker nodes)
  ingress_security_rules {
    protocol    = "6"
    source      = var.private_subnet_cidr
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 1521
      max = 1522
    }
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# ---------- NSG for ADB ----------
resource "oci_core_network_security_group" "db_nsg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.resource_prefix}-db-nsg"
  freeform_tags  = var.freeform_tags
}

resource "oci_core_network_security_group_security_rule" "db_ingress" {
  network_security_group_id = oci_core_network_security_group.db_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.private_subnet_cidr
  source_type               = "CIDR_BLOCK"

  tcp_options {
    destination_port_range {
      min = 1521
      max = 1522
    }
  }
}

# ---------- Subnets ----------
resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  display_name               = "${var.resource_prefix}-public-subnet"
  cidr_block                 = var.public_subnet_cidr
  dns_label                  = "pub"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
  freeform_tags              = var.freeform_tags
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  display_name               = "${var.resource_prefix}-private-subnet"
  cidr_block                 = var.private_subnet_cidr
  dns_label                  = "priv"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.private.id]
  freeform_tags              = var.freeform_tags
}

resource "oci_core_subnet" "db" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  display_name               = "${var.resource_prefix}-db-subnet"
  cidr_block                 = var.db_subnet_cidr
  dns_label                  = "db"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.db.id]
  freeform_tags              = var.freeform_tags
}
