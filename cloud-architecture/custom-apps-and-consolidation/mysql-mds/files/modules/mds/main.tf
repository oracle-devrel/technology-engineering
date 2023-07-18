# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration to declare oci mysql service provisioning.
# @author: Vijay Kokatnur

#MySQL Database System Service
resource "oci_mysql_mysql_db_system" "test_mysql_db_system" {
    #Required
    availability_domain = var.mysql_db_system_availability_domain
    compartment_id = var.compartment_id
    shape_name = var.mysql_shape_name
    subnet_id = var.mysql_db_system_subnet_id

    description = var.mysql_db_system_description
    display_name = var.mysql_db_system_display_name
    #fault_domain = var.mysql_db_system_fault_domain
    fault_domain = data.oci_identity_fault_domains.test_fault_domains.fault_domains[0].name
    
    #Optional
    admin_password = var.mysql_db_system_admin_password
    admin_username = var.mysql_db_system_admin_username
    backup_policy {
        is_enabled = var.mysql_db_system_backup_policy_is_enabled
        retention_in_days = var.mysql_db_system_backup_policy_retention_in_days
    }
    data_storage_size_in_gb = var.mysql_db_system_data_storage_size_in_gb
    
    freeform_tags = var.freeform_tags

    hostname_label = var.mysql_db_system_hostname_label
    is_highly_available = var.mysql_db_system_is_highly_available
   
}