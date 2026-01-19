# Gets home and current regions
data "oci_identity_tenancy" "tenant_details" {
  tenancy_id = var.tenancy_ocid
}

data oci_identity_regions regions {
}

# HOME REGION
locals {
  region_map = {
    for r in data.oci_identity_regions.regions.regions :
    r.key => r.name
  } 
  # XXXXX ISSUE WITH CHILD TENANCY - BAD work-around - Works only from home tenancy
  home_region = coalesce( var.home_region, try( lookup( local.region_map, data.oci_identity_tenancy.tenant_details.home_region_key ), var.region ) )
}

# Provider Home Region
provider "oci" {
  alias  = "home"
  region = local.home_region
}