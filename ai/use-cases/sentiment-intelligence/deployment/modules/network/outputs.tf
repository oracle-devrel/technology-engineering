output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.main.id
}

output "public_subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.public.id
}

output "private_subnet_id" {
  description = "OCID of the private subnet"
  value       = oci_core_subnet.private.id
}

output "db_subnet_id" {
  description = "OCID of the database subnet"
  value       = oci_core_subnet.db.id
}

output "db_nsg_id" {
  description = "OCID of the database NSG"
  value       = oci_core_network_security_group.db_nsg.id
}
