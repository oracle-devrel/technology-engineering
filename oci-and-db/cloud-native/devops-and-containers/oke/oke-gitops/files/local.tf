locals {
  git_username = "${data.oci_identity_tenancy.current_tenancy.name}/${data.oci_identity_user.current_user.name}"
}