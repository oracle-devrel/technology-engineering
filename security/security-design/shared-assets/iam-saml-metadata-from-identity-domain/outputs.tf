
output "identity_domain_id" {
  description = "The OCID of the created identity domain."
  value       = oci_identity_domain.identity_domain.id
}

output "identity_domain_url" {
  description = "The URL of the created identity domain."
  value       = oci_identity_domain.identity_domain.url
}

output "identity_domain_home_region_url" {
  description = "The home region URL of the created identity domain."
  value       = oci_identity_domain.identity_domain.home_region_url
}
