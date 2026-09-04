# =============================================================================
# OCI Provider / Tenancy
# =============================================================================

variable "tenancy_ocid" {
  description = "OCID of the OCI tenancy"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "region" {
  description = "OCI region for deployment (e.g. us-ashburn-1, eu-frankfurt-1)"
  type        = string
}

variable "home_region" {
  description = "Home region of the tenancy (used for IAM resources)"
  type        = string
  default     = ""
}

# =============================================================================
# General
# =============================================================================

variable "app_name" {
  description = "Application name used as a prefix for all resources"
  type        = string
  default     = "sentiment-intel"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "freeform_tags" {
  description = "Freeform tags applied to every resource"
  type        = map(string)
  default = {
    "Application" = "sentiment-intelligence"
    "ManagedBy"   = "terraform"
  }
}

# =============================================================================
# Networking
# =============================================================================

variable "vcn_cidr_block" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet (load balancers)"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for the private subnet (worker nodes)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "db_subnet_cidr" {
  description = "CIDR block for the database subnet"
  type        = string
  default     = "10.0.3.0/24"
}

# =============================================================================
# OKE (Oracle Kubernetes Engine)
# =============================================================================

variable "kubernetes_version" {
  description = "Kubernetes version for OKE cluster (must be a currently supported OKE version)"
  type        = string
  default     = "v1.34.2"
}

variable "node_pool_size" {
  description = "Number of worker nodes in the node pool"
  type        = number
  default     = 2
}

variable "node_shape" {
  description = "Shape for the OKE worker nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "node_ocpus" {
  description = "Number of OCPUs per worker node (flex shapes)"
  type        = number
  default     = 2
}

variable "node_memory_in_gbs" {
  description = "Memory in GBs per worker node (flex shapes)"
  type        = number
  default     = 32
}

variable "node_pool_image_type" {
  description = "Image type for OKE node pool"
  type        = string
  default     = "OKE"
}

# =============================================================================
# Oracle Autonomous Database
# =============================================================================

variable "adb_display_name" {
  description = "Display name for the Autonomous Database"
  type        = string
  default     = "SentimentDB"
}

variable "adb_db_name" {
  description = "Database name (alphanumeric, max 14 chars)"
  type        = string
  default     = "SENTIMENTDB"
}

variable "adb_admin_password" {
  description = "Admin password for Autonomous Database (min 12 chars, must include uppercase, lowercase, number)"
  type        = string
  sensitive   = true
}

variable "adb_cpu_core_count" {
  description = "Number of ECPU cores for the Autonomous Database"
  type        = number
  default     = 2
}

variable "adb_data_storage_size_in_gb" {
  description = "Data storage size in GB for the Autonomous Database"
  type        = number
  default     = 20
}

variable "adb_db_workload" {
  description = "Autonomous Database workload type (OLTP, DW, AJD, APEX)"
  type        = string
  default     = "OLTP"
  validation {
    condition     = contains(["OLTP", "DW", "AJD", "APEX"], var.adb_db_workload)
    error_message = "Workload type must be one of: OLTP, DW, AJD, APEX."
  }
}

variable "adb_is_free_tier" {
  description = "Whether to use Always Free Autonomous Database"
  type        = bool
  default     = false
}

variable "adb_license_model" {
  description = "License model for Autonomous Database (LICENSE_INCLUDED or BRING_YOUR_OWN_LICENSE)"
  type        = string
  default     = "LICENSE_INCLUDED"
}

# =============================================================================
# Oracle Select AI
# =============================================================================

variable "select_ai_profile" {
  description = "Name of the Select AI profile the backend uses for NL2SQL and inference (must be created in the database as a post-deploy step)"
  type        = string
  default     = "SENTIMENT_PROFILE"
}

# =============================================================================
# OCI Generative AI
# =============================================================================

variable "genai_region" {
  description = "OCI region where the Generative AI service is available (e.g. eu-frankfurt-1, us-chicago-1)"
  type        = string
  default     = "eu-frankfurt-1"
}

variable "genai_model_id" {
  description = "OCID or model name of the OCI Generative AI model to use"
  type        = string
  default     = "openai.gpt-oss-120b"
}

variable "genai_endpoint" {
  description = "OCI Generative AI inference endpoint URL (leave empty to auto-construct from genai_region)"
  type        = string
  default     = ""
}

# =============================================================================
# Container Registry (OCIR)
# =============================================================================

variable "ocir_repo_name" {
  description = "Name of the OCIR repository"
  type        = string
  default     = "sentiment-intel"
}

# =============================================================================
# Application Configuration
# =============================================================================

variable "backend_image_tag" {
  description = "Docker image tag for the backend service"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for the frontend service"
  type        = string
  default     = "latest"
}
