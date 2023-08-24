# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# ----------------------------------------------------------------------------------------------------

resource oci_functions_application exacc_maintenance {
    compartment_id = var.function_compartment_ocid
    display_name   = "ExaCC_app"
    subnet_ids     = [ oci_core_subnet.exacc_maintenance.id ]
}