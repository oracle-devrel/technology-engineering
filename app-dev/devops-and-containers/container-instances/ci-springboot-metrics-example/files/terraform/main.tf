resource "oci_container_instances_container_instance" "container_instance" {
  availability_domain = data.oci_identity_availability_domain.oci_ad.name
  compartment_id      = var.compartment_ocid
  
  #### LIST ALL APP CONTAINERS HERE ####
  
  containers {

    image_url    = "${var.ocir_region}/${data.oci_objectstorage_namespace.objectstorage_namespace.namespace}/${var.app_image_1}"
    display_name = "Java demo"
    
    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.log_mount_path
          volume_name = var.log_mount_name
    }
  }
  
  containers {
    image_url    = "${var.ocir_region}/${data.oci_objectstorage_namespace.objectstorage_namespace.namespace}/${var.sidecar_image}"
    display_name = "sidecar"
    environment_variables = {
      "config_bucket" = var.config_bucket
      "config_path" = var.config_mount_path
      "log_file" = "${var.log_mount_path}/${var.log_file}"
      "log_ocid" = var.log_ocid
      "reload_delay" = var.config_reload_delay
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
          mount_path  = var.config_mount_path
          volume_name = var.config_mount_name
    }

  }
  
  containers {

    image_url    = var.prometheus_node_exporter_image
    display_name = "prometheus Node Exporter"
    environment_variables = {
    }
    
    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.config_mount_path
          volume_name = var.config_mount_name
    }
  }
  
  containers {
    arguments = [
      "--config.file=${var.config_mount_path}/prometheus/prometheus.yml",
      "--enable-feature=auto-reload-config",
      "--config.auto-reload-interval=30s"
    ]
    image_url    = var.prometheus_image
    display_name = "prometheus"
    environment_variables = {
    }
    
    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.config_mount_path
          volume_name = var.config_mount_name
    } 
  }
  
  containers {
    arguments = [
    ]
    image_url    = var.grafana_image
    display_name = "grafana"
    environment_variables = {
    }
    
    is_resource_principal_disabled = "false"
    resource_config {
      memory_limit_in_gbs = "1.0"
      vcpus_limit         = "1.0"
    }
    volume_mounts {
          mount_path  = var.config_mount_path
          volume_name = var.config_mount_name
    } 
  }
  
  #######################################
  
  shape = "CI.Standard.E4.Flex"
  shape_config {
    memory_in_gbs = "16"
    ocpus         = "1"
  }
  
  vnics {
    subnet_id = var.subnet_ocid
  }

  container_restart_policy = "ON_FAILURE"
  display_name             = "Prometheus Grafana CI example"

  graceful_shutdown_timeout_in_seconds = "10"

  state = "ACTIVE"
  
  volumes {
      name          = var.log_mount_name
      volume_type   = "EMPTYDIR"
      backing_store = "EPHEMERAL_STORAGE"
  }
    
  volumes {
      name          = var.config_mount_name
      volume_type   = "EMPTYDIR"
      backing_store = "EPHEMERAL_STORAGE"
  }
}

data "oci_identity_availability_domain" "oci_ad" {

  compartment_id = var.tenancy_ocid
  ad_number      = var.ad_number
}

data "oci_objectstorage_namespace" "objectstorage_namespace" {
  compartment_id = var.compartment_ocid
}