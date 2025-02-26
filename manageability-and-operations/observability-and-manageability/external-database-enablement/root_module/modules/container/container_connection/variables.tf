#Common database system variables

variable "compartment_ocid" {
  type = string
}

variable "external_database_connector_connection_string_hostname" {
  description = "Hostname for connection string"
  type        = string
  validation {
  	condition = var.external_database_connector_connection_string_hostname != ""
	error_message = "The value of 'host' in the JSON-input for database systems is an empty string"
  }
}

variable "external_database_connector_connection_string_port" {
  description = "Port for connection string"
  type        = number
  default     = 1521
}

variable "external_database_connector_connection_string_protocol" {
  description = "Protocol for connection string. Can be 'TCP' or 'TCPS'"
  type        = string
  validation {
    condition     = contains(["TCP", "TCPS"], var.external_database_connector_connection_string_protocol)
    error_message = "The value of 'protocol' in the JSON-input for database systems must be 'TCP' or 'TCPS'"
  }
}

variable "ssl_secret_id" {
  description = "The OCID for the OCI Vault Secret used for TCPS-connections. PKCS12 and JKS are supported as trust store types"
  type        = string
  default     = null
}

variable "external_database_connector_agent_id" {
  description = "The OCID for the management agent used for database connections"
  type        = string
  validation {
  	condition = var.external_database_connector_agent_id != ""
	error_message = "The value of 'managementAgentId' in the JSON-input for database systems is an empty string"
  }
}

#Container database variables

variable "external_container_database_display_name" {
  description = "Name for external container database"
  type        = string
}

variable "external_cdb_connector_connection_credentials_credential_name" {
  description = "Name of credential set for container database connector. Must be in a 'x.y' format"
  type        = string
  validation {
    condition     = can(regex("[a-zA-Z\\d_]{1,64}\\.[a-zA-Z\\d_]{1,199}", var.external_cdb_connector_connection_credentials_credential_name))
    error_message = "The value of var.external_cdb_connector_connection_credentials_credential_name must be in 'x.y' format. x has a maximum of 64 characters, and y has a maximum of 199 characters. The strings can only contain letters, numbers, and underscores"
  }
}

variable "external_cdb_connector_connection_credentials_credential_type" {
  description = "Set to 'DETAILS' for TCP credentials and 'SSL_DETAILS' for TCPS credentials"
  type        = string
  validation {
    condition     = contains(["DETAILS", "SSL_DETAILS"], var.external_cdb_connector_connection_credentials_credential_type)
    error_message = "The value of var.external_cdb_connector_connection_credentials_credential_type must be 'DETAILS' or 'SSL_DETAILS'"
  }
}

variable "external_cdb_connector_connection_credentials_password" {
  description = "Password for container database connector"
  type        = string
  validation {
	condition = var.external_cdb_connector_connection_credentials_password != ""
	error_message = "Container database connector password is an empty string. Confirm values in the JSON-input for credentials"
  }
}

variable "external_cdb_connector_connection_credentials_role" {
  description = "User role for container database connector. Can be NORMAL or SYSDBA"
  type        = string
  validation {
    condition     = contains(["NORMAL", "SYSDBA"], var.external_cdb_connector_connection_credentials_role)
    error_message = "The value of 'userRole' in the JSON-input for credentials used for external database connectors must be 'NORMAL' or 'SYSDBA'"
  }
}

variable "external_cdb_connector_connection_credentials_username" {
  description = "Username for container database connector"
  type        = string
  validation {
	condition = var.external_cdb_connector_connection_credentials_username != ""
	error_message = "Container database connector username is an empty string. Confirm values in the JSON-input for credentials"
  }
}

variable "external_cdb_connector_connection_string_service" {
  description = "Service name for container database connector"
  type        = string
  validation {
    condition = var.external_cdb_connector_connection_string_service != ""
	error_message = "The value of 'containerServiceName' in the JSON-input for database systems is an empty string"
  }
}