locals {
  region_key = lower([for s in data.oci_identity_region_subscriptions.oci_region_subscriptions.region_subscriptions : s if s.region_name == var.region][0].region_key)
  namespace = data.oci_artifacts_container_configuration.ocir_config.namespace
  base_repo_path = "repos/${var.gitops_agent}"
}