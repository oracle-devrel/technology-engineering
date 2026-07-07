resource "oci_log_analytics_log_analytics_log_group" "soc_detection" {
  compartment_id = var.compartment_id
  namespace      = local.la_namespace
  display_name   = var.log_group_name
  description    = var.log_group_description
}
