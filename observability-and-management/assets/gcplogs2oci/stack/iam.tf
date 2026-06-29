# ─────────────────────────────────────────────────────────────
# iam.tf – IAM policies for Connector Hub
#
# Grants SCH permission to read from OCI Streaming and write
# to Log Analytics in the target compartment.
#
# Uses OCID-based compartment references (compartment id syntax)
# to avoid issues with compartment name resolution in nested
# hierarchies or names with special characters.
# ─────────────────────────────────────────────────────────────

resource "oci_identity_policy" "sch_streaming" {
  count = var.create_iam_policies ? 1 : 0

  compartment_id = var.tenancy_ocid
  name           = "gcplogs2oci-sch-streaming"
  description    = "Allow Connector Hub to read from OCI Streaming for the gcplogs2oci pipeline"

  statements = [
    "Allow any-user to use stream-pull in compartment id '${var.compartment_ocid}' where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use stream-consume in compartment id '${var.compartment_ocid}' where all {request.principal.type='serviceconnector'}",
  ]
}

resource "oci_identity_policy" "sch_log_analytics" {
  count = var.create_iam_policies ? 1 : 0

  compartment_id = var.tenancy_ocid
  name           = "gcplogs2oci-sch-log-analytics"
  description    = "Allow Connector Hub to write to Log Analytics for the gcplogs2oci pipeline"

  statements = [
    "Allow any-user to use log-analytics-log-group in compartment id '${var.compartment_ocid}' where all {request.principal.type='serviceconnector'}",
  ]
}
