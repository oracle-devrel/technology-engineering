### Start : These information are needed only outside of OCI Terraform Stack Manager
variable "tenancy_ocid" {
    description = "The OCI Tenancy ocid"
    type        = string
    default     = ""
}

variable "user_ocid" {
    description = "The OCI User ocid"
    type        = string
    default     = ""
}

variable "fingerprint" {
    description = "The Fingerprint of the OCI API Key"
    type        = string
    default     = ""
}

variable "private_api_key" {
    description = "The content of the OCI API private key passed to the container runtime"
    type        = string
    default     = ""
    sensitive   = true
}
### End : These information are needed only outside of OCI Terraform Stack Manager

variable "region" {
    description = "The OCI region"
    type        = string
}

variable "compartment_ocid" {
    description = "The OCI Compartment ocid"
    type        = string
}

variable "private_subnet_ocid" {
    description = "The OCI Private Subnet ocid"
    type        = string
}

variable "public_subnet_ocid" {
    description = "The OCI Public Subnet ocid"
    type        = string
}

# Use data to get ADs is better.
# variable "availability_domain" {
#     description = "The OCI Availability Domain"
#     type        = string
# }

variable "ci_name" {
    description = "The OCI Container Instance Name"
    type        = string
    default     = "CI_TRANSLATOR"
}

variable "ci_restart_policy" {
    description = "The OCI Container Instance Retsrat Policy"
    type        = string
    default     = "ALWAYS"
}

variable "ci_state" {
    description = "The OCI Container Instance State"
    type        = string
    default     = "ACTIVE"
}

variable "ci_shape" {
    description = "The OCI Container Instance Shape"
    type        = string
    default     = "CI.Standard.E5.Flex"
}

variable "ci_ocpus" {
    description = "The OCI Container Instance Ocpu Number"
    type        = number
    default     = 1
}

variable "ci_memory" {
    description = "The OCI Container Instance Memory GB Number"
    type        = number
    default     = 2
}

variable "ci_container_name" {
    description = "The OCI Container Name"
    type        = string
    default     = "CI_CONTAINER_NAME"
}

variable "ci_image_url" {
    description = "The OCI Container Image Url"
    type        = string
}

variable "ci_registry_secret" {
    description = "The OCI Vault Secret Id with username and password of OCI registry"
    type        = string
}

variable "ci_count" {
    description = "The OCI Container Instance Count Number"
    type        = number
}

variable "ci_compartment_id_env" {
  type        = string
  description = "OCI_COMPARTMENT_ID passed to the container for GenAI calls"
}

variable "ci_genai_endpoint" {
  type    = string
  default = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
}

variable "ci_default_model" {
  type    = string
  default = "cohere.command-a-03-2025"
}

variable "load_balancer_shape_details_maximum_bandwidth_in_mbps" {
    description = "The OCI LB Max Bandwith"  
    type        = number
    default = 100
}

variable "load_balancer_shape_details_minimum_bandwidth_in_mbps" {
    description = "The OCI LB Max Bandwith"  
    type = number
    default = 10
}

variable "lb_name" {
    description = "The OCI LB Name"
    type        = string
    default     = "CI_FLEX_LB"
}

variable "lb_health_port" {
    description = "The OCI LB Health Port"
    type        = string
    default     = "8000"
}

variable "lb_checker_health_port" {
    description = "The OCI LB Health Checker Port"
    type        = string
    default     = "8000"
}

variable "lb_checker_url_path" {
    description = "The OCI LB Health Checker URL"
    type        = string
    default     = "/docs"
}

variable "lb_listener_port" {
    description = "The OCI LB Listener Port"
    type        = number
    default     = 8000
}

variable "lb_backend_port" {
    description = "The OCI LB Listener Port"
    type        = number
    default     = 8000
}

variable "is_public_ip_assigned" {
    description = "Does the CI has a public ip ?"
    type        = bool
    default     = false
}

