terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source = "hashicorp/oci"
    } 
    null = {
      source = "hashicorp/null"
    }
  }
}

resource "oci_identity_domain" "identity_domain" {
  compartment_id     = var.compartment_id
  display_name       = var.domain_display_name
  description        = var.domain_description
  is_hidden_on_login = var.is_hidden_on_login
  license_type       = var.license_type
  home_region        = var.region
}

# Wait until the thing exists.
resource "null_resource" "configure_idcs_app" {
  depends_on = [oci_identity_domain.identity_domain]

  triggers = {
    identity_domain_id = oci_identity_domain.identity_domain.id
  }

  provisioner "local-exec" {
    when    = create
    command = "${path.module}/scripts/create_confidential_app_and_get_saml_meta_data.sh"
    environment = {
      IDCS_ENDPOINT = oci_identity_domain.identity_domain.url
      PROFILE       = var.oci_profile
    }
  }
}
