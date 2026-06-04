variable tenancy_ocid {}
variable region {}
variable compartment_ocid {}
variable prefix { default = "starter" }
variable username {}
variable auth_token {}

#############################################################################
terraform {
  backend "local" { 
    path = "../../target/devops.tfstate" 
  }
}

#############################################################################
provider "oci" {
  alias        = "current_region"
  tenancy_ocid = var.tenancy_ocid
  region       = var.region

  #user_ocid        = var.current_user_ocid
  #fingerprint      = var.fingerprint
  #private_key_path = var.private_key_path
}

#############################################################################

data "oci_identity_tenancy" "tenant_details" {
  tenancy_id = var.tenancy_ocid
  provider   = oci.current_region
}

data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

locals {
  ocir_namespace = lookup(data.oci_objectstorage_namespace.ns, "namespace")
}

resource "random_string" "id" {
  length  = 4
  special = false
}

#############################################################################

# Create OCI Notification
resource "oci_ons_notification_topic" "starter_devops_notification_topic" {
  compartment_id = var.compartment_ocid
  name           = "${var.prefix}-devops-topic-${random_string.id.result}"
}

# Create devops project
resource "oci_devops_project" "starter_devops_project" {
  compartment_id = var.compartment_ocid
  name           = "${var.prefix}-devops"
  description    = "${var.prefix}-devops"

  notification_config {
    #Required
    topic_id = oci_ons_notification_topic.starter_devops_notification_topic.id
  }
}

# Create log and log group
resource "oci_logging_log_group" "starter_devops_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.prefix}-devops-log-group"
}

resource "oci_logging_log" "starter_devops_log" {
  #Required
  display_name = "${var.prefix}-devops-log"
  log_group_id = oci_logging_log_group.starter_devops_log_group.id
  log_type     = "SERVICE"

  #Optional
  configuration {
    #Required
    source {
      #Required
      category    = "all"
      resource    = oci_devops_project.starter_devops_project.id
      service     = "devops"
      source_type = "OCISERVICE"
    }
    #Optional
    compartment_id = var.compartment_ocid
  }
  is_enabled         = true
  retention_duration = "30"
}

#############################################################################
# Used to run terraform from DevOps to keep the state in a fixed place
# Not needed when using ResourceManager
resource "oci_objectstorage_bucket" "starter_devops_bucket" {
  compartment_id = var.compartment_ocid
  namespace      = local.ocir_namespace
  name           = "${var.prefix}-devops-bucket"
  access_type    = "NoPublicAccess"
}

resource "oci_objectstorage_object" "starter_devops_object" {
  namespace           = local.ocir_namespace
  bucket              = oci_objectstorage_bucket.starter_devops_bucket.name
  object              = "terraform.tfstate"
  content_language    = "en-US"
  content_type        = "text/plain"
  content             = ""
  content_disposition = "attachment; filename=\"filename.html\""
}

resource "oci_objectstorage_preauthrequest" "starter_devops_object_par" {
  namespace    = local.ocir_namespace
  bucket       = oci_objectstorage_bucket.starter_devops_bucket.name
  object_name  = oci_objectstorage_object.starter_devops_object.object
  name         = "objectPar"
  access_type  = "ObjectReadWrite"
  time_expires = "2050-01-01T00:00:00Z"
}

locals {
  par_request_url = "https://objectstorage.${var.region}.oraclecloud.com${oci_objectstorage_preauthrequest.starter_devops_object_par.access_uri}"
}

#############################################################################

resource "oci_devops_repository" "starter_devops_repository" {
  #Required
  name       = "${var.prefix}"
  project_id = oci_devops_project.starter_devops_project.id

  #Optional
  default_branch = "main"
  description    = "${var.prefix} GIT Repository"
  repository_type = "HOSTED"
}

#############################################################################

resource "oci_devops_build_pipeline" "starter_devops_pipeline" {
  #Required
  project_id = oci_devops_project.starter_devops_project.id

  description  = "Build pipeline"
  display_name = "build-pipeline"

  build_pipeline_parameters {
    items {
      default_value = var.compartment_ocid
      description   = ""
      name          = "TF_VAR_compartment_ocid"
    }
    items {
      default_value = local.par_request_url
      description   = ""
      name          = "TF_VAR_terraform_state_url"
    }
  }
}

#############################################################################

resource "oci_devops_build_pipeline_stage" "starter_devops_build_function" {
  #Required
  build_pipeline_id = oci_devops_build_pipeline.starter_devops_pipeline.id
  build_pipeline_stage_predecessor_collection {
    #Required
    items {
      #Required
      id = oci_devops_build_pipeline.starter_devops_pipeline.id
    }
  }
  build_pipeline_stage_type = "BUILD"
  
  #Optional
  build_source_collection {
    #Optional
    items {
      #Required
      connection_type = "DEVOPS_CODE_REPOSITORY"

      #Optional
      branch = "main"
      # connection_id  = oci_devops_connection.test_connection.id
      name           = "build"
      repository_id  = oci_devops_repository.starter_devops_repository.id
      repository_url = "https://devops.scmservice.${var.region}.oci.oraclecloud.com/namespaces/${local.ocir_namespace}/projects/${oci_devops_project.starter_devops_project.name}/repositories/${oci_devops_repository.starter_devops_repository.name}"
    }
  }
  build_spec_file                    = "build_devops.yaml"
  description                        = "Build using build_all.sh"
  display_name                       = "Build using build_all.sh"
  image                              = "OL7_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = "36000"
  wait_criteria {
    #Required
    wait_duration = "waitDuration"
    wait_type     = "ABSOLUTE_WAIT"
  }
}

#############################################################################
/*
resource "null_resource" "sleep_before_build" {
  depends_on = [ oci_devops_build_pipeline_stage.build_other ]
  provisioner "local-exec" {
    command = "sleep 60"
  }
}

resource "oci_devops_build_run" "test_build_run_1" {
  depends_on = [null_resource.sleep_before_build]
  #Required
  build_pipeline_id = oci_devops_build_pipeline.test_build_pipeline.id
  #Optional
  display_name = "build-run-${random_id.tag.hex}"
}
*/
#############################################################################

locals {
  # OCI DevOps GIT login is tenancy/username
  encoded_oci_username = urlencode("${data.oci_identity_tenancy.tenant_details.name}/${var.username}")
  encoded_auth_token  = urlencode(var.auth_token)
  local_devops_git_url = "https://${local.encoded_oci_username}:${local.encoded_auth_token}@devops.scmservice.${var.region}.oci.oraclecloud.com/namespaces/${local.ocir_namespace}/projects/${oci_devops_project.starter_devops_project.name}/repositories/${oci_devops_repository.starter_devops_repository.name}"
}

output "devops_git_url" {
  value=local.local_devops_git_url
}