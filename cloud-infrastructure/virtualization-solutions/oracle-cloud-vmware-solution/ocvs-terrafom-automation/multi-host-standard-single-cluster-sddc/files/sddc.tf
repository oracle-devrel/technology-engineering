resource "oci_ocvp_sddc" "export_sddc" {
    compartment_id = var.compartment_ocid
    initial_configuration {
        initial_cluster_configurations {
            compute_availability_domain = data.oci_identity_availability_domains.export_availability_domains.availability_domains[0].name
            esxi_hosts_count = var.SDDC_ESXi_host_count
            network_configuration {
                nsx_edge_vtep_vlan_id = oci_core_vlan.export_VLAN-OCVS-NSX-Edge-VTEP.id
                nsx_vtep_vlan_id = oci_core_vlan.export_VLAN-OCVS-NSX-VTEP.id
                provisioning_subnet_id = oci_core_subnet.export_Subnet-OCVS.id
                vmotion_vlan_id = oci_core_vlan.export_VLAN-OCVS-vMotion.id
                vsan_vlan_id = oci_core_vlan.export_VLAN-OCVS-vSAN.id
                hcx_vlan_id = oci_core_vlan.export_VLAN-OCVS-HCX.id
                nsx_edge_uplink1vlan_id = oci_core_vlan.export_VLAN-OCVS-NSX-Uplink1.id
                nsx_edge_uplink2vlan_id = oci_core_vlan.export_VLAN-OCVS-NSX-Uplink2.id
                provisioning_vlan_id = oci_core_vlan.export_VLAN-OCVS-ProvisionNet.id
                replication_vlan_id = oci_core_vlan.export_VLAN-OCVS-ReplicationNet.id
                vsphere_vlan_id = oci_core_vlan.export_VLAN-OCVS-vSphere.id
            }
            vsphere_type = "MANAGEMENT"

            display_name = var.SDDC_Primary_Cluster_Name
            initial_commitment = var.SDDC_commitment
            initial_host_ocpu_count = var.SDDC_core_count
            initial_host_shape_name = var.SDDC_shape
            instance_display_name_prefix = var.SDDC_ESX_host_prefix_name
            workload_network_cidr = var.SDDC_NSX-workload-Segment

            datastores {
               block_volume_ids = [oci_core_volume.export_VMFS_Management_datastore_volume.id]
               datastore_type = "MANAGEMENT"
            }
            datastores {
               block_volume_ids = [oci_core_volume.export_VMFS_datastore_volume.id]
               datastore_type = "WORKLOAD"
            }


        }
    }
    ssh_authorized_keys = var.SDDC_ssh_public_key
    vmware_software_version = var.SDDC_vsphere_version
    display_name = var.SDDC_name
    is_single_host_sddc = false
    is_hcx_enabled = true
}