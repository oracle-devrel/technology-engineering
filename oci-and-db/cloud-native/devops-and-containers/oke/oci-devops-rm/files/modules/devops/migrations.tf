moved {
  from = oci_devops_project.devops_project
  to   = oci_devops_project.devops_project[0]
}

moved {
  from = oci_devops_deploy_environment.oke_environment
  to   = oci_devops_deploy_environment.oke_environment[0]
}

moved {
  from = oci_devops_deploy_environment.prod_oke_environment
  to   = oci_devops_deploy_environment.prod_oke_environment[0]
}

moved {
  from = oci_devops_deploy_artifact.application_bootstrap_command_spec
  to   = oci_devops_deploy_artifact.application_bootstrap_command_spec[0]
}

moved {
  from = oci_devops_deploy_artifact.component_verify_deployment_command_spec
  to   = oci_devops_deploy_artifact.component_verify_deployment_command_spec[0]
}

moved {
  from = oci_devops_deploy_artifact.promote_release_image_command_spec
  to   = oci_devops_deploy_artifact.promote_release_image_command_spec[0]
}

moved {
  from = oci_devops_deploy_artifact.tag_release_commit_command_spec
  to   = oci_devops_deploy_artifact.tag_release_commit_command_spec[0]
}
