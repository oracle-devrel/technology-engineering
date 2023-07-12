###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

# Container Registry Policies


resource "oci_artifacts_container_repository" "fn_container_repository" {
  
  compartment_id = var.compartment_ocid
  display_name   = "${var.ocir_repo_name}-${var.deployment_name}-${random_id.tag.hex}"
}
