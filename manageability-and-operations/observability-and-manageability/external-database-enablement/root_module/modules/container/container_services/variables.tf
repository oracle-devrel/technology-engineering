variable "compartment_ocid" {
  type = string
}

variable "external_database_connector_agent_id" {
  type = string
}

variable "external_container_id" {
  type = string
}

variable "external_container_display_name" {
  type = string
}

variable "external_container_connector_id" {
  type = string
}

variable "enable_database_management_cdb" {
  description = "Set enablement of Database Management for container database"
  type        = string
  validation {
    condition     = contains(["enable", "disable"], var.enable_database_management_cdb)
    error_message = "The value of 'containerDBManagement' in the JSON-input for database systems must be 'enable' or 'disable'"
  }
}

variable "external_container_database_management_license" {
  description = "Database Management license. Can be 'BRING_YOUR_OWN_LICENSE' or 'LICENSE_INCLUDED'"
  type        = string
  validation {
    condition     = contains(["BRING_YOUR_OWN_LICENSE", "LICENSE_INCLUDED"], var.external_container_database_management_license)
    error_message = "The value of 'dbManagementLicense' in the JSON-input for database systems must be 'BRING_YOUR_OWN_LICENSE' or 'LICENSE_INCLUDED'"
  }
}

variable "enable_stack_monitoring_cdb" {
  description = "Set enablement of Stack Monitoring for container database"
  type        = string
  validation {
    condition     = contains(["enable", "disable"], var.enable_stack_monitoring_cdb)
    error_message = "The value of 'containerStackMonitoring' in the JSON-input for database systems must be 'enable' or 'disable'"
  }
}

variable "enable_stack_monitoring_asm" {
  description = "Set enablement of ASM discovery in Stack Monitoring"
  type        = string
  validation {
    condition     = contains(["enable", "disable"], var.enable_stack_monitoring_asm)
    error_message = "The value of 'asmStackMonitoring' in the JSON-input for database systems must be 'enable' or 'disable'"
  }
}

variable "asm_hostname" {
  description = "Hostname for ASM discovery in Stack Monitoring"
  type        = string
}

variable "asm_port" {
  description = "Port for ASM discovery in Stack Monitoring"
  type        = string
}

variable "asm_service" {
  description = "Service name for ASM discovery in Stack Monitoring"
  type        = string
}

variable "asm_credentials_role" {
  description = "User role for ASM discovery in Stack Monitoring. Can be 'SYSASM', 'SYSDBA', or 'SYSOPER'"
  type        = string
  validation {
    condition     = contains(["SYSASM", "SYSDBA", "SYSOPER", ""], var.asm_credentials_role)
    error_message = "The value of 'userRole' in the JSON-input for credentials used for ASM discovery in Stack Monitoring must be 'SYSASM', 'SYSDBA', or 'SYSOPER'"
  }
}

variable "asm_credentials_username" {
  description = "Username for ASM discovery in Stack Monitoring"
  type        = string
}

variable "asm_credentials_password_secret_id" {
  description = "The OCID for the OCI Vault Secret conaining the password for ASM discovery in Stack Monitoring"
  type        = string
}