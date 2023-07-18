# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform variable declaration file.
# @author: Vijay Kokatnur

# provider parameters
variable "tenancy_id" {
  description = "tenancy id where to create the sources"
  type        = string
  default     = ""
}

# general oci parameters
variable "compartment_id" {
  description = "compartment id where to create all resources"
  type        = string
}

variable "label_prefix" {
  description = "a string that will be prepended to all resources"
  type        = string
  default     = "none"
}

# network parameters
variable "availability_domain" {
  description = "the AD to place the  host"
  default     = 1
  type        = number
}

variable "access" {
  description = "A list of CIDR blocks to which ssh access to the  must be restricted to. *anywhere* is equivalent to 0.0.0.0/0 and allows ssh access from anywhere."
  default     = ["anywhere"]
  type        = list
}

variable "ig_route_id" {
  description = "the route id to the internet gateway"
  type        = string
}

variable "subnet_cidr" {
  description = "the route id to the internet gateway"
  type        = string
  default     = ""
}

variable "netnum" {
  description = "0-based index of the  subnet when the VCN's CIDR is masked with the corresponding newbit value."
  default     = 0
  type        = number
}

variable "newbits" {
  description = "The difference between the VCN's netmask and the desired  subnet mask"
  default     = 14
  type        = number
}

variable "vcn_cidr" {
  description = "The VCN cidr range."
  type        = string
}

variable "vcn_id" {
  description = "The id of the VCN to use when creating the  resources."
  type        = string
}

# tagging
variable "freeform_tags" {
  description = "Freeform tags for compute instance"
  default = {
    access      = "private"
    environment = "dev"
  }
  type = map(any)
}
