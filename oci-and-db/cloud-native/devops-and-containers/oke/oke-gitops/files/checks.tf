check "existing_devops_project" {
  assert {
    condition = var.create_devops_project || can(regex(
      "^ocid1\\.devopsproject\\.[^.]+\\.[^.]*\\.[^.]+$",
      trimspace(var.existing_devops_project_id)
    ))
    error_message = "existing_devops_project_id must be a valid OCI DevOps project OCID when create_devops_project is false."
  }
}
