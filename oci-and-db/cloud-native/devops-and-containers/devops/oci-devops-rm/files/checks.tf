check "recommended_application_scale" {
  assert {
    condition     = local.application_count <= 20
    error_message = "This starter stack is optimized for at most 20 applications in one OCI DevOps project. The apply will continue, but review OCI DevOps service limits and consider splitting projects."
  }

  assert {
    condition     = local.component_count <= 50
    error_message = "This starter stack is optimized for at most 50 components in one OCI DevOps project. The apply will continue, but review repository, pipeline, and artifact service limits."
  }
}

check "conditional_inputs" {
  assert {
    condition = var.create_devops_project || can(regex(
      "^ocid1\\.devopsproject\\.",
      trimspace(coalesce(var.existing_devops_project_id, ""))
    ))
    error_message = "existing_devops_project_id must be a valid OCI DevOps project OCID when create_devops_project is false."
  }

  assert {
    condition = (var.application_delivery_mode == "build_only" && !var.enable_cluster_admin) || alltrue([
      for value in [
        var.oke_compartment_id,
        var.oke_cluster_id,
        var.prod_oke_cluster_id,
        var.prod_oke_compartment_id,
        var.network_compartment_id,
        var.prod_network_compartment_id,
        var.oke_vcn_id,
        var.prod_oke_vcn_id,
        var.oke_worker_subnet_id,
        var.prod_oke_worker_subnet_id,
      ] : try(trimspace(value), "") != ""
    ])
    error_message = "Both pre-production and production OKE cluster, compartment, VCN, and worker subnet inputs are required for OCI DevOps delivery or cluster administration."
  }
}

check "repository_names_are_unique" {
  assert {
    condition = can(jsondecode(var.applications)) ? length(distinct(concat(
      [lower(var.devops_pipeline_repository_name), "cluster-admin"],
      [for application in jsondecode(var.applications) : try(application.chart_repository_name, "${application.name}-chart")],
      flatten([for application in jsondecode(var.applications) : [for component in application.components : component.name]])
      ))) == length(concat(
      [lower(var.devops_pipeline_repository_name), "cluster-admin"],
      [for application in jsondecode(var.applications) : try(application.chart_repository_name, "${application.name}-chart")],
      flatten([for application in jsondecode(var.applications) : [for component in application.components : component.name]])
    )) : true
    error_message = "Derived repository names must be unique and cannot collide with the configured DevOps pipelines or cluster-admin repositories."
  }
}
