variable "compartment_ocid" {
    description = "The OCI Compartment ocid"
    type        = string
}

variable "private_subnet_ocid" {
    description = "The OCI Private Subnet ocid"
    type        = string
}

#Use data to get ADs is better.
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
    default     = "CI.Standard.E4.Flex"
}

variable "ci_ocpus" {
    description = "The OCI Container Instance Ocpu Number"
    type        = number
    default     = 2
}

variable "ci_memory" {
    description = "The OCI Container Instance Memory GB Number"
    type        = number
    default     = 4
}

variable "ci_container_name" {
    description = "The OCI Container Name"
    type        = string
    default     = "CI_TRANSLATOR"
}

variable "ci_image_url" {
    description = "The OCI Container Image Url"
    type        = string
}

variable "ci_count" {
    description = "The OCI Container Instance Count Number"
    type        = number
}

variable "ci_registry_secret" {
    description = "The OCI Vault Secret Id with username and password of OCI registry"
    type        = string
}

variable "is_public_ip_assigned" {
    description = "Does the CI has a public ip ?"
    type        = bool
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

variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID passed to the container runtime"
}

variable "user_ocid" {
  type        = string
  description = "OCI user OCID passed to the container runtime"
}

variable "fingerprint" {
  type        = string
  description = "OCI API key fingerprint passed to the container runtime"
}

variable "private_api_key" {
  type        = string
  description = "OCI API private key content passed to the container runtime"
  sensitive   = true
}

variable "region" {
  type        = string
  description = "OCI region passed to the container runtime"
}

#Get Availaibility Domains. We use only first AD. 
#TODO Later (Add logic for multi Ads Domain)
data "oci_identity_availability_domains" "ADs" {
  compartment_id = "${var.compartment_ocid}"
}

resource "oci_container_instances_container_instance" "this" {
  count = var.ci_count
  compartment_id           = var.compartment_ocid
  display_name             = var.ci_name
  availability_domain      = "${lookup(data.oci_identity_availability_domains.ADs.availability_domains[0], "name")}"
  container_restart_policy = var.ci_restart_policy
  state                    = var.ci_state
  shape                    = var.ci_shape
  shape_config {
    ocpus         = var.ci_ocpus
    memory_in_gbs = var.ci_memory
  }
  vnics {
    display_name           = "nicnametest${count.index}"
    hostname_label         = "hostnametest${count.index}"
    subnet_id              = var.private_subnet_ocid
    skip_source_dest_check = false
    is_public_ip_assigned  = var.is_public_ip_assigned
  }
  containers {
    display_name          = "${var.ci_container_name}${count.index}"
    image_url             = var.ci_image_url

    environment_variables = {
      OCI_COMPARTMENT_ID      = var.ci_compartment_id_env
      OCI_GENAI_ENDPOINT      = var.ci_genai_endpoint
      OCI_DEFAULT_MODEL       = var.ci_default_model
      OCI_AUTH                = "api_key"
      OCI_PRIVATE_KEY_CONTENT = var.private_api_key
      OCI_TENANCY             = var.tenancy_ocid
      OCI_USER                = var.user_ocid
      OCI_FINGERPRINT         = var.fingerprint
      OCI_REGION              = var.region
    }
  }

  image_pull_secrets {
        #Required
        #registry_endpoint = "fra.ocir.io"
        registry_endpoint = "cdg.ocir.io"
        #secret_type = "BASIC"
        #username = base64encode("username")
        #password = base64encode("password")
        secret_type = "VAULT"
        secret_id = var.ci_registry_secret
    }
}
