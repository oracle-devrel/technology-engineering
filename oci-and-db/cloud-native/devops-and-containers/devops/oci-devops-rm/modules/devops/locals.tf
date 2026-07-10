locals {
  region_key = lower([for s in data.oci_identity_region_subscriptions.region_subscriptions.region_subscriptions : s if s.region_name == var.region][0].region_key)
  namespace  = data.oci_artifacts_container_configuration.ocir_config.namespace

  platform_repo_path  = "repos/pipelines"
  project_repo_prefix = replace(lower(var.devops_project_name), "/[^a-z0-9._-]+/", "-")

  applications_by_name = {
    for application in var.applications : application.name => {
      name                  = application.name
      chart_repository_name = coalesce(application.chart_repository_name, "${application.name}-chart")
      chart_path            = coalesce(application.chart_path, application.name)
      chart_version         = application.chart_version
      namespace             = coalesce(application.namespace, application.name)
      prod_namespace        = coalesce(application.prod_namespace, coalesce(application.namespace, application.name))
      kubernetes_group      = application.kubernetes_group
      repo_path             = "repos/generated/charts/${application.name}"
      chart_repo_prefix     = "${local.project_repo_prefix}/charts"
      ocir_chart            = "oci://${local.region_key}.ocir.io/${local.namespace}/${local.project_repo_prefix}/charts/${application.name}"
      components            = application.components
    }
  }

  components_by_name = merge([
    for application in var.applications : {
      for component in application.components : component.name => {
        name                       = component.name
        application_name           = application.name
        application_namespace      = coalesce(application.namespace, application.name)
        application_prod_namespace = coalesce(application.prod_namespace, coalesce(application.namespace, application.name))
        application_chart_path     = coalesce(application.chart_path, application.name)
        chart_version              = component.chart_version
        build_spec_path            = coalesce(component.build_spec_path, "${component.name}-build-pipeline.yaml")
        generate_build_spec        = component.build_spec_path == null
        repo_path                  = "repos/generated/components/${component.name}"
        chart_path                 = "${coalesce(application.chart_path, application.name)}/charts/${component.name}"
        chart_repo_prefix          = "${local.project_repo_prefix}/charts/${application.name}"
        image_repo_prefix          = "${local.project_repo_prefix}/${application.name}/${component.name}"
        ocir_chart                 = "oci://${local.region_key}.ocir.io/${local.namespace}/${local.project_repo_prefix}/charts/${application.name}/${component.name}"
        image_repository           = "${local.region_key}.ocir.io/${local.namespace}/${local.project_repo_prefix}/${application.name}/${component.name}"
      }
    }
  ]...)

  generated_component_build_specs = {
    for name, component in local.components_by_name : name => component if component.generate_build_spec
  }

  custom_build_spec_paths = distinct([
    for component in values(local.components_by_name) : component.build_spec_path
    if !component.generate_build_spec
  ])

  custom_build_specs_by_path = {
    for path in local.custom_build_spec_paths : path => {
      component = local.components_by_name[sort([
        for name, component in local.components_by_name : name
        if !component.generate_build_spec && component.build_spec_path == path
      ])[0]]
      component_names = sort([
        for name, component in local.components_by_name : name
        if !component.generate_build_spec && component.build_spec_path == path
      ])
    }
  }

  component_environment_pairs = merge([
    for component_name, component in local.components_by_name : {
      for environment in ["dev", "staging"] : "${component_name}:${environment}" => merge(component, {
        environment = environment
      })
    }
  ]...)

  application_bootstrap_targets = merge([
    for application_name, application in local.applications_by_name : {
      "${application_name}:noprod" = {
        application_name = application_name
        cluster_name     = "noprod"
        namespace        = application.namespace
        subnet_id        = var.oke_worker_subnet_id
        nsg_ids          = local.oke_worker_nsg_ids
      }
      "${application_name}:prod" = {
        application_name = application_name
        cluster_name     = "prod"
        namespace        = application.prod_namespace
        subnet_id        = local.prod_oke_worker_subnet_id
        nsg_ids          = local.prod_oke_worker_nsg_ids
      }
    }
  ]...)

  default_application_environment = "dev"
  baseline_cluster_name           = "noprod"
  kube_endpoint                   = "PRIVATE_ENDPOINT"

  prod_oke_cluster_id       = var.prod_oke_cluster_id
  prod_oke_worker_subnet_id = var.prod_oke_worker_subnet_id
  prod_oke_worker_nsg_id    = var.prod_oke_worker_nsg_id
  oke_worker_nsg_ids        = try(trimspace(var.oke_worker_nsg_id), "") == "" ? [] : [var.oke_worker_nsg_id]
  prod_oke_worker_nsg_ids   = try(trimspace(local.prod_oke_worker_nsg_id), "") == "" ? [] : [local.prod_oke_worker_nsg_id]

  oke_environment_id      = oci_devops_deploy_environment.oke_environment.id
  prod_oke_environment_id = oci_devops_deploy_environment.prod_oke_environment.id

  cluster_admin_repo_path = "repos/generated/cluster-admin"
  cluster_admin_singleton = var.enable_cluster_admin ? { enabled = true } : {}
  cluster_admin_tags = {
    owner   = "cluster-administrators"
    purpose = "cluster-administration"
    scope   = "operations"
  }
  # A shared topology keeps both physical-cluster pipelines structurally identical.
  # The nested noprod list is retained as a fallback for existing stack inputs.
  cluster_admin_tools = var.enable_cluster_admin ? coalesce(
    try(var.cluster_administration.tools, null),
    try(var.cluster_administration.noprod.tools, null),
    []
  ) : []
  cluster_admin_clusters = var.enable_cluster_admin ? {
    noprod = {
      name              = "noprod"
      approval_required = false
      cluster_id        = var.oke_cluster_id
      environment_id    = local.oke_environment_id
      subnet_id         = var.oke_worker_subnet_id
      nsg_ids           = local.oke_worker_nsg_ids
      tools             = local.cluster_admin_tools
    }
    prod = {
      name              = "prod"
      approval_required = true
      cluster_id        = local.prod_oke_cluster_id
      environment_id    = local.prod_oke_environment_id
      subnet_id         = local.prod_oke_worker_subnet_id
      nsg_ids           = local.prod_oke_worker_nsg_ids
      tools             = local.cluster_admin_tools
    }
  } : {}

  cluster_admin_tool_pairs = merge([
    for cluster_name, cluster in local.cluster_admin_clusters : {
      for tool in cluster.tools : "${cluster_name}:${tool.name}" => {
        cluster_name      = cluster_name
        tool_name         = tool.name
        namespace         = coalesce(tool.namespace, tool.name)
        dependencies      = try(tool.depends_on, [])
        approval_required = cluster.approval_required
        cluster_id        = cluster.cluster_id
        environment_id    = cluster.environment_id
        subnet_id         = cluster.subnet_id
        nsg_ids           = cluster.nsg_ids
        values_path       = "cluster-admin/${cluster_name}/tools/${tool.name}/values.yaml"
      }
    }
  ]...)

  cluster_admin_approval_clusters = {
    for name, cluster in local.cluster_admin_clusters : name => cluster if cluster.approval_required
  }

}
