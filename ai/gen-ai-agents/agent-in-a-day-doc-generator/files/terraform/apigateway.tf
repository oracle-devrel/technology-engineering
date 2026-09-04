# --- API Gateway (HTTPS termination for the MCP server) ---

resource "oci_apigateway_gateway" "mcp_gateway" {
  compartment_id = var.compartment_ocid
  endpoint_type  = "PUBLIC"
  subnet_id      = oci_core_subnet.mcp_subnet.id
  display_name   = "${var.prefix}-api-gw"
  freeform_tags  = local.freeform_tags
}

resource "oci_apigateway_deployment" "mcp_deployment" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.mcp_gateway.id
  path_prefix    = "/"
  display_name   = "${var.prefix}-api-deployment"

  specification {
    routes {
      path    = "/api/generate_report"
      methods = ["POST"]
      backend {
        type                       = "HTTP_BACKEND"
        url                        = "http://${oci_core_instance.mcp_server.private_ip}:8000/api/generate_report"
        connect_timeout_in_seconds = 30
        read_timeout_in_seconds    = 300
        send_timeout_in_seconds    = 300
      }
    }
    routes {
      path    = "/api/report_status"
      methods = ["GET"]
      backend {
        type = "HTTP_BACKEND"
        url  = "http://${oci_core_instance.mcp_server.private_ip}:8000/api/report_status"
      }
    }
    routes {
      path    = "/api/health"
      methods = ["GET"]
      backend {
        type = "HTTP_BACKEND"
        url  = "http://${oci_core_instance.mcp_server.private_ip}:8000/api/health"
      }
    }
  }

  freeform_tags = local.freeform_tags
}
