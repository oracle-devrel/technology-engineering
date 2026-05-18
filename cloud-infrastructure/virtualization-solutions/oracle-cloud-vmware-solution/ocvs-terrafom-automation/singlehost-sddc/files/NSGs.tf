
# --[ VLAN Edge Uplink 1 ]--------------------------------------------------
resource oci_core_network_security_group export_UPLINK1_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for Uplink1"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-UPLINK1-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_UPLINK1_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-UPLINK1-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_UPLINK1_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN Edge Uplink 2 ]--------------------------------------------------
# Uplink2 is unused by default, so no rules specified
resource oci_core_network_security_group export_UPLINK2_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for Uplink2"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-UPLINK2-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_UPLINK2_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-UPLINK2-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_UPLINK2_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN EdgeVTEP ]--------------------------------------------------
resource oci_core_network_security_group export_EdgeVTEP_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for Edge VTEP"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-EdgeVTEP-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_EdgeVTEP_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-EdgeVTEP-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_EdgeVTEP_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN VTEP ]--------------------------------------------------
resource oci_core_network_security_group export_VTEP_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSX for VTEP"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-VTEP-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_VTEP_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-VTEP-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_VTEP_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN vMOTION ]--------------------------------------------------
resource oci_core_network_security_group export_vMOTION_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for vMotion"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-vMOTION-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_vMOTION_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-vMOTION-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_vMOTION_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN vSAN ]--------------------------------------------------
resource oci_core_network_security_group export_vSAN_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for vSAN"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-vSAN-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_vSAN_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-vSAN-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_vSAN_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN vSPHERE ]--------------------------------------------------
resource oci_core_network_security_group export_vSPHERE_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for vSphere"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-vSPHERE-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_vSPHERE_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-vSPHERE-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_vSPHERE_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-vSPHERE-rule_3 {
  description = "Allow traffic to Internet"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_vSPHERE_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN HCX ]--------------------------------------------------
resource oci_core_network_security_group export_HCX_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG for HCX"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-HCX-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_HCX_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-HCX-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_HCX_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN ReplicationNET ]--------------------------------------------------
resource oci_core_network_security_group export_ReplicationNET_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSX for ReplicationNet"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-ReplicationNET-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_ReplicationNET_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-ReplicationNET-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_ReplicationNET_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}

# --[ VLAN ProvisionNET ]--------------------------------------------------
resource oci_core_network_security_group export_ProvisionNET_nsg {
  compartment_id = var.compartment_ocid
  display_name = "NSG ProvisionNet"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
}

resource oci_core_network_security_group_security_rule export_NSG-ProvisionNET-rule_1 {
  description = "Allow traffic from VCN"
  destination_type          = ""
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.export_ProvisionNET_nsg.id
  protocol                  = "all"
  source                    = var.vcn_cidr
  source_type               = "CIDR_BLOCK"
  stateless                 = "false"
}

resource oci_core_network_security_group_security_rule export_NSG-ProvisionNET-rule_2 {
  description = "Allow traffic to VCN"
  destination               = var.vcn_cidr
  destination_type          = "CIDR_BLOCK"
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.export_ProvisionNET_nsg.id
  protocol                  = "all"
  source_type               = ""
  stateless                 = "false"
}
