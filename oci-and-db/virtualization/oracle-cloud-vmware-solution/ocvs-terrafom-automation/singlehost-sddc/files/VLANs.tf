resource oci_core_vlan export_VLAN-OCVS-NSX-Uplink1 {
  cidr_block          = var.vlan_NSX_Uplink1
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-NSX Edge Uplink 1"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1001"
  nsg_ids = [
    oci_core_network_security_group.export_UPLINK1_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_NSX_Uplink1.id
}

resource oci_core_vlan export_VLAN-OCVS-NSX-Uplink2 {
  cidr_block          = var.vlan_NSX_Uplink2
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-NSX Edge Uplink 2"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1002"
  nsg_ids = [
    oci_core_network_security_group.export_UPLINK2_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_NSX_Uplink2.id
}

resource oci_core_vlan export_VLAN-OCVS-NSX-Edge-VTEP {
  cidr_block          = var.vlan_NSX_Edge_VTEP
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-NSX Edge VTEP"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1003"
  nsg_ids = [
    oci_core_network_security_group.export_EdgeVTEP_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_NSX_Edge_VTEP.id
}

resource oci_core_vlan export_VLAN-OCVS-NSX-VTEP {
  cidr_block          = var.vlan_NSX_VTEP
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-NSX VTEP"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1004"
  nsg_ids = [
    oci_core_network_security_group.export_VTEP_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_NSX_VTEP.id
}

resource oci_core_vlan export_VLAN-OCVS-vMotion {
  cidr_block          = var.vlan_NSX_vMotion
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-vMotion"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1005"
  nsg_ids = [
    oci_core_network_security_group.export_vMOTION_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_vMotion.id
}

resource oci_core_vlan export_VLAN-OCVS-vSAN {
  cidr_block          = var.vlan_NSX_vSAN
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-vSAN"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1006"
  nsg_ids = [
    oci_core_network_security_group.export_vSAN_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_vSAN.id
}

resource oci_core_vlan export_VLAN-OCVS-vSphere {
  cidr_block          = var.vlan_NSX_vSphere
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-vSPHERE"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1007"
  nsg_ids = [
    oci_core_network_security_group.export_vSPHERE_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_vSphere.id
}

resource oci_core_vlan export_VLAN-OCVS-HCX {
  cidr_block          = var.vlan_NSX_HCX
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-HCX"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1008"
  nsg_ids = [
    oci_core_network_security_group.export_HCX_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_HCX.id
}

resource oci_core_vlan export_VLAN-OCVS-ReplicationNet {
  cidr_block          = var.vlan_NSX_ReplicationNet
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-Replication Net"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1009"
  nsg_ids = [
    oci_core_network_security_group.export_ReplicationNET_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_ReplicationNet.id
}

resource oci_core_vlan export_VLAN-OCVS-ProvisionNet {
  cidr_block          = var.vlan_NSX_ProvisionNet
  compartment_id      = var.compartment_ocid
  display_name        = "VLAN-Provision Net"
  vcn_id         = oci_core_vcn.export_sddc_vcn.id
  vlan_tag       = "1010"
  nsg_ids = [
    oci_core_network_security_group.export_ProvisionNET_nsg.id
  ]
  route_table_id = oci_core_route_table.export_route_table_VLAN_ProvisioningNet.id
}
