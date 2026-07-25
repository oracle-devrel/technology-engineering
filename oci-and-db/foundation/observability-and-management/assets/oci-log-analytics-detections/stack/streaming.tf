resource "oci_streaming_stream" "soc_detection" {
  for_each = local.stream_definitions

  name               = each.key
  partitions         = var.stream_partitions
  retention_in_hours = var.stream_retention_hours

  # Use stream pool if provided, otherwise place in compartment directly
  stream_pool_id = var.stream_pool_id != "" ? var.stream_pool_id : null
  compartment_id = var.stream_pool_id == "" ? var.compartment_id : null

  freeform_tags = {
    "project"    = "soc-detection-rules"
    "log_source" = each.value.log_source
  }
}
