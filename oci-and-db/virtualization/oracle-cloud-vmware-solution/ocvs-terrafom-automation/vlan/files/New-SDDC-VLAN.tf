variable region {default = "your_region"}  #example: eu-frankfurt-1
variable SDDC_OCID {default = "OCID_of_your_SDDC"}
variable VCN_OCID { default = "OCID_of_your_VCN_That_the_VLAN_will_be_created_into"}
variable VLAN_Name { default = "VLAN-Name"}
variable VLAN_CIDR { default = "VLAN_CIDR_RANGE"}  #example: 192.168.1.0/24 -> Range needs to be within VCN range
variable VLAN_TAG_ID  { default = 2000}  # Change number for unique VLAN ID

provider oci {
	region = var.region
}

#Get VCN information to leverage the same compartment ID
data "oci_core_vcn" "test_vcn" {
    vcn_id = var.VCN_OCID
}

# Create VLAN in the specified VCN
resource "oci_core_vlan" "new_vlan" {
    cidr_block = var.VLAN_CIDR
    compartment_id = data.oci_core_vcn.test_vcn.compartment_id
    vcn_id = var.VCN_OCID
    display_name =var.VLAN_Name
    vlan_tag = var.VLAN_TAG_ID
}

# Get all hosts attached to the OCVS environment
data oci_ocvp_esxi_hosts export_esxi_hosts {
    sddc_id = var.SDDC_OCID
}

# Get VLAN OCID so it can be assigned to the ESXi hosts
data oci_core_vlan attach_vlan {
    vlan_id = oci_core_vlan.new_vlan.id
}

# For Each ESXi hosts create VNIC and attach to VLAN on NIC0
resource "oci_core_vnic_attachment" "vnic_attachment-nic0" {
    count = length(data.oci_ocvp_esxi_hosts.export_esxi_hosts.esxi_host_collection)
    create_vnic_details {
        display_name = "${data.oci_core_vlan.attach_vlan.display_name}-Nic0"
        vlan_id = oci_core_vlan.new_vlan.id
    }
    instance_id =  data.oci_ocvp_esxi_hosts.export_esxi_hosts.esxi_host_collection[count.index].compute_instance_id
    nic_index = 0
}

# For Each ESXi hosts create VNIC and attach to VLAN on NIC1
resource "oci_core_vnic_attachment" "vnic_attachment-nic1" {
    count = length(data.oci_ocvp_esxi_hosts.export_esxi_hosts.esxi_host_collection)
    create_vnic_details {
        display_name = "${data.oci_core_vlan.attach_vlan.display_name}-Nic1"
        vlan_id = oci_core_vlan.new_vlan.id
    }
    instance_id =  data.oci_ocvp_esxi_hosts.export_esxi_hosts.esxi_host_collection[count.index].compute_instance_id
    nic_index = 1
}