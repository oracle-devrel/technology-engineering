# ----------------------------------------------------------------------------------------------------
# ExaCC Status & Maintenance Reports
# Copyright © 2020-2022, Oracle and/or its affiliates. 
# All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
# ----------------------------------------------------------------------------------------------------

resource oci_events_rule exacc_maintenance {
    compartment_id = var.event_rules_compartment_ocid
    condition      = "{\"eventType\":[\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenance.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancereminder\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduled\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancescheduled\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancestorageservers.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancevm.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancecustomactiontime.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.begin\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancenetworkswitches.end\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancemethodchange\",\"com.oraclecloud.databaseservice.exaccinfrastructuremaintenancerescheduledwithreason\"],\"data\":{}}"
    display_name   = "ExaCC-Maintenance-Events"
    description    = "ExaCC maintenance Events"
    is_enabled     = "true"
    actions {
        actions {
            action_type = "FAAS"
            is_enabled  = "true"
            function_id = var.function_id
        }
    }

}