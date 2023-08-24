# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

resource oci_events_rule exacc_daily_reports {
    compartment_id = var.compartment_ocid
    #condition      = "{\"eventType\":[\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancereminder\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduled\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancescheduled\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancemethodchange\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduledwithreason\"],\"data\":{}}"
    condition      = "{\"eventType\":[\"com.oraclecloud.objectstorage.createobject\"],\"data\":{\"additionalDetails\":{\"bucketName\":[\"${var.bucket_name}\"]}}}"
    display_name   = "ExaCC-daily-reports-Events"
    description    = "ExaCC-daily-reports-Events (cpauliat, June 2022)"
    is_enabled     = "true"
    actions {
        actions {
            action_type = "FAAS"
            is_enabled  = "true"
            function_id = var.function_id
        }
    }
}