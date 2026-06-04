# --- Required Variables ---

variable "tenancy_ocid" {
  description = "Tenancy OCID"
}

variable "region" {
  description = "OCI Region"
  default     = "eu-frankfurt-1"
}

variable "compartment_ocid" {
  description = "Compartment OCID"
}

variable "prefix" {
  description = "Prefix for all resource names"
  default     = "docreport"
  nullable    = false
}

# --- Compute ---

variable "instance_shape" {
  description = "Compute instance shape"
  default     = "VM.Standard.x86.Generic"
  nullable    = false
}

variable "instance_ocpus" {
  description = "Number of OCPUs"
  default     = 1
  nullable    = false
}

variable "instance_memory_in_gbs" {
  description = "Memory in GBs"
  default     = 8
  nullable    = false
}

# --- SSH ---

variable "ssh_public_key" {
  description = "Public SSH key (auto-generated if null)"
  default     = null
}

variable "ssh_private_key" {
  description = "Private SSH key (auto-generated if null)"
  default     = null
  sensitive   = true
}

resource "tls_private_key" "ssh_key" {
  count     = var.ssh_public_key == null ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

locals {
  ssh_public_key  = var.ssh_public_key != null ? var.ssh_public_key : tls_private_key.ssh_key[0].public_key_openssh
  ssh_private_key = var.ssh_public_key != null ? var.ssh_private_key : tls_private_key.ssh_key[0].private_key_pem
}

# --- GenAI ---

variable "genai_model" {
  description = "OCI GenAI model ID for LLM inference"
  default     = "meta.llama-3.3-70b-instruct"
}

locals {
  freeform_tags = {
    app_prefix = var.prefix
    project    = "agent-day-doc-report"
  }
}
