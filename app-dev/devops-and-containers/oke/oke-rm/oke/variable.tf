variable "tenancy_ocid" {}
variable "region" {}
variable "home_region" {}

# NETWORK

variable "network_compartment_id" {}
variable "cni_type" {
  default = "vcn_native"
}
variable "vcn_id" {}
variable "lb_subnet_id" {}
variable "cp_subnet_id" {}
variable "cp_nsg_id" {}
variable "worker_subnet_id" {}
variable "worker_nsg_id" {}
variable "pod_nsg_id" {
  default = null
}
variable "pod_subnet_id" {
  default = null
}
variable "cp_allowed_cidr_list" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}


# CLUSTER

variable "oke_compartment_id" {}
variable "cluster_name" {
  default = "oke-rm-quickstart"
}
variable "kubernetes_version" {}

variable "cluster_type" {
  default = "enhanced"
}

variable "services_cidr" {
  default = "10.96.0.0/16"
}

variable "pods_cidr" {
  default = "10.244.0.0/16"
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
  default = null
}

variable "oke_vault_id" {
  default = null
}

variable "cluster_kms_key_id" {
  default = null
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
  default = null
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