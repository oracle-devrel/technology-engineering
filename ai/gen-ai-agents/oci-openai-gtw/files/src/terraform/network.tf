# --- Network ---
/* 
# To use a existing Landing Zone, add these variables in env.sh
#
# Landing Zone
# export TF_VAR_lz_app_cmp_ocid=$TF_VAR_compartment_ocid')
# export TF_VAR_lz_db_cmp_ocid=$TF_VAR_compartment_ocid')
# export TF_VAR_lz_network_cmp_ocid=$TF_VAR_compartment_ocid')
# export TF_VAR_lz_security_cmp_ocid=$TF_VAR_compartment_ocid')
# export TF_VAR_lz_vcn_ocid="XXXX"')
# export TF_VAR_lz_web_subnet_ocid="XXXX"')
# export TF_VAR_lz_app_subnet_ocid="XXXX"')
# export TF_VAR_lz_db_subnet_ocid="XXXX"')
#
# Existing VCN and Subnets
# variable "vcn_ocid" {}
# variable "web_subnet_ocid" {}
# variable "app_subnet_ocid" {}
# variable "db_subnet_ocid" {}

data "oci_core_vcn" "starter_vcn" {
  vcn_id = var.vcn_ocid
}

data "oci_core_subnet" "starter_web_subnet" {
  subnet_id = var.web_subnet_ocid
}

data "oci_core_subnet" "starter_app_subnet" {
  subnet_id = var.app_subnet_ocid
}

data "oci_core_subnet" "starter_db_subnet" {
  subnet_id = var.db_subnet_ocid
}
*/

# New VCN and Subnets
locals {
  cidr_vcn = "10.0.0.0/16"
  cidr_web_subnet = "10.0.1.0/24"
  cidr_app_subnet =  "10.0.2.0/24"
  cidr_db_subnet =  "10.0.3.0/24"  
}

resource "oci_core_vcn" "starter_vcn" {
  cidr_block     = local.cidr_vcn
  compartment_id = local.lz_network_cmp_ocid
  display_name   = "${var.prefix}-vcn"
  dns_label      = "${var.prefix}vcn"
  freeform_tags  = local.freeform_tags
}

resource "oci_core_internet_gateway" "starter_internet_gateway" {
  compartment_id = local.lz_network_cmp_ocid
  display_name   = "${var.prefix}-internet-gateway"
  vcn_id         = oci_core_vcn.starter_vcn.id
  freeform_tags  = local.freeform_tags
}

resource "oci_core_default_route_table" "default_route_table" {
  manage_default_resource_id = oci_core_vcn.starter_vcn.default_route_table_id
  display_name               = "DefaultRouteTable"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.starter_internet_gateway.id
  }
  freeform_tags = local.freeform_tags
}

# Public Subnet
resource "oci_core_subnet" "starter_web_subnet" {
  cidr_block        = local.cidr_web_subnet
  display_name      = "${var.prefix}-web-subnet"
  dns_label         = "${var.prefix}web"
  security_list_ids = [oci_core_vcn.starter_vcn.default_security_list_id, oci_core_security_list.starter_security_list.id]
  compartment_id    = local.lz_network_cmp_ocid
  vcn_id            = oci_core_vcn.starter_vcn.id
  route_table_id    = oci_core_vcn.starter_vcn.default_route_table_id
  dhcp_options_id   = oci_core_vcn.starter_vcn.default_dhcp_options_id
  freeform_tags     = local.freeform_tags
}

# App Subnet
resource "oci_core_subnet" "starter_app_subnet" {
  cidr_block        = local.cidr_app_subnet
  display_name      = "${var.prefix}-app-subnet"
  dns_label         = "${var.prefix}app"
  security_list_ids = [oci_core_vcn.starter_vcn.default_security_list_id, oci_core_security_list.starter_security_list.id]
  compartment_id    = local.lz_network_cmp_ocid
  vcn_id            = oci_core_vcn.starter_vcn.id
  route_table_id    = oci_core_route_table.starter_route_private.id
  dhcp_options_id   = oci_core_vcn.starter_vcn.default_dhcp_options_id
  freeform_tags     = local.freeform_tags
  prohibit_public_ip_on_vnic = true
}

# DB Subnet
resource "oci_core_subnet" "starter_db_subnet" {
  cidr_block        = local.cidr_db_subnet
  display_name      = "${var.prefix}-db-subnet"
  dns_label         = "${var.prefix}db"
  security_list_ids = [oci_core_vcn.starter_vcn.default_security_list_id, oci_core_security_list.starter_security_list.id]
  compartment_id    = local.lz_network_cmp_ocid
  vcn_id            = oci_core_vcn.starter_vcn.id
  route_table_id    = oci_core_route_table.starter_route_private.id
  dhcp_options_id   = oci_core_vcn.starter_vcn.default_dhcp_options_id
  freeform_tags     = local.freeform_tags
  prohibit_public_ip_on_vnic = true
}

resource "oci_core_security_list" "starter_security_list" {
  compartment_id = local.lz_network_cmp_ocid
  vcn_id         = oci_core_vcn.starter_vcn.id
  display_name   = "${var.prefix}-security-list"

  ingress_security_rules {
    protocol  = "6" // tcp
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol  = "6" // tcp
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 80
      max = 80
    }
  }

  // XXXXXX 0.0.0.0/0 ??
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 8080
      max = 8080
    }
  }  

  // Oracle TNS Listener port
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 1521
      max = 1522
    }
  }  

  // MySQL listener port: XXX optional ?
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 3306
      max = 3306
    }
  }  

  // MySQL listener port_x: XXX optional ?
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 33060
      max = 33060
    }
  }  

  // PostgreSQL
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 5432
      max = 5433
    }
  }  

  // Opensearch
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 9200
      max = 9200
    }
  }  

  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 5601
      max = 5601
    }
  }
  
  // External access to Kubernetes API endpoint
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 6443
      max = 6443
    }
  }  

  // Kubernetes worker to control plane communication
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 12250
      max = 12250
    }
  }  

  // K8S Ingress-Controller
  ingress_security_rules {
    protocol  = "6" // tcp
    source    = local.cidr_vcn
    stateless = false

    tcp_options {
      min = 8443
      max = 8443
    }
  }  

  freeform_tags = local.freeform_tags
}

# Compatibility with network_existing.tf
data "oci_core_vcn" "starter_vcn" {
  vcn_id = oci_core_vcn.starter_vcn.id
}

data "oci_core_subnet" "starter_web_subnet" {
  subnet_id = oci_core_subnet.starter_web_subnet.id
}

data "oci_core_subnet" "starter_app_subnet" {
  subnet_id = oci_core_subnet.starter_app_subnet.id
} 

data "oci_core_subnet" "starter_db_subnet" {
  subnet_id = oci_core_subnet.starter_db_subnet.id
} 

# NAT Gateway
resource "oci_core_nat_gateway" "starter_nat_gateway" {
  compartment_id = local.lz_network_cmp_ocid
  vcn_id         = oci_core_vcn.starter_vcn.id
  display_name   = "${var.prefix}-nat-gateway"
  freeform_tags  = local.freeform_tags
}

# Service Gateway
resource "oci_core_service_gateway" "starter_service_gateway" {
  compartment_id = local.lz_network_cmp_ocid
  services {
    service_id = data.oci_core_services.all_services.services[0]["id"]
  }
  vcn_id         = oci_core_vcn.starter_vcn.id

  display_name   = "${var.prefix}-service-gateway"
  freeform_tags  = local.freeform_tags
}

# Route Private Subnet
resource "oci_core_route_table" "starter_route_private" {
  compartment_id = local.lz_network_cmp_ocid
  vcn_id         = oci_core_vcn.starter_vcn.id
  display_name   = "${var.prefix}-route-private"

  route_rules {
    destination       = data.oci_core_services.all_services.services[0]["cidr_block"]
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.starter_service_gateway.id
  }  
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.starter_nat_gateway.id
  }
}