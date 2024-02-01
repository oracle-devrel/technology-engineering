###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

locals {
    resource_nc = "-${var.deployment_name}-${var.region}-${var.purpose}-${random_id.tag.hex}"
    resource_nc_dnslabel = "${var.deployment_name}${random_id.tag.hex}"
    vcn_dns_label = "${var.vcndnslabelprefix}${local.resource_nc_dnslabel}"
    vcn_displayname = "${var.vcnnameprefix}${local.resource_nc}"
    service_gw_displayname = "${var.vcnnameservicegatewayprefix}${local.resource_nc}"
    vcnnameroutingtable_displayname = "${var.vcnnameroutingtableprefix}${local.resource_nc}"
    dhcpoptions_displayname = "${var.vcnnamedhcpopitonsprefix}${local.resource_nc}"
    subnet_displayname = "${var.subnetnameprefix}${local.resource_nc}"
    subnet_dns_label = "${var.subnetdnslabelprefix}${local.resource_nc_dnslabel}"
    vcn_securitylist_displayname = "${var.vcnnamesecuritylistprefix}${local.resource_nc}"
}