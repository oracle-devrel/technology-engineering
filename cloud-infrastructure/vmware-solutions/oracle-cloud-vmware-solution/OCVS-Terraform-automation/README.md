# Oracle Cloud VMware Solution - Terraform Automation

An OCVS (Oracle Cloud VMware Solution) environment comprises multiple hosts (Bare Metal Servers). 
This means that some operations need to be repeated multiple times
and therefore it would be easier to automate.

Terraform allows you to automate operations / modifications towards your
OCVS environment in an easy way. Using the Terraform data sources, you can easily read
out all servers in your OCVS environment and execute modifications against them

```tf
#example of getting all Hosts that are part of an OCVS environment
data oci_ocvp_esxi_hosts export_esxi_hosts{
  sddc_id = var.SDDC_OCID
}
```

### New VLAN Assignment to your OCVS environment

If you want to have a new extra VLAN for OCVS environment, you would need to do the following steps
before you can use the VLAN on your Distributed Switch.
1. Create the VLAN in the VCN
2. For every ESXi hosts add a vNIC attached to this VLAN on nic0
3. For every ESXi hosts add a vNIC attached to this VLAN on nic3

Doing this manually can be error prone, so using Terraform is a much easier way. 

Here is a terraform example of creating a VLAN and assigning it to every ESXi host.

```tf
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
```
