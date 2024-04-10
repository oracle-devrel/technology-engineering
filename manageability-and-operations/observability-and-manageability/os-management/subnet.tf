# Source from https://registry.terraform.io/providers/hashicorp/oci/latest/docs/resources/core_subnet

resource oci_core_subnet vcn-subnet{

  # Required
  #compartment_id = oci_identity_compartment.tf-compartment.id
  compartment_id = var.compartment_ocid
          vcn_id = module.vcn.vcn_id
        for_each = var.vcndef.subnets
      cidr_block = each.value.cidr
 
  # Optional
             route_table_id = module.vcn.ig_route_id
          security_list_ids = each.value.private ?  [oci_core_security_list.private-security-list.id] : [oci_core_security_list.public-security-list.id]
               display_name = "${each.key}"
  prohibit_internet_ingress = each.value.private
}
