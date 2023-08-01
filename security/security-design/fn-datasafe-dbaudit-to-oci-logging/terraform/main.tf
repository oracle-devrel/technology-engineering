###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################



module "setup-network" {
  source = "./modules/network"
  count  = var.create_network ? 1 : 0
  compartment_ocid = var.compartment_ocid
  vcn_cidr = var.vcn_cidr
  subnet_cidr = var.subnet_cidr
  vcndnslabelprefix = var.vcndnslabelprefix
  vcnnameprefix = var.vcnnameprefix
  vcnnameroutingtableprefix = var.vcnnameroutingtableprefix
  vcnroutingtabledescriptionservicegw = var.vcnroutingtabledescriptionservicegw
  vcnnamedhcpopitonsprefix = var.vcnnamedhcpopitonsprefix
  subnetnameprefix = var.subnetnameprefix
  subnetdnslabelprefix = var.subnetdnslabelprefix
  vcnnamesecuritylistprefix = var.vcnnamesecuritylistprefix
  vcnnameservicegatewayprefix = var.vcnnameservicegatewayprefix
  deployment_name = var.deployment_name
  region = var.region
  purpose = var.purpose
}
