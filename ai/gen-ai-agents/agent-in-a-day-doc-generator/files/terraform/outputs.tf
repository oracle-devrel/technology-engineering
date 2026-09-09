# --- Outputs ---

output "mcp_server_public_ip" {
  description = "Public IP of the MCP server instance"
  value       = oci_core_instance.mcp_server.public_ip
}

output "mcp_endpoint" {
  description = "MCP endpoint URL for OCI Agent Hub registration"
  value       = "http://${oci_core_instance.mcp_server.public_ip}:8000/mcp"
}

output "agent_endpoint_ocid" {
  description = "Agent endpoint OCID (used by MCP server for KB search)"
  value       = oci_generative_ai_agent_agent_endpoint.endpoint.id
}

output "documents_bucket" {
  description = "Upload your documents to this bucket"
  value       = oci_objectstorage_bucket.documents_bucket.name
}

output "reports_bucket" {
  description = "Generated reports are uploaded here"
  value       = oci_objectstorage_bucket.reports_bucket.name
}

output "object_storage_namespace" {
  description = "Object Storage namespace"
  value       = local.object_storage_namespace
}

output "ssh_private_key" {
  description = "SSH private key (if auto-generated)"
  value       = var.ssh_public_key != null ? "(provided externally)" : tls_private_key.ssh_key[0].private_key_pem
  sensitive   = true
}

output "upload_documents_command" {
  description = "Command to upload documents to the KB bucket"
  value       = "oci os object bulk-upload -ns ${local.object_storage_namespace} -bn ${oci_objectstorage_bucket.documents_bucket.name} --src-dir ../sample_docs --overwrite --content-type auto"
}

output "api_gateway_url" {
  description = "HTTPS endpoint for OCI Agent API endpoint tool"
  value       = "${oci_apigateway_gateway.mcp_gateway.hostname}/api/generate_report"
}

output "agent_private_subnet_ocid" {
  description = "Private subnet for OCI Agent PE (use when creating API endpoint tool)"
  value       = oci_core_subnet.agent_private_subnet.id
}

output "deploy_command" {
  description = "Command to deploy app code to the instance"
  value       = "scp -i <key> oci_auth.py docx_report.py server.py opc@${oci_core_instance.mcp_server.public_ip}:/home/opc/agent-day-doc-report/ && ssh -i <key> opc@${oci_core_instance.mcp_server.public_ip} 'sudo systemctl restart mcp-server'"
}
