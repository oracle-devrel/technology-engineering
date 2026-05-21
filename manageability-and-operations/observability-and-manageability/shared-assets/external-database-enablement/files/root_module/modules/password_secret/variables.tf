# Copyright (c) 2026 Oracle and/or its affiliates.
variable "password_secret_id" {
  description = "Optional OCI Vault Secret OCID for password instead of plain text"
  type        = string
  default     = null
}