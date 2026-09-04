variable "tenancy_ocid" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.tenancy\\.", var.tenancy_ocid))
    error_message = "tenancy_ocid must be a tenancy OCID."
  }
}

variable "region" {
  type = string
  validation {
    condition     = length(trimspace(var.region)) > 0
    error_message = "region must not be empty."
  }
}

# NETWORK

variable "network_compartment_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.(compartment|tenancy)\\.", var.network_compartment_id))
    error_message = "network_compartment_id must be a compartment or tenancy OCID."
  }
}
variable "cni_type" {
  type    = string
  default = "vcn_native"
  validation {
    condition     = contains(["vcn_native", "flannel"], var.cni_type)
    error_message = "cni_type must be either vcn_native or flannel."
  }
}
variable "vcn_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.vcn\\.", var.vcn_id))
    error_message = "vcn_id must be a VCN OCID."
  }
}
variable "lb_subnet_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.subnet\\.", var.lb_subnet_id))
    error_message = "lb_subnet_id must be a subnet OCID."
  }
}
variable "cp_subnet_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.subnet\\.", var.cp_subnet_id))
    error_message = "cp_subnet_id must be a subnet OCID."
  }
}
variable "cp_nsg_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.networksecuritygroup\\.", var.cp_nsg_id))
    error_message = "cp_nsg_id must be a network security group OCID."
  }
}
variable "worker_subnet_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.subnet\\.", var.worker_subnet_id))
    error_message = "worker_subnet_id must be a subnet OCID."
  }
}
variable "worker_nsg_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.networksecuritygroup\\.", var.worker_nsg_id))
    error_message = "worker_nsg_id must be a network security group OCID."
  }
}
variable "pod_nsg_id" {
  type    = string
  default = null
  validation {
    condition     = var.pod_nsg_id == null || can(regex("^ocid1\\.networksecuritygroup\\.", var.pod_nsg_id))
    error_message = "pod_nsg_id must be null or a network security group OCID."
  }
}
variable "pod_subnet_id" {
  type    = string
  default = null
  validation {
    condition     = var.pod_subnet_id == null || can(regex("^ocid1\\.subnet\\.", var.pod_subnet_id))
    error_message = "pod_subnet_id must be null or a subnet OCID."
  }
}
variable "cp_allowed_cidr_list" {
  type    = list(string)
  default = ["0.0.0.0/0"]
  validation {
    condition     = length(var.cp_allowed_cidr_list) > 0 && alltrue([for cidr in var.cp_allowed_cidr_list : can(cidrnetmask(cidr))])
    error_message = "cp_allowed_cidr_list must contain at least one valid IPv4 CIDR block."
  }
}


# CLUSTER

variable "oke_compartment_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.(compartment|tenancy)\\.", var.oke_compartment_id))
    error_message = "oke_compartment_id must be a compartment or tenancy OCID."
  }
}
variable "cluster_name" {
  type    = string
  default = "oke-rm-quickstart"
  validation {
    condition     = length(trimspace(var.cluster_name)) > 0
    error_message = "cluster_name must not be empty."
  }
}
variable "kubernetes_version" {
  type = string
  validation {
    condition     = can(regex("^v?[0-9]+\\.[0-9]+(\\.[0-9]+)?$", var.kubernetes_version))
    error_message = "kubernetes_version must be a Kubernetes version such as v1.35.1."
  }
}

variable "cluster_type" {
  type    = string
  default = "enhanced"
  validation {
    condition     = contains(["enhanced", "basic"], var.cluster_type)
    error_message = "cluster_type must be either enhanced or basic."
  }
}

variable "services_cidr" {
  type    = string
  default = "10.96.0.0/16"
  validation {
    condition     = can(cidrnetmask(var.services_cidr))
    error_message = "services_cidr must be a valid IPv4 CIDR block."
  }
}

variable "pods_cidr" {
  type    = string
  default = "10.244.0.0/16"
  validation {
    condition     = can(cidrnetmask(var.pods_cidr))
    error_message = "pods_cidr must be a valid IPv4 CIDR block."
  }
}

# ADD-ONS

variable "enable_cert_manager" {
  type    = bool
  default = true
}

variable "enable_metrics_server" {
  type    = bool
  default = true
}

# SECURITY

variable "kms_compartment_id" {
  type    = string
  default = null
  validation {
    condition     = var.kms_compartment_id == null || can(regex("^ocid1\\.(compartment|tenancy)\\.", var.kms_compartment_id))
    error_message = "kms_compartment_id must be null or a compartment or tenancy OCID."
  }
}

variable "oke_vault_id" {
  type    = string
  default = null
  validation {
    condition     = var.oke_vault_id == null || can(regex("^ocid1\\.vault\\.", var.oke_vault_id))
    error_message = "oke_vault_id must be null or a Vault OCID."
  }
}

variable "cluster_kms_key_id" {
  type    = string
  default = null
  validation {
    condition     = var.cluster_kms_key_id == null || can(regex("^ocid1\\.key\\.", var.cluster_kms_key_id))
    error_message = "cluster_kms_key_id must be null or a KMS key OCID."
  }
}

# POLICIES

variable "enable_policies" {
  type    = bool
  default = false
}

variable "policies_dry_run" {
  type    = bool
  default = false
}

variable "create_karpenter_policies" {
  type    = bool
  default = false
}

variable "iam_domain_compartment_id" {
  default = null
}

variable "karpenter_iam_domain_id" {
  default = null
}

variable "karpenter_dynamic_group_name" {
  default = null
}

variable "karpenter_namespace" {
  type    = string
  default = "karpenter"
  validation {
    condition     = length(trimspace(var.karpenter_namespace)) > 0
    error_message = "karpenter_namespace must not be empty."
  }
}

variable "karpenter_service_account" {
  type    = string
  default = "karpenter"
  validation {
    condition     = length(trimspace(var.karpenter_service_account)) > 0
    error_message = "karpenter_service_account must not be empty."
  }
}

variable "create_karpenter_cluster_placement_group_policy_optional" {
  type    = bool
  default = false
}

variable "create_karpenter_tag_policy_optional" {
  type    = bool
  default = false
}

variable "tag_compartment_id" {
  default = null
}

variable "create_karpenter_capacity_reservation_policy_optional" {
  type    = bool
  default = false
}

variable "create_karpenter_compute_cluster_policy_optional" {
  type    = bool
  default = false
}

variable "create_autoscaler_policies" {
  type    = bool
  default = false
}


# OIDC

variable "enable_oidc_discovery" {
  type    = bool
  default = false
}

variable "enable_oidc_authentication" {
  type    = bool
  default = false
}

variable "oidc_issuer" {
  type    = string
  default = null
  validation {
    condition     = var.oidc_issuer == null || can(regex("^https://", var.oidc_issuer))
    error_message = "oidc_issuer must be null or an HTTPS URL."
  }
}
variable "oidc_client_id" {
  default = null
}
variable "oidc_username_claim" {
  default = "sub"
}
variable "oidc_username_prefix" {
  default = "oidc:"
}
variable "oidc_groups_claim" {
  default = "groups"
}
variable "oidc_groups_prefix" {
  default = "oidc:"
}

# Tagging

variable "tag_value" {
  type = object({
    freeformTags = map(string)
    definedTags  = map(string)
  })
  default = null
}
