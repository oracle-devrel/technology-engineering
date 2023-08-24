# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# ----------------------------------------------------------------------------------------------------

data oci_objectstorage_namespace exacc_maintenance {
    compartment_id = var.tenancy_ocid
}

resource oci_objectstorage_bucket exacc_maintenance {
    compartment_id = var.bucket_compartment_ocid
    name           = var.bucket_name
    namespace      = data.oci_objectstorage_namespace.exacc_maintenance.namespace
}

