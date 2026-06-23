
locals {
  #create_script_bucket = try(data.oci_objectstorage_bucket.script_bucket.bucket_id != null ? false : true, true)
  #bucket_id = local.create_script_bucket ?  oci_objectstorage_bucket.script_bucket[0].bucket_id : data.oci_objectstorage_bucket.script_bucket.bucket_id
  files_to_upload = [
    "InstanceScripts/instancectl.bash.tftpl",
    "InstanceScripts/updatedns.bash.tftpl",
    "InstanceScripts/oci_cli_rc.tftpl",
    "InstanceScripts/oci-connectivity.bash.tftpl",
    "InstanceScripts/osmh-logs.bash.tftpl",
    "InstanceScripts/params.txt.tftpl",
    "InstanceScripts/register-to-osmh.bash.tftpl",
    "InstanceScripts/root-setup.bash.tftpl",
    "InstanceScripts/rpi-connect.bash.tftpl",
    "InstanceScripts/suicide.bash.tftpl",
    "InstanceScripts/tmux-default.bash.tftpl",
    "InstanceScripts/unregister-from-osmh.bash.tftpl",
    "InstanceScripts/user-setup.bash.tftpl",
  ]
}

output "compartment_name" {
  value = local.compartment.name
}
output "compartment_id" {
  value = local.compartment.id
}

# by using content transformation, file content changes trigger upload, not file metadata
resource "oci_objectstorage_object" "upload_files" {
  for_each                   = { for idx, filepath in local.files_to_upload : filepath => filepath }
  namespace                  = data.oci_objectstorage_namespace.namespace.namespace
  bucket                     = var.bucket_name
  #source                     = each.value                   # Local file path
  object                     = trimsuffix(basename(each.value), ".tftpl")  # Object name in bucket
  content     = templatefile(each.value, {
                  tf_eternal_terminal_nsg = local.et_nsg.display_name
                  tf_http_nsg             = local.http_nsg.display_name
                  tf_compartment_name     = local.compartment.name
                  tf_compartment_id       = local.compartment.id
                  tf_bucket_name          = var.bucket_name
                  tf_command_server_name  = var.command_server_name
                  tf_zone_name            = var.zone_name
                  tf_rpiconnect_name      = var.rpiconnect_name
                  DOLLAR = "$"
                })
  delete_all_object_versions = true
  content_type               = "text/plain" # Optional: set content type or derive per file
  depends_on                 = [ oci_objectstorage_bucket.script_bucket, ]
}

resource "oci_objectstorage_bucket" "script_bucket" {
  # this approach does not work. When terraform created the bucket,
  # the second apply sets the count to zero and the resource is destroyed
  #count          = local.create_script_bucket ? 1 : 0
  compartment_id = local.compartment.id
  namespace      = data.oci_objectstorage_namespace.namespace.namespace
  name           = var.bucket_name

  # Optional settings
  access_type    = "NoPublicAccess"  # Options: NoPublicAccess, ObjectRead, ObjectReadWithoutList
  storage_tier   = "Standard"        # Options: Standard, Archive
  versioning     = "Disabled"        # Options: Enabled, Disabled
  #lifecycle {
  #  prevent_destroy = true
  #}
}

