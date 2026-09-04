resource "oci_devops_deploy_artifact" "cluster_admin_deploy_command" {
  for_each = local.cluster_admin_singleton

  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Deploys a validated cluster-tool change plan"
  display_name               = "cluster-admin-deploy-command-spec"
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "deploy-command"
  })
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/cluster-admin-deploy-command-spec.yaml.tpl", {
      artifact_repository_id = oci_artifacts_repository.cluster_admin_values[each.key].id
      chart_prefix           = "${local.project_repo_prefix}/charts/cluster-tools"
      kube_endpoint          = local.kube_endpoint
      region                 = var.region
      registry               = "${local.region_key}.ocir.io"
      repository_id          = oci_devops_repository.cluster_admin[each.key].id
      tenancy_namespace      = local.namespace
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "cluster_admin_decommission_command" {
  for_each = local.cluster_admin_singleton

  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Explicitly removes supplemental resources and uninstalls one cluster tool"
  display_name               = "cluster-admin-decommission-command-spec"
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "decommission"
  })
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/cluster-admin-decommission-command-spec.yaml.tpl", {
      kube_endpoint         = local.kube_endpoint
      noprod_oke_cluster_id = var.oke_cluster_id
      prod_oke_cluster_id   = local.prod_oke_cluster_id
      region                = var.region
      repository_id         = oci_devops_repository.cluster_admin[each.key].id
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}
