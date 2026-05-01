# --- Object Storage Buckets ---

# Documents bucket — upload your files here, KB ingests from this bucket
resource "oci_objectstorage_bucket" "documents_bucket" {
  compartment_id        = var.compartment_ocid
  namespace             = local.object_storage_namespace
  name                  = "${var.prefix}-documents"
  object_events_enabled = true
  freeform_tags         = local.freeform_tags
}

# Reports bucket — generated DOCX reports are uploaded here
resource "oci_objectstorage_bucket" "reports_bucket" {
  compartment_id = var.compartment_ocid
  namespace      = local.object_storage_namespace
  name           = "${var.prefix}-reports"
  freeform_tags  = local.freeform_tags
}
