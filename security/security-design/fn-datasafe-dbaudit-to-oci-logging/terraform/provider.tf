###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
# comment for stack zip file
  user_ocid        = var.user_ocid
# comment for stack zip file
  fingerprint      = var.fingerprint
# comment for stack zip file
  private_key_path = var.private_key_path
  region           = var.region
}

provider "oci" {
  alias                = "homeregion"
  tenancy_ocid         = var.tenancy_ocid
# comment for stack zip file
  user_ocid            = var.user_ocid
# comment for stack zip file
  fingerprint          = var.fingerprint
# comment for stack zip file
  private_key_path     = var.private_key_path
  region               = data.oci_identity_region_subscriptions.home_region_subscriptions.region_subscriptions[0].region_name
  disable_auto_retries = "true"
}
