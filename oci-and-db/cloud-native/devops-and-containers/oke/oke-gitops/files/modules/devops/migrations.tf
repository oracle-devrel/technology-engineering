moved {
  from = oci_devops_project.devops_project
  to   = oci_devops_project.devops_project[0]
}

moved {
  from = oci_logging_log_group.devops_log_group
  to   = oci_logging_log_group.devops_log_group[0]
}

moved {
  from = oci_logging_log.devops_log
  to   = oci_logging_log.devops_log[0]
}
