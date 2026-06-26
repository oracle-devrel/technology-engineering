variable "compartment_id" {
  description = "Compartment OCID that holds the databases, private endpoints, and Vault secret."
  type        = string
}

variable "dbm_private_endpoint_id" {
  description = "Database Management private endpoint OCID."
  type        = string
}

variable "opsi_private_endpoint_id" {
  description = "Operations Insights private endpoint OCID. Required when enable_ops_insights is true."
  type        = string
  default     = null
}

variable "password_secret_id" {
  description = "Vault secret OCID holding the monitoring user's password."
  type        = string
}

variable "monitoring_user" {
  description = "Database monitoring user."
  type        = string
  default     = "DBSNMP"
}

# --- Feature toggles: flip a feature on/off without touching the others. ---
variable "enable_database_management" {
  type    = bool
  default = true
}

variable "enable_ops_insights" {
  type    = bool
  default = true
}

variable "set_preferred_credentials" {
  description = "Create a Vault named credential and wire PC_READ/PC_WRITE for advanced diagnostics."
  type        = bool
  default     = true
}

variable "enable_data_safe" {
  description = "Register each target as a Data Safe target database (security pillar)."
  type        = bool
  default     = false
}

variable "data_safe_private_endpoint_id" {
  description = "Data Safe private endpoint OCID in the DB subnet. Required when enable_data_safe is true."
  type        = string
  default     = null
}

variable "data_safe_password" {
  description = <<-EOT
    Plaintext password for the Data Safe service account (monitoring_user). The
    oci_data_safe_target_database resource takes a password, not a Vault secret,
    so it lands in Terraform state — supply via TF_VAR_data_safe_password and keep
    state encrypted/restricted; never commit it. Required when enable_data_safe is true.
  EOT
  type        = string
  default     = null
  sensitive   = true
}

variable "targets" {
  description = <<-EOT
    Enablement targets keyed by a short name (e.g. "cdb", "pdb1"). For OCI-native
    DBCS the managed-database OCID equals the database / pluggable-database OCID,
    so database_id is reused as the managed-database id. service_name must be the
    REAL listener service (db_unique_name.domain for the CDB, pdb_name.domain for
    a PDB) — the bare DB/PDB name causes ORA-12514.
  EOT
  type = map(object({
    database_id            = string
    database_role          = string # CDB | PDB | NON_CDB
    database_resource_type = string # OPSI value, lowercase: "database" | "pluggabledatabase"
    service_name           = string
    host_ip                = string
    management_type        = optional(string, "ADVANCED")
    # Parent DB system OCID — required only for Data Safe DATABASE_CLOUD_SERVICE
    # registration (Base DB / Exadata cloud service).
    db_system_id           = optional(string)
  }))
}
