resource "oci_core_network_security_group" "oke_lb_nsg_frontend" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "oke-lb-frontend"
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_80_ingress_rule" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = true
  description = "Allow HTTP traffic from everywhere"
  tcp_options {
    destination_port_range {
      max = 80
      min = 80
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_80_egress_rule_stateless" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = true
  description = "Allow HTTP traffic from everywhere - stateless egress"
  tcp_options {
    source_port_range {
      max = 80
      min = 80
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_443_ingress_rule" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = true
  description = "Allow HTTPS traffic from everywhere"
  tcp_options {
    destination_port_range {
      max = 443
      min = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_frontend_443_egress_rule_stateless" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg_frontend.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = true
  description = "Allow HTTP traffic from everywhere - stateless egress"
  tcp_options {
    source_port_range {
      max = 443
      min = 443
    }
  }
}