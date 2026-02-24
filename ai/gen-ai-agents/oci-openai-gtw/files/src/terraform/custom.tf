variable no_policy { default=null }

resource "oci_identity_policy" "starter_policy" {
    count          = var.no_policy=="true" ? 0 : 1      
    provider       = oci.home    
    name           = "${var.prefix}-policy"
    description    = "${var.prefix} policy"
    compartment_id = local.lz_serv_cmp_ocid

    statements = [
        "allow any-user to manage generative-ai-family in compartment id ${local.lz_serv_cmp_ocid} where request.principal.id='${oci_core_instance.starter_compute.id}'"
    ]
}

# APIGW
resource oci_apigateway_gateway starter_apigw {
  compartment_id = local.lz_app_cmp_ocid
  display_name  = "${var.prefix}-apigw"
  endpoint_type = "PUBLIC"
  subnet_id = data.oci_core_subnet.starter_web_subnet.id
  freeform_tags = local.freeform_tags       
}

locals {
  apigw_ocid = try(oci_apigateway_gateway.starter_apigw.id, "")
  apigw_ip   = try(oci_apigateway_gateway.starter_apigw.ip_addresses[0].ip_address,"")
}   

// API Management - Tags
variable git_url { 
  description = "Git URL"  
  default = "" 
  nullable = false
}
variable build_src { 
  default = "" 
  nullable = false
}

locals {
  api_git_tags = {
      group = local.group_name
      app_prefix = var.prefix

      api_icon = "python"
      api_git_url = var.git_url 
      api_git_spec_path = "src/app/openapi_spec.yaml"
      api_git_spec_type = "OpenAPI"
      api_git_endpoint_path = "src/terraform/apigw_existing.tf"
      api_endpoint_url = "app/dept"
  }
  api_tags = var.git_url !=""? local.api_git_tags:local.freeform_tags
}


# APIGW_DEPLOYMENT
locals {
  apigw_dest_private_ip = local.local_compute_ip
}

resource "oci_apigateway_deployment" "starter_apigw_deployment" {   
  compartment_id = local.lz_app_cmp_ocid
  display_name   = "${var.prefix}-apigw-deployment"
  gateway_id     = local.apigw_ocid
  path_prefix    = "/${var.prefix}"
  specification {
    logging_policies {
      access_log {
        is_enabled = true
      }
      execution_log {
        #Optional
        is_enabled = true
      }
    }
    routes {
      path    = "/app/{pathname*}"
      methods = [ "ANY" ]
      backend {
        type = "HTTP_BACKEND"
        url    = "http://${local.apigw_dest_private_ip}:8080/$${request.path[pathname]}"
        connect_timeout_in_seconds = 10
        read_timeout_in_seconds = 60
        send_timeout_in_seconds = 60              
      }
    }     
    routes {
      path    = "/{pathname*}"
      methods = [ "ANY" ]
      backend {
        type = "HTTP_BACKEND"
        url    = "http://${local.apigw_dest_private_ip}/$${request.path[pathname]}"
        connect_timeout_in_seconds = 10
        read_timeout_in_seconds = 60
        send_timeout_in_seconds = 60              
      }
    }
  }
  freeform_tags = local.api_tags
}