#====================================================
# Create VLAN and assign to OpenShift Worker Nodes 
#====================================================

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
}

#====================================================
# Define variables
#====================================================
variable "OpenShiftNameSpace" {
  description = "The namespace for the OpenShift environment"
  type        = string
  default     = "---OCI Namespace that is being used for your OpenShift Cluster---"
}

variable "compartment_id" {
  description = "The compartment OCID in which to create resources"
  type        = string
  default     = "---OCID of the Compartment the OpenShift cluster is in---"
}

variable "vcn_id" {
  description = "The OCID of the VCN in which the VLAN (subnet) will be created"
  type        = string
  default     = "---OCID of the VCN your are using---"
}

variable "vlan_cidr" {
  description = "The CIDR block for the VLAN (subnet) to be created"
  type        = string
  default     = "10.0.101.0/24"  # Change to CIDR range that is part of your VCN and is still available
}

variable "vlan_name" {
  description = "Name of the VLAN"
  type        = string
  default     = "EgressVLAN"   
}

#====================================================
# Create VLAN in existing (specified) VCN
#====================================================
resource "oci_core_vlan" "new_vlan" {
  compartment_id = var.compartment_id
  vcn_id         = var.vcn_id
  cidr_block     = var.vlan_cidr
  display_name   = "vlan-${var.vlan_name}"
}

#====================================================
# DATA SOURCE: GET Openshift Worker Nodes based on tag
#====================================================
data "oci_core_instances" "compute_instances" {
  compartment_id = var.compartment_id

  filter {
    # Use defined tag filtering syntax: defined_tags.<namespace>.<tag-key>
    name   = "defined_tags.${var.OpenShiftNameSpace}.instance-role"
    values = ["compute"]
  }
}

#====================================================
# LOCALS: Create list of Worker nodes instances
#====================================================
locals {
  compute_instances = {
    for instance in data.oci_core_instances.compute_instances.instances :
    instance.id => instance
  }
}

#====================================================
# Attach VLAN to each worker node
#====================================================
resource "oci_core_vnic_attachment" "vlan_vnic" {
  for_each = local.compute_instances
    instance_id = each.key
    create_vnic_details{
      display_name = "vlan-${var.vlan_name}"    
      vlan_id = oci_core_vlan.new_vlan.id
    }
}
