resource "oci_devops_build_pipeline" "cluster_admin_build" {
  for_each = local.cluster_admin_singleton

  project_id   = oci_devops_project.devops_project.id
  display_name = "cluster-admin-build"
  description  = "Validates changed cluster configuration, publishes immutable plans and values, and dispatches cluster orchestrators"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "cluster_admin_build" {
  for_each = local.cluster_admin_singleton

  build_pipeline_id                  = oci_devops_build_pipeline.cluster_admin_build[each.key].id
  build_pipeline_stage_type          = "BUILD"
  display_name                       = "Cluster Admin Build"
  description                        = "Validates and dispatches changed cluster administration stages in dependency waves"
  build_spec_file                    = ".oci-devops/build-pipeline.yaml"
  primary_build_source               = "cluster-admin"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "configuration-dispatch"
  })

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.cluster_admin_build[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "cluster-admin"
      repository_id   = oci_devops_repository.cluster_admin[each.key].id
      repository_url  = oci_devops_repository.cluster_admin[each.key].http_url
    }
  }

  depends_on = [null_resource.seed_cluster_admin_entities]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline" "cluster_admin_mirror" {
  for_each = local.cluster_admin_singleton

  project_id   = oci_devops_project.devops_project.id
  display_name = "cluster-admin-mirror-charts"
  description  = "Mirrors all missing public Kubernetes tool chart versions from the cluster-admin catalog into OCIR"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "cluster_admin_mirror" {
  for_each = local.cluster_admin_singleton

  build_pipeline_id                  = oci_devops_build_pipeline.cluster_admin_mirror[each.key].id
  build_pipeline_stage_type          = "BUILD"
  display_name                       = "Mirror Cluster Tool Charts"
  description                        = "Mirrors missing pinned public Helm charts into OCIR"
  build_spec_file                    = ".oci-devops/mirror-charts-pipeline.yaml"
  primary_build_source               = "cluster-admin"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "chart-mirror"
  })

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.cluster_admin_mirror[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "cluster-admin"
      repository_id   = oci_devops_repository.cluster_admin[each.key].id
      repository_url  = oci_devops_repository.cluster_admin[each.key].http_url
    }
  }

  depends_on = [null_resource.seed_cluster_admin_entities]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline" "cluster_admin_pr" {
  for_each = local.cluster_admin_singleton

  project_id   = oci_devops_project.devops_project.id
  display_name = "cluster-admin-pr"
  description  = "Validates cluster administration pull requests without accessing an OKE cluster"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "cluster_admin_pr" {
  for_each = local.cluster_admin_singleton

  build_pipeline_id                  = oci_devops_build_pipeline.cluster_admin_pr[each.key].id
  build_pipeline_stage_type          = "BUILD"
  display_name                       = "Cluster Admin Pull Request"
  description                        = "Validates the cluster tool catalog and per-cluster configuration"
  build_spec_file                    = ".oci-devops/pull-request-pipeline.yaml"
  primary_build_source               = "cluster-admin"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "pull-request-validation"
  })

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.cluster_admin_pr[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "cluster-admin"
      repository_id   = oci_devops_repository.cluster_admin[each.key].id
      repository_url  = oci_devops_repository.cluster_admin[each.key].http_url
    }
  }

  depends_on = [null_resource.seed_cluster_admin_entities]

  lifecycle {
    ignore_changes = all
  }
}
