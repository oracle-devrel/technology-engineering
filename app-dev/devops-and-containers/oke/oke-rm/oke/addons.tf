# Add on section, you can also manage addons through Terraform
# To find out add-ons available and configurations, run: oci ce addon-option list --kubernetes-version <OKE_VERSION > addons.json
# See also https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringclusteraddons-configurationarguments.htm

locals {
  # SET THIS TO TRUE IF YOU WANT TO OVERRIDE THE COREDNS PLUGIN AND MANAGE IT THROUGH TERRAFORM
  # It requires at least 1 node in the cluster where CoreDNS can be scheduled
  override_coredns = true

  coredns_addon_configs = {
    # Distribute replicas on nodes belonging to different ADs, if possible
    /*    topologySpreadConstraints = jsonencode(
      yamldecode(
        <<-YAML
          - maxSkew: "1"
            topologyKey: topology.kubernetes.io/zone
            whenUnsatisfiable: ScheduleAnyway
            labelSelector:
              matchLabels:
                k8s-app: kube-dns
          YAML
      )
    )*/
    # Try to spread CoreDNS pods across different nodes
    affinity = jsonencode(
      yamldecode(
        <<-YAML
          nodeAffinity:
            preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                - key: node-role/system
                  operator: In
                  values:
                  - "true"
          podAntiAffinity:
            preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    k8s-app: kube-dns
                topologyKey: kubernetes.io/hostname
            - weight: 80
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    k8s-app: kube-dns
                topologyKey: topology.kubernetes.io/zone
            - weight: 50
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    k8s-app: kube-dns
                topologyKey: oci.oraclecloud.com/fault-domain
          YAML
      )
    )

    # For large clusters, it's better to increase this value. The default behaviour is to create a new CoreDNS for every new node. Also, resources for single CoreDNS pods should be increased
    nodesPerReplica = "1"
    # In case you need to customize the coredns ConfigMap in kube-system
    customizeCoreDNSConfigMap = "false"

    tolerations = "[{\"key\":\"CriticalAddonsOnly\", \"operator\":\"Exists\"}]"
  }

  metrics_server_addon_configs = {
    numOfReplicas = "2"
  }
}


resource "oci_containerengine_addon" "oke_cert_manager" {
  addon_name                       = "CertManager"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  depends_on                       = [module.oke]
  count                            = local.enable_cert_manager ? 1 : 0
}

resource "oci_containerengine_addon" "oke_metrics_server" {
  addon_name                       = "KubernetesMetricsServer"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  dynamic "configurations" {
    for_each = local.metrics_server_addon_configs
    content {
      key   = configurations.key
      value = configurations.value
    }
  }
  depends_on = [module.oke, oci_containerengine_addon.oke_cert_manager]
  count      = local.enable_metrics_server ? 1 : 0
}

resource "oci_containerengine_addon" "oke_coredns" {
  addon_name                       = "CoreDNS"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = false
  override_existing                = true
  dynamic "configurations" {
    for_each = local.coredns_addon_configs
    content {
      key   = configurations.key
      value = configurations.value
    }
  }
  depends_on = [module.oke]
  count      = var.cluster_type == "enhanced" && local.override_coredns ? 1 : 0
}

resource "oci_containerengine_addon" "oke_nodeProblemDetector" {
  addon_name                       = "NodeProblemDetector"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  override_existing                = true
  configurations {
    key   = "enableKubernetesExporter"
    value = "true"
  }
  depends_on = [module.oke]
  count      = var.cluster_type == "enhanced" ? 1 : 0
}