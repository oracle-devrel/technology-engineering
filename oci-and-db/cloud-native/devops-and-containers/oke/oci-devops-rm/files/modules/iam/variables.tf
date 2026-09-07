variable "compartment_id" {}
variable "iam_domain_id" {}
variable "network_compartment_id" {}
variable "prod_network_compartment_id" {}
variable "oke_compartment_id" {}
variable "prod_oke_compartment_id" {}
variable "secret_compartment_id" {}
variable "devops_policy_name" {}
variable "dynamic_group_name" {}
variable "enable_oke_access" {
  type = bool
}
variable "enable_secret_access" {
  type = bool
}
