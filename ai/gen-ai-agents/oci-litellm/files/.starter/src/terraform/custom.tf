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
      path    = "/{pathname*}"
      methods = [ "ANY" ]
      backend {
        type = "HTTP_BACKEND"
        url    = "http://${local.local_compute_ip}:8080/$${request.path[pathname]}"
      }
    }     
  }
  freeform_tags = local.freeform_tags
}


## CUSTOM DEPENDENCY (Add your dependency before building the app)
resource "null_resource" "custom_dependency" {
  depends_on = [
    oci_apigateway_deployment.starter_apigw_deployment
  ]
}