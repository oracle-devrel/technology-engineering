resource "oci_core_network_security_group" "oke_lb_nsg_frontend" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "oke-lb-frontend"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
}

# HTTP traffic (port 80)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_http_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  source_type               = "CIDR_BLOCK"
  source                    = "0.0.0.0/0"
  stateless                 = true
  description               = "Allow HTTP ingress traffic from anywhere on port 80"
  tcp_options {
    destination_port_range {
      max = 80
      min = 80
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_http_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = "0.0.0.0/0"
  stateless                 = true
  description               = "Allow HTTP egress traffic to anywhere on port 80"
  tcp_options {
    source_port_range {
      max = 80
      min = 80
    }
  }
}

# HTTPS traffic (port 443)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_https_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  source_type               = "CIDR_BLOCK"
  source                    = "0.0.0.0/0"
  stateless                 = true
  description               = "Allow HTTPS ingress traffic from anywhere on port 443"
  tcp_options {
    destination_port_range {
      max = 443
      min = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_https_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = "0.0.0.0/0"
  stateless                 = true
  description               = "Allow HTTPS egress traffic to anywhere on port 443"
  tcp_options {
    source_port_range {
      max = 443
      min = 443
    }
  }
}
