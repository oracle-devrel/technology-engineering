resource "oci_sch_service_connector" "soc_detection" {
  for_each = local.stream_definitions

  compartment_id = var.compartment_id
  display_name   = "sch-${each.key}-to-la"
  description    = "Routes ${each.key} stream to Log Analytics (${each.value.log_source})"
  state          = "ACTIVE"

  source {
    kind = "streaming"

    cursor {
      kind = "TRIM_HORIZON"
    }

    stream_id = oci_streaming_stream.soc_detection[each.key].id
  }

  target {
    kind         = "loggingAnalytics"
    log_group_id = oci_log_analytics_log_analytics_log_group.soc_detection.id

    dimensions {
      dimension_value {
        kind = "static"
        path = "logSourceName"
        value = each.value.log_source
      }
    }
  }

  freeform_tags = {
    "project" = "soc-detection-rules"
  }

  depends_on = [oci_identity_policy.sch_policies]
}
