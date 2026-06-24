variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID."
}

variable "compartment_ocid" {
  type        = string
  description = "OCI compartment OCID for PoC resources."
}

variable "region" {
  type        = string
  description = "OCI region."
}

variable "create_test_network" {
  type        = bool
  description = "Create a PoC VCN/subnet."
  default     = false
}

variable "vcn_ocid" {
  type        = string
  description = "Existing VCN OCID."
  default     = null
}

variable "subnet_ocid" {
  type        = string
  description = "Existing subnet OCID."
  default     = null
}

variable "test_vcn_cidr" {
  type        = string
  description = "PoC VCN CIDR."
  default     = "10.44.0.0/16"
}

variable "test_subnet_cidr" {
  type        = string
  description = "PoC private subnet CIDR."
  default     = "10.44.10.0/24"
}

variable "create_vault" {
  type        = bool
  description = "Create a PoC vault/key."
  default     = false
}

variable "vault_ocid" {
  type        = string
  description = "Existing vault OCID."
  default     = null
}

variable "key_ocid" {
  type        = string
  description = "Existing key OCID."
  default     = null
}

variable "policy_name" {
  type        = string
  description = "IAM policy name."
}

variable "policy_description" {
  type        = string
  description = "IAM policy description."
}

variable "policy_statements" {
  type        = list(string)
  description = "IAM policy statements."
}

variable "create_identity_policy" {
  type        = bool
  description = "Create the IAM policy for DBM/OPSI enablement. Set false when an existing operator/group policy is managed outside this stack."
  default     = true
}

variable "targets" {
  type = list(object({
    kind            = string
    name            = string
    resource_id     = optional(string)
    provision       = bool
    management_type = string
  }))
  description = "Database targets selected by the wizard."
  default     = []
}

variable "ssh_public_keys" {
  type        = list(string)
  description = "SSH public keys for provisioned DBCS VM DB systems."
  default     = []
}

variable "db_admin_password" {
  type        = string
  description = "Admin password for provisioned DBCS databases. Pass through TF_VAR_db_admin_password."
  sensitive   = true
  default     = null
}

variable "adb_admin_password" {
  type        = string
  description = "Admin password for provisioned Autonomous Databases. Pass through TF_VAR_adb_admin_password."
  sensitive   = true
  default     = null
}

variable "dbcs_shape" {
  type        = string
  description = "DBCS shape for zero-start PoC provisioning."
  default     = "VM.Standard.E4.Flex"
}

variable "db_version" {
  type        = string
  description = "Oracle Database version for provisioned DBCS systems."
  default     = "19.0.0.0"
}

variable "adb_compute_count" {
  type        = number
  description = "ECPU/core count for provisioned Autonomous Databases."
  default     = 2
}

variable "adb_storage_tbs" {
  type        = number
  description = "Storage in TB for provisioned Autonomous Databases."
  default     = 1
}

# --- Optional: enable DBM + OPSI on databases provisioned/known to this stack ---
variable "enable_observability" {
  type        = bool
  description = "Call the dbm-opsi-enablement module to enable DBM/OPSI on observability_targets."
  default     = false
}

variable "dbsnmp_secret_id" {
  type        = string
  description = "Vault secret OCID holding the DBSNMP password (required when enable_observability=true)."
  default     = null
}

variable "opsi_private_endpoint_id" {
  type        = string
  description = "OPSI private endpoint OCID. When null, only DBM (not Ops Insights) is enabled."
  default     = null
}

variable "observability_targets" {
  description = <<-EOT
    Targets for DBM/OPSI enablement, keyed by short name. service_name and host_ip
    are runtime-discovered (lsnrctl / DB node IP), so they are supplied here after
    the database is up rather than derived from Terraform attributes.
  EOT
  type = map(object({
    database_id            = string
    database_role          = string
    database_resource_type = string # "database" | "pluggabledatabase"
    service_name           = string
    host_ip                = string
    management_type        = optional(string, "ADVANCED")
  }))
  default = {}
}

variable "dbcs_cpu_core_count" {
  description = "OCPU core count for a provisioned Flex-shape DB system."
  type        = number
  default     = 1
}

variable "dbcs_data_storage_gb" {
  description = "Data storage (GB) for a provisioned VM DB system. Minimum 256."
  type        = number
  default     = 256
}

variable "config_file_profile" {
  description = "OCI CLI config profile (~/.oci/config) the provider authenticates with."
  type        = string
  default     = "DEFAULT"
}

variable "availability_domain_index" {
  description = "Index into the region's availability domains for provisioned DB systems (0-based). Pin to an AD with DB block-storage headroom."
  type        = number
  default     = 0
}

variable "dbcs_domain" {
  description = "Network domain for a provisioned DB system. Required when the subnet has no DNS label. null derives it from a DNS-enabled subnet."
  type        = string
  default     = null
}
