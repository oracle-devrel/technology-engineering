# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform variable declaration file.
# @author: Vijay Kokatnur

# provider parameters
variable "api_fingerprint" {
  default     = ""
  description = "Fingerprint of the API private key to use with OCI API."
  type        = string
}

variable "api_private_key" {
  default     = ""
  description = "The contents of the private key file to use with OCI API. This takes precedence over private_key_path if both are specified in the provider."
  sensitive   = "true"
  type        = string
}

variable "api_private_key_password" {
  default     = ""
  description = "The corresponding private key password to use with the api private key if it is encrypted."
  sensitive   = "true"
  type        = string
}

variable "api_private_key_path" {
  default     = ""
  description = "The path to the OCI API private key."
  type        = string
}

variable "home_region" {
  # List of regions: https://docs.cloud.oracle.com/iaas/Content/General/Concepts/regions.htm#ServiceAvailabilityAcrossRegions
  description = "The tenancy's home region. Required to perform identity operations."
  type        = string
}

variable "region" {
  # List of regions: https://docs.cloud.oracle.com/iaas/Content/General/Concepts/regions.htm#ServiceAvailabilityAcrossRegions
  description = "The OCI region where OKE resources will be created."
  type        = string
}

variable "tenancy_id" {
  description = "The tenancy id of the OCI Cloud Account in which to create the resources."
  type        = string
}

variable "user_id" {
  description = "The id of the user that terraform will use to create the resources."
  type        = string
  default     = ""
}

variable "config_file_profile" {
  default     = "DEFAULT"
  description = "Fingerprint of the API private key to use with OCI API."
  type        = string
}

# general oci parameters
variable "compartment_id" {
  description = "compartment id where to create all resources"
  type        = string
}

variable "label_prefix" {
  description = "a string that will be prepended to all resources"
  type        = string
  default     = "none"
}

# network parameters

variable "instance_count" {
  description = "number of OCI Compute instances to create."
  default     = 1
  type        = number
}

variable "availability_domain" {
  description = "the AD to place the  host"
  default     = 1
  type        = number
}

variable "access" {
  description = "A list of CIDR blocks to which ssh access to the  must be restricted to. *anywhere* is equivalent to 0.0.0.0/0 and allows ssh access from anywhere."
  default     = ["anywhere"]
  type        = list
}

variable "vcn_cidr" {
  description = "the route id to the internet gateway"
  type        = string
  default     = ""
}

variable "ig_route_id" {
  description = "the route id to the internet gateway"
  type        = string
  default     = ""
}

variable "create_subnet" {
  description = "The id of the Subnet to use when creating the  resources."
  type        = string
}

variable "subnet_cidr" {
  description = "the route id to the internet gateway"
  type        = string
  default     = ""
}

variable "netnum" {
  description = "0-based index of the  subnet when the VCN's CIDR is masked with the corresponding newbit value."
  default     = 0
  type        = number
}

variable "newbits" {
  description = "The difference between the VCN's netmask and the desired  subnet mask"
  default     = 14
  type        = number
}

variable "subnet_id" {
  description = "The id of the VCN to use when creating the  resources."
  type        = string
  default     = ""
}

variable "vcn_id" {
  description = "The id of the VCN to use when creating the  resources."
  type        = string
  default     = ""
}

#  host parameters
variable "image_id" {
  description = "Provide a custom image id for the  host or leave as Autonomous."
  default     = "Autonomous"
  type        = string
}

variable "os_version" {
  description = "In case Autonomous Linux is used, allow specification of Autonomous version"
  default     = "7.9"
  type        = string
}

variable "shape" {
  description = "The shape of  instance."
  default = {
    shape = "VM.Standard.E4.Flex", ocpus = 1, memory = 4, boot_volume_size = 50
  }
  type = map(any)
}

variable "state" {
  description = "The target state for the instance. Could be set to RUNNING or STOPPED. (Updatable)"
  default     = "RUNNING"
  type        = string
}

variable "timezone" {
  description = "The preferred timezone for the  host."
  default     = "Australia/Sydney"
  type        = string
}

variable "type" {
  description = "Whether to make the  host public or private."
  default     = "public"
  type        = string
}

variable "ssh_public_key" {
  description = "the content of the ssh public key used to access the . set this or the ssh_public_key_path"
  default     = ""
  type        = string
}

variable "ssh_public_key_path" {
  description = "path to the ssh public key used to access the . set this or the ssh_public_key"
  default     = ""
  type        = string
}

variable "ssh_private_key_path" {
  description = "path to the ssh public key used to access the . set this or the ssh_public_key"
  default     = ""
  type        = string
}

variable "upgrade" {
  description = "Whether to upgrade the  host packages after provisioning. It's useful to set this to false during development/testing so the  is provisioned faster."
  default     = false
  type        = bool
}

# tagging
variable "freeform_tags" {
  description = "Freeform tags for compute instance"
  default = {
    access      = "private"
    environment = "dev"
    role        = "mongodb"
  }
  type = map(any)
}

variable "cloud_agent_plugins" {
  description = "Whether each Oracle Cloud Agent plugins should be ENABLED or DISABLED."
  type        = map(string)
  default = {
    autonomous_linux       = "ENABLED"
    bastion                = "ENABLED"
    block_volume_mgmt      = "DISABLED"
    custom_logs            = "ENABLED"
    management             = "DISABLED"
    monitoring             = "ENABLED"
    osms                   = "ENABLED"
    run_command            = "ENABLED"
    vulnerability_scanning = "ENABLED"
  }
  #* need to craft a validation condition at some point
}

variable "extended_metadata" {
  description = "(Updatable) Additional metadata key/value pairs that you provide."
  type        = map(any)
  default     = {}
}

# MySql DB System parameters
variable mysql_db_system_availability_domain {
    type = string
    default = "kWcK:EU-FRANKFURT-1-AD-1"
}

variable mysql_shape_name {
    type = string
    default = "VM.Standard2.4"
}

variable mysql_db_subnet {
    type = string
    default = ""
}

variable mysql_db_system_admin_username {
    type = string
    default = "admin"
}

variable mysql_db_system_admin_password {
    type = string
    default = "32Welcome@54"
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
    default = "30"
}

variable mysql_db_system_backup_policy_window_start_time {
    type = string
    default = ""
}

variable mysql_db_system_crash_recovery {
    type = string
    default = ""
}

variable mysql_db_system_data_storage_size_in_gb {
    type = string
    default = "true"
}

variable mysql_db_system_deletion_policy_automatic_backup_retention {
    type = string
    default = ""
}

variable mysql_db_system_deletion_policy_final_backup {
    type = string
    default = ""
}

variable mysql_db_system_deletion_policy_is_delete_protected {
    type = string
    default = ""
}

variable mysql_db_system_description {
    type = string
    default = "true"
}

variable mysql_db_system_display_name {
    type = string
    default = "OCI MySQL Database service"
}

variable mysql_db_system_fault_domain {
    type = string
    default = "FD-1"
}

variable mysql_db_system_hostname_label {
    type = string
    default = ""
}

variable mysql_db_system_is_highly_available {
    type = bool
    default = false
}

variable mysql_db_bastion_enable {
    type = bool
    default = false
}

variable "enable_ext" {
  description = "Whether to upgrade the host packages after provisioning. It's useful to set this to false during development/testing so the  is provisioned faster."
  default     = false
  type        = bool
}

variable "assign_public_ip" {
  description = "assign_public_ip "
  default     = false
  type        = bool
}
