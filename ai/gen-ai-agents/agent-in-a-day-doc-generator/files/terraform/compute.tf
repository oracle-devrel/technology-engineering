# --- Compute Instance with cloud-init ---

resource "oci_core_instance" "mcp_server" {
  availability_domain = local.availability_domain_name
  compartment_id      = var.compartment_ocid
  display_name        = "${var.prefix}-mcp-server"
  shape               = local.shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id                 = oci_core_subnet.mcp_subnet.id
    assign_public_ip          = true
    display_name              = "primaryvnic"
    assign_private_dns_record = true
    hostname_label            = "${var.prefix}-mcp"
  }

  metadata = {
    ssh_authorized_keys = local.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      oci_region          = var.region
      agent_endpoint_ocid = oci_generative_ai_agent_agent_endpoint.endpoint.id
      compartment_ocid    = var.compartment_ocid
      genai_model         = var.genai_model
      os_namespace        = local.object_storage_namespace
      reports_bucket      = oci_objectstorage_bucket.reports_bucket.name
    }))
  }

  source_details {
    source_type             = "image"
    boot_volume_size_in_gbs = 50
    source_id               = data.oci_core_images.oraclelinux.images.0.id
  }

  lifecycle {
    ignore_changes = [
      source_details[0].source_id,
      shape
    ]
  }

  freeform_tags = local.freeform_tags
}

# --- Policy for Instance Principals (no dynamic group needed) ---

resource "oci_identity_policy" "mcp_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.prefix}-mcp-policy"
  description    = "Allow MCP server to use GenAI, Agent Runtime, and Object Storage"
  statements = [
    "allow any-user to manage generative-ai-family in compartment id ${var.compartment_ocid} where request.principal.id='${oci_core_instance.mcp_server.id}'",
    "allow any-user to manage genai-agent-family in compartment id ${var.compartment_ocid} where request.principal.id='${oci_core_instance.mcp_server.id}'",
    "allow any-user to manage object-family in compartment id ${var.compartment_ocid} where request.principal.id='${oci_core_instance.mcp_server.id}'",
  ]
  freeform_tags = local.freeform_tags
}
