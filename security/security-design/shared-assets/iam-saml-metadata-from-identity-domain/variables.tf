variable "tenancy_ocid" {
  description = "The OCID of your OCI tenancy."
  type        = string
}

variable "region" {
  description = "The OCI region where resources will be created."
  type        = string
}

variable "compartment_id" {
  description = "The OCID of the compartment where the identity domain will be created."
  type        = string
}

variable "domain_display_name" {
  description = "The display name for the identity domain."
  type        = string
}

variable "domain_description" {
  description = "A description for the identity domain."
  type        = string
}

variable "is_hidden_on_login" {
  description = "Whether the identity domain should be hidden on the login page."
  type        = bool
  default     = false
}

variable "license_type" {
  description = "The license type for the identity domain (e.g., 'premium', 'free')."
  type        = string
}

variable "oci_profile" {
  description = "The OCI profile to use from the config file."
  type        = string
  default     = "DEFAULT"
}
