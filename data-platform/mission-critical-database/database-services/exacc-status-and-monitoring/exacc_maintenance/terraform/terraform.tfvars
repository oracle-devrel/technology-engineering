# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

tenancy_ocid             = "ocid1.tenancy.oc1..<unique_ID>"
user_ocid                = "ocid1.user.oc1..<unique_ID>"
fingerprint              = "00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:01"
private_key_path         = "/<path>/<to>/.oci/mykey.pem"
region                   = "<region>"     

network_compartment_ocid = "ocid1.compartment.oc1..<unique_ID>"   
bucket_compartment_ocid  = "ocid1.compartment.oc1..<unique_ID>"  
vault_compartment_ocid   = "ocid1.compartment.oc1..<unique_ID>"    
function_id              = "ocid1.fnfunc.oc1.<region>.<unique_ID>"
bucket_name              = "ExaCC_maintenance_reports"
vault_id                 = "ocid1.vault.oc1.<region>.<unique_ID>.<unique_ID>"
vault_secret_id          = "ocid1.vaultsecret.<region>.<unique_ID>"
