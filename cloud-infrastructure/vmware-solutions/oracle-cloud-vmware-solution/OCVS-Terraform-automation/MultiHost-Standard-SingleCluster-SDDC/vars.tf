
variable region { default = "eu-frankfurt-1"}
variable compartment_ocid { default = "ocid1.compartment.oc1..aaaaaaaaofmxfqtgasp3qilge44fmwhraxtkcqecpw6ge7vqhrhnt37aagma" }

# Network Setting
variable vcn_name {default = "SDDC-VCN"}
variable vcn_dns_label {default = "sddc"}
variable vcn_cidr {default = "10.0.0.0/16"}
variable subnet_esxi {default = "10.0.0.0/26"}
variable vlan_NSX_Uplink1 {default = "10.0.0.64/26"}
variable vlan_NSX_Uplink2 {default = "10.0.0.128/26"}
variable vlan_NSX_Edge_VTEP {default = "10.0.0.192/26"}
variable vlan_NSX_VTEP {default = "10.0.1.0/25"}
variable vlan_NSX_vMotion {default = "10.0.1.128/26"}
variable vlan_NSX_vSAN {default = "10.0.1.192/26"}
variable vlan_NSX_vSphere {default = "10.0.2.0/26"}
variable vlan_NSX_HCX {default = "10.0.2.64/26"}
variable vlan_NSX_ReplicationNet {default = "10.0.2.128/26"}
variable vlan_NSX_ProvisionNet {default = "10.0.2.192/26"}

# SDDC Settings
variable AD {default = 0} # the array index of the Availability Domains, possible values 0,1,2 (multi-ad_ or just 0 (single AD)
variable SDDC_name {default = "SDDC"}
variable SDDC_ESX_host_prefix_name {default = "ESXi"}
variable SDDC_commitment {default = "HOUR"} # possible: HOUR, MONTH, ONE_YEAR, THREE_YEARS
variable SDDC_vsphere_version {default = "8.0 update 1"} # possible: "7.0 update 3" or "8.0 update 1"
variable SDDC_ESXi_host_count {default = 3}
variable SDDC_shape {default = "BM.Standard2.52"}  # possible: "BM.Standard2.52", "BM.Standard3.64" or "BM.Standard.E4.128"
variable SDDC_core_count {default = 12}
variable SDDC_Primary_Cluster_Name {default = "Cluster1"}
variable SDDC_NSX-workload-Segment {default = "192.168.1.0/24"}
variable SDDC_ssh_public_key { default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDIQS8UDvLnTocbmm9q5ytQlO8MwE6BRhk3OVF/y2gfKbdQPGhKTisZCx8i0jJO8vPnp3a5ra0rg52LJ7UZ+FJNepbK//1Cb6iXPOP1nLft8FlvdC2YJOPrwYXAWL8ZQQY3W3qOID72vTwhns1ZJSAgSCn9gI8NUZCUwLxFMsQJwGtV+aPt2zsGnE1Vgzxsr795KgoRRt6E0UKT38BPxRkVXRp7JXwSjz8qLnqiAFp4JKFMCVud2pdyj0rQAMvb+QT49I4k9NKDQWzbjGRlsoUZDbc6lwnmo6jQ+pw3fZDS/CNi1+4udDJ6i5iaeU7hPnvQXfzSI3vOoFtrb83oZy2D phpseclib-generated-ke" }

# Block Volume for VMFS datastores Settings
variable SDDC_BlockVolume_name {default = "VMFS1"}
variable SDDC_BlockVolume_SizeInGB {default = 6144}
variable SDDC_BlockVolume_VPUs {default = 20}
