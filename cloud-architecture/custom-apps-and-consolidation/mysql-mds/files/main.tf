# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to declare required resource provisioning.
# @author: Vijay Kokatnur

module "network" {
    source = "./modules/network"

    compartment_id  = var.compartment_id
    label_prefix    = var.label_prefix
    vcn_id          = var.vcn_id
    ig_route_id     = var.ig_route_id
    vcn_cidr        = var.vcn_cidr
    newbits         = var.newbits
    netnum          = var.netnum   

    providers = {
        oci.home = oci.home
    }

    count = var.create_subnet == "true" ? 1 : 0
}

# module to provision OCI MySQL DB system.
module "mds" {
    source = "./modules/mds"

    tenancy_id      = var.tenancy_id
    compartment_id  = var.compartment_id
    mysql_db_system_availability_domain = element(local.ADs, 0) 
    mysql_shape_name          = var.mysql_shape_name
    mysql_db_system_subnet_id = var.create_subnet == true ? module.network.snevndtmdb_id : var.subnet_id

    mysql_db_system_description     = var.mysql_db_system_description
    mysql_db_system_display_name    = var.mysql_db_system_display_name
    mysql_db_system_fault_domain    = var.mysql_db_system_fault_domain

    mysql_db_system_admin_password  = var.mysql_db_system_admin_password
    mysql_db_system_admin_username  = var.mysql_db_system_admin_username

    mysql_db_system_backup_policy_is_enabled        = var.mysql_db_system_backup_policy_is_enabled
    mysql_db_system_backup_policy_retention_in_days = var.mysql_db_system_backup_policy_retention_in_days
    mysql_db_system_data_storage_size_in_gb         = var.mysql_db_system_data_storage_size_in_gb
    
    mysql_db_system_hostname_label      = var.mysql_db_system_hostname_label
    mysql_db_system_is_highly_available = var.mysql_db_system_is_highly_available

    providers = {
        oci.home = oci.home
    }

    depends_on = [
        module.network
    ]
}
