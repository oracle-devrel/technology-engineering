############################
#  OCI Tenancy Credentials #
############################
variable "tenancy_ocid" {
  description = "User Tenancy OCID"
}

variable "compartment_ocid" {
  description = "User Compartment OCID"
}

variable "primary_region" {
  description = "User Primary Region Value"
}

variable "standby_region" {
  description = "User Standby Region Value"
}


variable "user_ocid" {
  description = "User OCID"
}

variable "fingerprint" {
  description = "User Private Key Fingerprint"
}

variable "private_key_path" {
  description = "User Private Key Path"
}

###########################################
#  Oracle Cloud Infrastructure Variables  #
###########################################

variable "hub_vcn_primary_name" {
  description = "Hub VCN Primary name"
  default     = "hub_vcn_primary"
}

variable "hub_vcn_primary_cidr_block" {
  description = "Hub VCN Primary CIDR"
  default     = "10.15.0.0/24"
}

variable "hub_vcn_primary_transit_drg_rt_name" {
  description = "Hub VCN Primary Transit DRG RT name"
  default     = "hub_vcn_primary_transit_drg_rt"
}

variable "hub_vcn_primary_transit_drg_lpg_name" {
  description = "Hub VCN Primary Transit LPG RT name"
  default     = "hub_vcn_primary_transit_lpg_rt"
}

variable "vcn_primary_ocid" {
  description = "VCN Primary ocid"
}

variable "vcn_primary_client_subnet" {
  description = "VCN Primary Client Subnet"
}

variable "vcn_standby_client_subnet" {
  description = "VCN Standby Client Subnet"
}

variable "hub_primary_local_peering_gateway_name" {
  description = "Hub Primary Local Peering Gateway name "
  default     = "hub_primary_lpg"
}

variable "primary_local_peering_gateway_name" {
  description = "Primary Local Peering Gateway name "
  default     = "primary_lpg"
}

variable "oci_primary_drg_name" {
  description = "Primary DRG name"
  default     = "primary_drg"
}

variable "primary_drg_vcn_attachment_name" {
  description = "Primary DRG Hub VCN attachment name"
  default     = "primary_drg_hub_vcn_att"
}

variable "hub_vcn_standby_name" {
  description = "Hub VCN Standby name"
  default     = "hub_vcn_standby"
}

variable "hub_vcn_standby_cidr_block" {
  description = "Hub VCN Standby CIDR"
  default     = "10.16.0.0/24"
}

variable "hub_vcn_standby_transit_drg_rt_name" {
  description = "Hub VCN Standby Transit DRG RT name"
  default     = "hub_vcn_standby_transit_drg_rt"
}

variable "hub_vcn_standby_transit_drg_lpg_name" {
  description = "Hub VCN Standby Transit LPG RT name"
  default     = "hub_vcn_standby_transit_lpg_rt"
}

variable "vcn_standby_ocid" {
  description = "VCN Standby ocid"
}

variable "hub_standby_local_peering_gateway_name" {
  description = "Hub Standby Local Peering Gateway name "
  default     = "hub_standby_lpg"
}

variable "standby_local_peering_gateway_name" {
  description = "Standby Local Peering Gateway name "
  default     = "standby_lpg"
}

variable "oci_standby_drg_name" {
  description = "Standby DRG name"
  default     = "standby_drg"
}

variable "standby_drg_vcn_attachment_name" {
  description = "Standby DRG Hub VCN attachment name"
  default     = "standby_drg_hub_vcn_att"
}

variable "primary_drg_vcn_route_table_name" {
  description = "Primary DRG VCN RT name"
  default     = "primary_drg_vcn_rt"
}

variable "primary_drg_rpc_route_table_name" {
  description = "Primary DRG RPC RT name"
  default     = "primary_drg_rpc_rt"
}

variable "standby_drg_vcn_route_table_name" {
  description = "Standby DRG VCN RT name"
  default     = "standby_drg_vcn_rt"
}

variable "standby_drg_rpc_route_table_name" {
  description = "Standby DRG RPC RT name"
  default     = "standby_drg_rpc_rt"
}

variable "primary_drg_route_distribution_name" {
  description = "Primary DRG Route Distribution name"
  default     = "primary_drg_rd"
}

variable "primary_drg_remote_peering_connection_name" {
  description = "Primary DRG Remote Peering Connection name"
  default     = "primary_drg_rpc"
}

variable "standby_drg_route_distribution_name" {
  description = "Standby DRG Route Distribution name"
  default     = "standby_drg_rd"
}

variable "standby_drg_remote_peering_connection_name" {
  description = "Standby DRG Remote Peering Connection name"
  default     = "standby_drg_rpc"
}