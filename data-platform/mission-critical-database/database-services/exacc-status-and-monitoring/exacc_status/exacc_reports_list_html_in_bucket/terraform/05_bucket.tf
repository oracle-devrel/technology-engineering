# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

data oci_objectstorage_namespace namespace {
  compartment_id = var.compartment_ocid
}

# resource oci_objectstorage_bucket exacc_daily_reports {
#   compartment_id = var.compartment_ocid
#   name           = var.bucket_name
#   namespace      = data.oci_objectstorage_namespace.namespace.namespace
#   access_type    = "NoPublicAccess"
# }

resource oci_objectstorage_preauthrequest exacc_daily_reports  {
  access_type  = "AnyObjectRead"
  bucket       = var.bucket_name
  name         = "par-bucket-read"
  namespace    = data.oci_objectstorage_namespace.namespace.namespace
  time_expires = "2024-12-31T23:59:59Z"
}

output PAR {
    value = "https://objectstorage.${var.region}.oraclecloud.com${oci_objectstorage_preauthrequest.exacc_daily_reports.access_uri}"
}