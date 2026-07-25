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
