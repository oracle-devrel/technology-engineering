##############################
# ------ Region Primary ---- #
##############################

# ------ Create Hub VCN Primary 
resource "oci_core_vcn" "hub_vcn_primary" {
  provider = oci.region-primary
  compartment_id = var.compartment_ocid
  display_name   = var.hub_vcn_primary_name
  cidr_block     = var.hub_vcn_primary_cidr_block
}

# ------ Create Hub VCN Primary Transit DRG Route Table
resource "oci_core_route_table" "hub_vcn_primary_transit_drg_rt" {
    provider = oci.region-primary
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_primary.id
    display_name       = var.hub_vcn_primary_transit_drg_rt_name
    route_rules {
        network_entity_id = oci_core_local_peering_gateway.hub_primary_local_peering_gateway.id
        destination = data.oci_core_vcn.vcn_primary.cidr_block
        destination_type = "CIDR_BLOCK"
    }
}

# ------ Create Hub VCN Primary Transit LPG Route Table
resource "oci_core_route_table" "hub_vcn_primary_transit_lpg_rt" {
    provider = oci.region-primary
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_primary.id
    display_name       = var.hub_vcn_primary_transit_drg_lpg_name
    route_rules {
        network_entity_id = oci_core_drg.primary_drg.id
        destination = data.oci_core_vcn.vcn_standby.cidr_block
        destination_type = "CIDR_BLOCK"
    }
}

# ------ Create Hub Primary LPG
resource "oci_core_local_peering_gateway" "hub_primary_local_peering_gateway" {
    provider = oci.region-primary
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_primary.id
    display_name = var.hub_primary_local_peering_gateway_name
    peer_id = oci_core_local_peering_gateway.primary_local_peering_gateway.id
    route_table_id = oci_core_route_table.hub_vcn_primary_transit_lpg_rt.id
}

# ------ Create Primary LPG
resource "oci_core_local_peering_gateway" "primary_local_peering_gateway" {
    provider = oci.region-primary
    compartment_id = var.compartment_ocid
    vcn_id = var.vcn_primary_ocid
    display_name = var.primary_local_peering_gateway_name
}

# ------ Create Primary DRG
resource "oci_core_drg" "primary_drg" {
  provider = oci.region-primary
  compartment_id = var.compartment_ocid
  display_name   = var.oci_primary_drg_name
}

# ------ Create Primary DRG Hub VCN attachment
resource "oci_core_drg_attachment" "primary_drg_vcn_attachment" {
  provider = oci.region-primary
  vcn_id             = oci_core_vcn.hub_vcn_primary.id
  drg_id             = oci_core_drg.primary_drg.id
  drg_route_table_id = oci_core_drg_route_table.primary_drg_vcn_route_table.id
  route_table_id     = oci_core_route_table.hub_vcn_primary_transit_drg_rt.id
  display_name       = var.primary_drg_vcn_attachment_name
}

# ------ Create Primary DRG VCN Route Table

resource "oci_core_drg_route_table" "primary_drg_vcn_route_table" {
  provider = oci.region-primary
  display_name = var.primary_drg_vcn_route_table_name
  drg_id = oci_core_drg.primary_drg.id
  import_drg_route_distribution_id = oci_core_drg_route_distribution.primary_drg_route_distribution.id
}

# ------ Create Primary DRG RPC Route Table

resource "oci_core_drg_route_table" "primary_drg_rpc_route_table" {
  provider = oci.region-primary
  display_name = var.primary_drg_rpc_route_table_name
  drg_id = oci_core_drg.primary_drg.id
}

# ------ Create Primary DRG RPC Route Table rule

resource "oci_core_drg_route_table_route_rule" "primary_drg_route_table_route_rule_primary_client_subnet" {
    provider = oci.region-primary
    drg_route_table_id = oci_core_drg_route_table.primary_drg_rpc_route_table.id
    destination = data.oci_core_vcn.vcn_primary.cidr_block
    destination_type = "CIDR_BLOCK"
    next_hop_drg_attachment_id = oci_core_drg_attachment.primary_drg_vcn_attachment.id
}

# ------ Create Primary DRG Route Distribution

resource "oci_core_drg_route_distribution" "primary_drg_route_distribution" {
  provider = oci.region-primary
  distribution_type = "IMPORT"
  display_name = var.primary_drg_route_distribution_name
  drg_id = oci_core_drg.primary_drg.id
}

# ------ Create Primary DRG Route Distribution Statement for RPC

resource "oci_core_drg_route_distribution_statement" "primary_drg_route_distribution_rpc" {
  provider = oci.region-primary
  drg_route_distribution_id = oci_core_drg_route_distribution.primary_drg_route_distribution.id
  action = "ACCEPT"
    match_criteria {
    match_type = "DRG_ATTACHMENT_TYPE"
    attachment_type = "REMOTE_PEERING_CONNECTION"
    }
    priority = "1"
}

# ------ Create Primary DRG RPC

resource "oci_core_remote_peering_connection" "primary_drg_remote_peering_connection" {
    provider = oci.region-primary
    compartment_id = var.compartment_ocid
    drg_id = oci_core_drg.primary_drg.id
    display_name = var.primary_drg_remote_peering_connection_name
    peer_id = oci_core_remote_peering_connection.standby_drg_remote_peering_connection.id
    peer_region_name = var.standby_region
}

# ------ Modify Primary DRG RT for RPC

resource "oci_core_drg_attachment_management" "primary_drg_rpc_attachment" {
  provider = oci.region-primary
  attachment_type = "REMOTE_PEERING_CONNECTION"
  compartment_id = var.compartment_ocid
  network_id = oci_core_remote_peering_connection.primary_drg_remote_peering_connection.id
  drg_id = oci_core_drg.primary_drg.id
  drg_route_table_id = oci_core_drg_route_table.primary_drg_rpc_route_table.id
}

##############################
# ------ Region Standby ---- #
##############################

# ------ Create Hub VCN Standby 
resource "oci_core_vcn" "hub_vcn_standby" {
  provider = oci.region-standby
  compartment_id = var.compartment_ocid
  display_name   = var.hub_vcn_standby_name
  cidr_block     = var.hub_vcn_standby_cidr_block
}

# ------ Create Hub VCN Standby Transit DRG Route Table
resource "oci_core_route_table" "hub_vcn_standby_transit_drg_rt" {
    provider = oci.region-standby
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_standby.id
    display_name       = var.hub_vcn_standby_transit_drg_rt_name
    route_rules {
        network_entity_id = oci_core_local_peering_gateway.hub_standby_local_peering_gateway.id
        destination = data.oci_core_vcn.vcn_standby.cidr_block
        destination_type = "CIDR_BLOCK"
    }
}

# ------ Create Hub VCN Standby Transit LPG Route Table
resource "oci_core_route_table" "hub_vcn_standby_transit_lpg_rt" {
    provider = oci.region-standby
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_standby.id
    display_name       = var.hub_vcn_standby_transit_drg_lpg_name
    route_rules {
        network_entity_id = oci_core_drg.standby_drg.id
        destination = data.oci_core_vcn.vcn_primary.cidr_block
        destination_type = "CIDR_BLOCK"
    }
}

# ------ Create Hub Standby LPG
resource "oci_core_local_peering_gateway" "hub_standby_local_peering_gateway" {
    provider = oci.region-standby
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.hub_vcn_standby.id
    display_name = var.hub_standby_local_peering_gateway_name
    peer_id = oci_core_local_peering_gateway.standby_local_peering_gateway.id
    route_table_id = oci_core_route_table.hub_vcn_standby_transit_lpg_rt.id
}

# ------ Create Standby LPG
resource "oci_core_local_peering_gateway" "standby_local_peering_gateway" {
    provider = oci.region-standby
    compartment_id = var.compartment_ocid
    vcn_id = var.vcn_standby_ocid
    display_name = var.standby_local_peering_gateway_name
}

# ------ Create Standby DRG
resource "oci_core_drg" "standby_drg" {
  provider = oci.region-standby
  compartment_id = var.compartment_ocid
  display_name   = var.oci_standby_drg_name
}

# ------ Create Standby DRG Hub VCN attachment
resource "oci_core_drg_attachment" "standby_drg_vcn_attachment" {
  provider = oci.region-standby
  vcn_id             = oci_core_vcn.hub_vcn_standby.id
  drg_id             = oci_core_drg.standby_drg.id
  drg_route_table_id = oci_core_drg_route_table.standby_drg_vcn_route_table.id
  route_table_id     = oci_core_route_table.hub_vcn_standby_transit_drg_rt.id
  display_name       = var.standby_drg_vcn_attachment_name
}


# ------ Create Standby DRG VCN Route Table

resource "oci_core_drg_route_table" "standby_drg_vcn_route_table" {
  provider = oci.region-standby
  display_name = var.standby_drg_vcn_route_table_name
  drg_id = oci_core_drg.standby_drg.id
  import_drg_route_distribution_id = oci_core_drg_route_distribution.standby_drg_route_distribution.id
}

# ------ Create Standby DRG RPC Route Table

resource "oci_core_drg_route_table" "standby_drg_rpc_route_table" {
  provider = oci.region-standby
  display_name = var.standby_drg_rpc_route_table_name
  drg_id = oci_core_drg.standby_drg.id
}

# ------ Create Standby DRG RPC Route Table rule

resource "oci_core_drg_route_table_route_rule" "standby_drg_route_table_route_rule_primary_client_subnet" {
    provider = oci.region-standby
    drg_route_table_id = oci_core_drg_route_table.standby_drg_rpc_route_table.id
    destination = data.oci_core_vcn.vcn_standby.cidr_block
    destination_type = "CIDR_BLOCK"
    next_hop_drg_attachment_id = oci_core_drg_attachment.standby_drg_vcn_attachment.id
}

# ------ Create Standby DRG Route Distribution

resource "oci_core_drg_route_distribution" "standby_drg_route_distribution" {
  provider = oci.region-standby
  distribution_type = "IMPORT"
  display_name = var.standby_drg_route_distribution_name
  drg_id = oci_core_drg.standby_drg.id
}

# ------ Create Standby DRG Route Distribution Statement for RPC

resource "oci_core_drg_route_distribution_statement" "standby_drg_route_distribution_rpc" {
  provider = oci.region-standby
  drg_route_distribution_id = oci_core_drg_route_distribution.standby_drg_route_distribution.id
  action = "ACCEPT"
    match_criteria {
    match_type = "DRG_ATTACHMENT_TYPE"
    attachment_type = "REMOTE_PEERING_CONNECTION"
    }
    priority = "1"
}

# ------ Create Standby DRG RPC

resource "oci_core_remote_peering_connection" "standby_drg_remote_peering_connection" {
    provider = oci.region-standby
    compartment_id = var.compartment_ocid
    drg_id = oci_core_drg.standby_drg.id
    display_name = var.standby_drg_remote_peering_connection_name
}

# ------ Modify Standby DRG RT for RPC

resource "oci_core_drg_attachment_management" "standby_drg_rpc_attachment" {
  provider = oci.region-standby
  attachment_type = "REMOTE_PEERING_CONNECTION"
  compartment_id = var.compartment_ocid
  network_id = oci_core_remote_peering_connection.standby_drg_remote_peering_connection.id
  drg_id = oci_core_drg.standby_drg.id
  drg_route_table_id = oci_core_drg_route_table.standby_drg_rpc_route_table.id
}