################################################################################
# Copyright (c) 2023, Oracle and/or its affiliates. All rights reserved.
# This software is dual-licensed to you under the Universal Permissive 
# License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl
################################################################################



variable "compartment_ocid" {
  description = "the OCID of the compartment where the environment will be created."
}

variable "VCN-CIDR" {
  default = "10.0.0.0/22"
  description = "The CIDR block of VCN"
}

variable "subnet-CIDR" {
  default = "10.0.1.0/24"
}

variable "vcndnslabelprefix" {
  default = "dnsepl"
}

variable "vcnnameprefix" {
  default = "vnc"
  description = "The prefix display name of VCN"
}

variable "vcnnameroutingtableprefix" {
  default = "rt"
}

variable "vcnroutingtabledescriptionservicegw" {
  default = "Route for Service Gateway"
}

variable "vcnnamedhcpopitonsprefix" {
  default = "dhcpo"
}

variable "subnetnameprefix" {
  default = "sub"
}

variable "subnetdnslabelprefix" {
  default = "dnsepl"
}

variable "vcnnamesecuritylistprefix" {
  default = "sl"
}
variable "vcnnameservicegatewayprefix" {
  default = "sgw"
}
