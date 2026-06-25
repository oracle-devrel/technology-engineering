resource "oci_identity_policy" "sch_policies" {
  compartment_id = var.tenancy_ocid
  name           = "soc-detection-sch-policies"
  description    = "IAM policies for SOC Detection Service Connector Hub pipelines"

  statements = [
    "Allow any-user to use stream-pull in compartment id ${var.compartment_id} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use stream-push in compartment id ${var.compartment_id} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to {LOG_ANALYTICS_LOG_GROUP_UPLOAD_LOGS} in compartment id ${var.compartment_id} where all {request.principal.type='serviceconnector'}",
  ]
}
