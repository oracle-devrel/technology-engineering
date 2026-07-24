resource "oci_devops_deploy_pipeline" "cluster_admin" {
  for_each = local.cluster_admin_clusters

  project_id   = oci_devops_project.devops_project.id
  display_name = "cluster-admin-${each.key}"
  description  = "Applies the cluster baseline and Kubernetes tool DAG to the ${each.key} OKE cluster"
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "cluster-pipeline"
  })

  deploy_pipeline_parameters {
    items {
      name          = "config_commit"
      default_value = ""
      description   = "Exact cluster-admin Git commit containing baseline and supplemental resources"
    }

    items {
      name          = "cluster_id"
      default_value = each.value.cluster_id
      description   = "OKE cluster OCID used by shell deployment stages"
    }

    items {
      name          = "cluster_name"
      default_value = each.key
      description   = "Cluster configuration directory name"
    }

  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_pipeline" "cluster_admin_decommission" {
  for_each = local.cluster_admin_clusters

  project_id   = oci_devops_project.devops_project.id
  display_name = "cluster-admin-${each.key}-decommission"
  description  = "Manually uninstalls one cluster tool from the ${each.key} OKE cluster"
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "decommission-pipeline"
  })

  deploy_pipeline_parameters {
    items {
      name          = "tool_name"
      default_value = ""
      description   = "Tool and Helm release name to remove"
    }
    items {
      name          = "tool_namespace"
      default_value = ""
      description   = "Namespace containing the tool release and supplemental resources"
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "cluster_admin_approval" {
  for_each = local.cluster_admin_approval_clusters

  approval_policy {
    approval_policy_type         = "COUNT_BASED_APPROVAL"
    number_of_approvals_required = 1
  }

  deploy_pipeline_id = oci_devops_deploy_pipeline.cluster_admin[each.key].id
  deploy_stage_type  = "MANUAL_APPROVAL"
  description        = "Approve cluster administration changes for the ${each.key} OKE cluster"
  display_name       = "Approve ${title(each.key)} Cluster Changes"
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "approval"
  })

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.cluster_admin[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "cluster_admin_orchestrator" {
  for_each = local.cluster_admin_clusters

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.cluster_admin_deploy_command["enabled"].id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.cluster_admin[each.key].id
  deploy_stage_type               = "SHELL"
  description                     = "Deploy the selected cluster administration change plan to ${each.key}"
  display_name                    = "Deploy ${title(each.key)} Cluster Changes"
  timeout_in_seconds              = 10000
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "cluster-orchestrator"
  })

  container_config {
    container_config_type = "CONTAINER_INSTANCE_CONFIG"
    compartment_id        = var.compartment_id
    shape_name            = "CI.Standard.E4.Flex"

    shape_config {
      ocpus         = 1
      memory_in_gbs = 2
    }

    network_channel {
      network_channel_type = "SERVICE_VNIC_CHANNEL"
      subnet_id            = each.value.subnet_id
      nsg_ids              = each.value.nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    dynamic "items" {
      for_each = each.value.approval_required ? [1] : []
      content {
        id = oci_devops_deploy_stage.cluster_admin_approval[each.key].id
      }
    }

    dynamic "items" {
      for_each = each.value.approval_required ? [] : [1]
      content {
        id = oci_devops_deploy_pipeline.cluster_admin[each.key].id
      }
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "cluster_admin_decommission_approval" {
  for_each = local.cluster_admin_approval_clusters

  approval_policy {
    approval_policy_type         = "COUNT_BASED_APPROVAL"
    number_of_approvals_required = 1
  }

  deploy_pipeline_id = oci_devops_deploy_pipeline.cluster_admin_decommission[each.key].id
  deploy_stage_type  = "MANUAL_APPROVAL"
  description        = "Approve explicit removal of a tool from the ${each.key} OKE cluster"
  display_name       = "Approve ${title(each.key)} Tool Decommission"
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "decommission-approval"
  })

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.cluster_admin_decommission[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "cluster_admin_decommission" {
  for_each = local.cluster_admin_clusters

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.cluster_admin_decommission_command["enabled"].id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.cluster_admin_decommission[each.key].id
  deploy_stage_type               = "SHELL"
  description                     = "Delete supplemental resources and uninstall one Helm release from ${each.key}"
  display_name                    = "Decommission ${title(each.key)} Tool"
  timeout_in_seconds              = 1200
  freeform_tags = merge(local.cluster_admin_tags, {
    cluster = each.key
    role    = "decommission"
  })

  container_config {
    container_config_type = "CONTAINER_INSTANCE_CONFIG"
    compartment_id        = var.compartment_id
    shape_name            = "CI.Standard.E4.Flex"

    shape_config {
      ocpus         = 1
      memory_in_gbs = 2
    }

    network_channel {
      network_channel_type = "SERVICE_VNIC_CHANNEL"
      subnet_id            = each.value.subnet_id
      nsg_ids              = each.value.nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    dynamic "items" {
      for_each = each.value.approval_required ? [1] : []
      content {
        id = oci_devops_deploy_stage.cluster_admin_decommission_approval[each.key].id
      }
    }

    dynamic "items" {
      for_each = each.value.approval_required ? [] : [1]
      content {
        id = oci_devops_deploy_pipeline.cluster_admin_decommission[each.key].id
      }
    }
  }

  lifecycle {
    ignore_changes = all
  }
}
