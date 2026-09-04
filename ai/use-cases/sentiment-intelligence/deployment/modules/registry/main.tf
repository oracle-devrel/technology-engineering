# =============================================================================
# OCI Container Registry (OCIR) Module
# =============================================================================

resource "oci_artifacts_container_repository" "backend" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.repo_name}/backend"
  is_public      = false
  freeform_tags  = var.freeform_tags
}

resource "oci_artifacts_container_repository" "frontend" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.repo_name}/frontend"
  is_public      = false
  freeform_tags  = var.freeform_tags
}
