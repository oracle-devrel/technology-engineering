# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform variable declaration file.
# @author: Vijay Kokatnur

variable "tenancy_id" {
  description = "The tenancy id of the OCI Cloud Account in which to create the resources."
  type        = string
}

# General OCI parameters
variable mysql_db_system_availability_domain {
    type = string
    default = "true"
}

variable compartment_id {
    type = string
    default = "true"
}

variable mysql_shape_name {
    type = string
    default = "true"
}

variable mysql_db_subnet {
    type = string
    default = "true"
}

variable mysql_db_system_admin_username {
    type = string
    default = "true"
}

variable mysql_db_system_admin_password {
    type = string
    default = "true"
}

variable mysql_db_system_backup_policy_is_enabled {
    type = string
    default = "true"
}

variable mysql_db_system_backup_policy_pitr_policy_is_enabled {
    type = string
    default = "true"
}

variable mysql_db_system_backup_policy_retention_in_days {
    type = string
    default = "true"
}

variable mysql_db_system_backup_policy_window_start_time {
    type = string
    default = "true"
}

variable mysql_db_system_crash_recovery {
    type = string
    default = "true"
}

variable mysql_db_system_data_storage_size_in_gb {
    type = string
    default = "true"
}

variable mysql_db_system_deletion_policy_automatic_backup_retention {
    type = string
    default = "true"
}

variable mysql_db_system_deletion_policy_final_backup {
    type = string
    default = "true"
}

variable mysql_db_system_deletion_policy_is_delete_protected {
    type = string
    default = "true"
}

variable mysql_db_system_description {
    type = string
    default = "true"
}

variable mysql_db_system_display_name {
    type = string
    default = "true"
}

variable mysql_db_system_fault_domain {
    type = string
    default = "true"
}

variable mysql_db_system_hostname_label {
    type = string
    default = "true"
}

variable mysql_db_system_is_highly_available {
    type = bool
    default = false
}

variable mysql_db_system_subnet_id {
    type = string
    default = ""
}

variable "freeform_tags" {
  description = "Freeform tags for compute instance"
  default = {
    access      = "private"
    environment = "dev"
    role        = "mysqldb"
  }
  type = map(any)
}