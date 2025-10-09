resource "oci_container_instances_container_instance" "container_instance" {
  availability_domain = data.oci_identity_availability_domain.oci_ad.name
  compartment_id      = var.compartment_ocid
  containers {

    image_url    = "nginx"
    display_name = "nginx"

    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.log_mount_path
          volume_name = var.log_mount_name
    }
    volume_mounts {
          mount_path  = var.www_mount_path
          volume_name = var.www_mount_name
    }

  }
  containers {
    image_url    = var.sidecar_image
    display_name = "nginx-sidecar"
    environment_variables = {
      "log_ocid" = var.log_ocid
      "log_file" = "${var.log_mount_path}/${var.log_file}"
      "www_path" = var.www_mount_path
      "os_bucket" = var.www_data_bucket
    }

    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.log_mount_path
          volume_name = var.log_mount_name
    }
    volume_mounts {
          mount_path  = var.www_mount_path
          volume_name = var.www_mount_name
    }

  }
  shape = "CI.Standard.E4.Flex"
  shape_config {
    memory_in_gbs = "2"
    ocpus         = "1"
  }
  vnics {
    subnet_id = var.subnet_ocid
  }

  container_restart_policy = "ON_FAILURE"
  display_name             = "Nginx with OCI SDK sidecar"

  graceful_shutdown_timeout_in_seconds = "10"

  state = "ACTIVE"
  
  volumes {
      name          = var.log_mount_name
      volume_type   = "EMPTYDIR"
      backing_store = "EPHEMERAL_STORAGE"
  }
    
  volumes {
      name          = var.www_mount_name
      volume_type   = "EMPTYDIR"
      backing_store = "EPHEMERAL_STORAGE"
  }
}

data "oci_identity_availability_domain" "oci_ad" {

  compartment_id = var.tenancy_ocid
  ad_number      = var.ad_number
}