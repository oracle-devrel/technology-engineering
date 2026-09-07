resource "oci_devops_project_repository_setting" "project" {
  project_id = oci_devops_project.devops_project.id

  merge_settings {
    allowed_merge_strategies = [
      "MERGE_COMMIT",
      "SQUASH",
      "SQUASH_FAST_FORWARD_ONLY",
    ]
    default_merge_strategy = "SQUASH"
  }

  lifecycle {
    # OCI normalizes merge settings after creation; preserve the adopted settings.
    ignore_changes = all
  }
}

resource "oci_devops_repository_setting" "repositories" {
  for_each = merge(
    {
      pipelines = oci_devops_repository.platform_pipelines.id
    },
    { for key, repo in oci_devops_repository.cluster_admin : "cluster-admin" => repo.id },
    { for name, repo in oci_devops_repository.application_chart : "chart:${name}" => repo.id },
    { for name, repo in oci_devops_repository.application_source : "source:${name}" => repo.id }
  )

  repository_id = each.value

  merge_settings {
    allowed_merge_strategies = [
      "MERGE_COMMIT",
      "SQUASH",
      "SQUASH_FAST_FORWARD_ONLY",
    ]
    default_merge_strategy = "SQUASH"
  }

  lifecycle {
    # OCI normalizes merge settings after creation; preserve the adopted settings.
    ignore_changes = all
  }
}
