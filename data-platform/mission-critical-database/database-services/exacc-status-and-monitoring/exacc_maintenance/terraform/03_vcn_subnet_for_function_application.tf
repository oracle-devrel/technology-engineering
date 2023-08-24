# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# ----------------------------------------------------------------------------------------------------

# ------ Create a new VCN
resource oci_core_vcn exacc_maintenance {
    compartment_id = var.network_compartment_ocid
    display_name   = "ExaCC-maintenance-reports"
    dns_label      = "exacc"
    cidr_blocks    = [ "10.0.0.0/16" ]
}

# ------ Create a new Internet Gategay
resource oci_core_internet_gateway exacc_maintenance {
    compartment_id = var.network_compartment_ocid
    display_name   = "reports-ig"
    vcn_id         = oci_core_vcn.exacc_maintenance.id
}

# ------ Create a new Route Table
resource oci_core_route_table exacc_maintenance {
    compartment_id = var.network_compartment_ocid
    vcn_id         = oci_core_vcn.exacc_maintenance.id
    display_name   = "reports-rt"

    route_rules {
        destination       = "0.0.0.0/0"
        network_entity_id = oci_core_internet_gateway.exacc_maintenance.id
        description       = "single route rule to Internet gateway for all traffic"
    }
}

# ------ Create a new security list to be used in the new subnet
resource oci_core_security_list exacc_maintenance {
    compartment_id = var.network_compartment_ocid
    vcn_id         = oci_core_vcn.exacc_maintenance.id
    display_name   = "reports-sl"

    egress_security_rules {
        protocol    = "all"
        destination = "0.0.0.0/0"
        description = "Allow all outgoing traffic"
    }
}

# ------ Create a regional public subnet
resource oci_core_subnet exacc_maintenance {
    compartment_id      = var.network_compartment_ocid
    vcn_id              = oci_core_vcn.exacc_maintenance.id
    cidr_block          = "10.0.0.0/24"
    display_name        = "reports-subnet"
    dns_label           = "subnet"
    route_table_id      = oci_core_route_table.exacc_maintenance.id
    security_list_ids   = [oci_core_security_list.exacc_maintenance.id]
    dhcp_options_id     = oci_core_vcn.exacc_maintenance.default_dhcp_options_id
}