module vcn {
  source  = "oracle-terraform-modules/vcn/oci"
  version = "3.5.3"
  #providers = {
  #  oci = oci.target
  #}
  # insert the 5 required variables here
                 compartment_id = var.compartment_ocid
                         region = var.region

   internet_gateway_route_rules = null
         local_peering_gateways = null
        nat_gateway_route_rules = null

  # Optional Inputs
                       vcn_name = "${var.vcndef.name}"
                  vcn_dns_label = var.vcndef.name
                      vcn_cidrs = var.vcndef.cidr

        create_internet_gateway = true
             create_nat_gateway = true
         create_service_gateway = true

}

