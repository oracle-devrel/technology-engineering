# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# ----------------------------------------------------------------------------------------------------

resource oci_identity_dynamic_group exacc_maintenance {
    compartment_id = var.tenancy_ocid
    description    = "Dynamic group for ExaCC maintenance report function"
    matching_rule  = "resource.id = '${var.function_id}'"
    name           = "ExaCC-maintenance"
}

resource oci_identity_policy exacc_maintenance {
    compartment_id = var.tenancy_ocid
    description    = "Policy for ExaCC maintenance report function"
    name           = "ExaCC-maintenance"
    statements     = [ 
        "Allow dynamic-group ExaCC-maintenance to use secret-family in compartment id ${var.vault_compartment_ocid}",
        "Allow dynamic-group ExaCC-maintenance to read vaults in compartment id ${var.vault_compartment_ocid} where target.vault.id='${var.vault_id}'",
        "Allow dynamic-group ExaCC-maintenance to read secrets in compartment id ${var.vault_compartment_ocid} where target.secret.id='${var.vault_secret_id}'",
        "Allow dynamic-group ExaCC-maintenance to read exadata-infrastructures in tenancy",
        "Allow dynamic-group ExaCC-maintenance to read buckets in compartment id ${var.bucket_compartment_ocid} where target.bucket.name='${var.bucket_name}'",
        "Allow dynamic-group ExaCC-maintenance to manage buckets in compartment id ${var.bucket_compartment_ocid} where all { target.bucket.name='${var.bucket_name}', request.permission='PAR_MANAGE' }",
        "Allow dynamic-group ExaCC-maintenance to manage objects in compartment id ${var.bucket_compartment_ocid} where target.bucket.name='${var.bucket_name}'",
        "Allow service FaaS to use virtual-network-family in compartment id ${var.network_compartment_ocid}",
        "Allow service FaaS to read repos in tenancy" ]
}