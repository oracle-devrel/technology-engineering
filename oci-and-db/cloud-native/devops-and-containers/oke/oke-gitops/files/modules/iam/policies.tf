locals {
  build_principal     = "dynamic-group id ${oci_identity_domains_dynamic_resource_group.devOpsDynamicGroup.ocid}"
  bootstrap_principal = "dynamic-group id ${oci_identity_domains_dynamic_resource_group.bootstrap.ocid}"
  deploy_principal    = "dynamic-group id ${oci_identity_domains_dynamic_resource_group.deployment.ocid}"
  project_scope       = "in compartment id ${var.compartment_id} where target.project.id = '${var.project_id}'"
  registry_scope      = "in compartment id ${var.compartment_id} where target.repo.name = /${replace(var.ocir_repo_path_prefix, "/", "\\/")}\\/*/"

  build_statements = [
    "Allow ${local.build_principal} to read devops-project ${local.project_scope}",
    "Allow ${local.build_principal} to read devops-repository in compartment id ${var.compartment_id} where target.repository.id = '${var.pipelines_repository_id}'",
    # ListContainerRepositories and GetContainerConfiguration have no target.repo.name.
    "Allow ${local.build_principal} to inspect repos in compartment id ${var.compartment_id}",
    "Allow ${local.build_principal} to manage repos in compartment id ${var.compartment_id} where all {target.repo.name = /${replace(var.ocir_repo_path_prefix, "/", "\\/")}\\/*/, any {request.permission = 'REPOSITORY_READ', request.permission = 'REPOSITORY_CREATE', request.permission = 'REPOSITORY_UPDATE'}}"
  ]

  bootstrap_statements = [
    "Allow ${local.bootstrap_principal} to manage devops-family in compartment id ${var.compartment_id}"
  ]

  deploy_statements = [
    "Allow ${local.deploy_principal} to manage devops-family in compartment id ${var.compartment_id}",
    "Allow ${local.deploy_principal} to read repos ${local.registry_scope}",
    # CLUSTER_MANAGE is necessary for AdministerK8s, but not cluster CRUD.
    "Allow ${local.deploy_principal} to manage clusters in compartment id ${var.oke_compartment_id} where all {target.cluster.id = '${var.oke_cluster_id}', any {request.permission = 'CLUSTER_READ', request.permission = 'CLUSTER_USE', request.permission = 'CLUSTER_MANAGE'}}",
    "Allow ${local.deploy_principal} to manage compute-container-instances in compartment id ${var.compartment_id} where any {request.permission = 'COMPUTE_CONTAINER_INSTANCE_INSPECT', request.permission = 'COMPUTE_CONTAINER_INSTANCE_READ', request.permission = 'COMPUTE_CONTAINER_INSTANCE_CREATE', request.permission = 'COMPUTE_CONTAINER_INSTANCE_DELETE'}",
    "Allow ${local.deploy_principal} to manage compute-containers in compartment id ${var.compartment_id} where any {request.permission = 'COMPUTE_CONTAINER_INSPECT', request.permission = 'COMPUTE_CONTAINER_READ', request.permission = 'COMPUTE_CONTAINER_CREATE', request.permission = 'COMPUTE_CONTAINER_DELETE', request.permission = 'COMPUTE_CONTAINER_LOG_RETRIEVE'}"
  ]

  network_statements = concat([
    "Allow ${local.deploy_principal} to use subnets in compartment id ${var.network_compartment_id}",
    "Allow ${local.deploy_principal} to use vnics in compartment id ${var.network_compartment_id}",
    "Allow ${local.deploy_principal} to inspect dhcp-options in compartment id ${var.network_compartment_id}"
    ], var.use_network_security_groups ? [
    "Allow ${local.deploy_principal} to use network-security-groups in compartment id ${var.network_compartment_id}"
  ] : [])

  secret_statements = length(var.secret_ids) == 0 ? [] : [
    "Allow ${local.deploy_principal} to read secret-bundles in compartment id ${var.compartment_id} where any {${join(", ", [for id in var.secret_ids : "target.secret.id = '${id}'"])}}"
  ]
  statements = concat(local.build_statements, local.bootstrap_statements, local.deploy_statements, local.network_statements, local.secret_statements)
}



resource "oci_identity_policy" "devops_policy" {
  compartment_id = var.policy_compartment_id
  description    = "GitOps build and installation execution permissions"
  name           = var.devops_policy_name
  statements     = local.statements
}
