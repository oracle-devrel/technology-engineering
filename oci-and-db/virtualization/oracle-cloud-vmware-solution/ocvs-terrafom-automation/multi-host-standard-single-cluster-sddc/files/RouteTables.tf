resource "oci_core_route_table" "export_route_table_SDDC_Subnet" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table SDDC Subnet"
}

#The vSphere VLAN needs internet access during provisioning!
#This is to properly licence the vCenter and HCX Components
resource "oci_core_route_table" "export_route_table_VLAN_vSphere" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table vSphere vLAN"
    route_rules {
        network_entity_id = oci_core_nat_gateway.sddc_nat_gateway.id
        description = "Internet access via NAT Gateway"
        destination = "0.0.0.0/0"
        destination_type = "CIDR_BLOCK"
    }
}

resource "oci_core_route_table" "export_route_table_VLAN_NSX_Uplink1" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table NSX Uplink1 VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_NSX_Uplink2" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table NSX Uplink2 VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_NSX_Edge_VTEP" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table NSX Edge VTEP VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_NSX_VTEP" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table NSX VTEP VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_vMotion" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table vMotion VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_vSAN" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table vSAN VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_HCX" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table HCX VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_ReplicationNet" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table Replication VLAN"
}

resource "oci_core_route_table" "export_route_table_VLAN_ProvisioningNet" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "Route Table ProvisioningNet VLAN"
}

