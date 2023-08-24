# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

resource oci_identity_dynamic_group exacc_daily_reports {
    compartment_id = var.tenancy_ocid
    description    = "Dynamic group for ExaCC daily reports function"
    matching_rule  = "resource.id = '${var.function_id}'"
    name           = "ExaCC-daily-reports"
}

resource oci_identity_policy exacc_daily_reports {
    compartment_id = var.compartment_ocid
    description    = "Policy for ExaCC daily reports function"
    name           = "ExaCC-daily-reports"
    statements     = [ 
        "Allow dynamic-group ExaCC-daily-reports to read buckets in compartment id ${var.compartment_ocid} where target.bucket.name='${var.bucket_name}'",
        "Allow dynamic-group ExaCC-daily-reports to manage objects in compartment id ${var.compartment_ocid} where target.bucket.name='${var.bucket_name}'" ]
}