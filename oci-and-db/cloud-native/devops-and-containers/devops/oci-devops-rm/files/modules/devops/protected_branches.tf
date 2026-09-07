resource "oci_devops_repository_protected_branch_management" "application_source_main" {
  for_each = local.components_by_name

  repository_id = oci_devops_repository.application_source[each.key].id
  branch_name   = "main"

  protection_levels = [
    "PULL_REQUEST_MERGE_ONLY",
  ]

  depends_on = [
    null_resource.seed_application_source
  ]

  lifecycle {
    # Provider normalization otherwise replaces branch protection on every plan.
    ignore_changes = all
  }
}

resource "oci_devops_repository_protected_branch_management" "application_chart_main" {
  for_each = local.applications_by_name

  repository_id = oci_devops_repository.application_chart[each.key].id
  branch_name   = "main"

  protection_levels = [
    "PULL_REQUEST_MERGE_ONLY",
  ]

  depends_on = [
    null_resource.seed_application_chart_components
  ]

  lifecycle {
    # Provider normalization otherwise replaces branch protection on every plan.
    ignore_changes = all
  }
}

resource "oci_devops_repository_protected_branch_management" "cluster_admin_main" {
  for_each = local.cluster_admin_singleton

  repository_id = oci_devops_repository.cluster_admin[each.key].id
  branch_name   = "main"

  protection_levels = [
    "PULL_REQUEST_MERGE_ONLY",
  ]

  depends_on = [null_resource.seed_cluster_admin_entities]

  lifecycle {
    # Provider normalization otherwise replaces branch protection on every plan.
    ignore_changes = all
  }
}
