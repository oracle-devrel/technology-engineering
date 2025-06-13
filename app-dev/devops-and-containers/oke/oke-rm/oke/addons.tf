# Add on section, you can also manage addons through Terraform
# To find out add-ons available and configurations, run: oci ce addon-option list --kubernetes-version <OKE_VERSION > addons.json
# See also https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringclusteraddons-configurationarguments.htm

locals {

  # SET THIS TO TRUE IF YOU WANT TO OVERRIDE THE COREDNS PLUGIN AND MANAGE IT THROUGH TERRAFORM
  # REQUIRES AT LEAST 1 NODE IN THE CLUSTER. THAT NODE MUST BE FROM THE SYSTEM NODE POOL IF CLUSTER AUTOSCALER IS ENABLED!
  override_coredns = false

  coredns_addon_configs_base = {
    # Distribute replicas on nodes belonging to different ADs, if possible
    topologySpreadConstraints = jsonencode(
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
    )
    # Try to spread CoreDNS pods across different nodes
    affinity = jsonencode(
      yamldecode(
        <<-YAML
          podAntiAffinity:
            preferredDuringSchedulingIgnoredDuringExecution:
              - podAffinityTerm:
                  labelSelector:
                    matchLabels:
                      k8s-app: "kube-dns"
                  topologyKey: "kubernetes.io/hostname"
                weight: 100
          YAML
      )
    )
    # Rolling update configurations for CoreDNS
    rollingUpdate = "{\"maxSurge\": \"50%\", \"maxUnavailable\":\"25%\"}"
    # For large clusters, it's better to increase this value. The default behaviour is to create a new CoreDNS for every new node. Also, resources for single CoreDNS pods should be increased
    nodesPerReplica = "1"
    # In case you need to customize the coredns ConfigMap in kube-system
    customizeCoreDNSConfigMap = "false"
  }

  # COREDNS MUST be scheduled to the system node pool in case cluster autoscaler is enabled
  coredns_addon_configs = merge(local.coredns_addon_configs_base, local.enable_cluster_autoscaler ? {
    nodeSelectors = "{\"role\": \"system\"}"
  } : null)

  metrics_server_addon_configs_base = {
    # At least 3 replicas for high availability
    numOfReplicas = "3"
    # Spread the replicas across ADs if possible
    topologySpreadConstraints = jsonencode(
      yamldecode(
        <<-YAML
          - maxSkew: "1"
            topologyKey: topology.kubernetes.io/zone
            whenUnsatisfiable: ScheduleAnyway
            labelSelector:
              matchLabels:
                k8s-app: metrics-server
          YAML
      )
    )
  }

  # METRICS-SERVER MUST be scheduled to the system node pool in case cluster autoscaler is enabled
  metrics_server_addon_configs = merge(local.metrics_server_addon_configs_base, local.enable_cluster_autoscaler ? {
    nodeSelectors = "{\"role\": \"system\"}"
  } : null)

  cluster_autoscaler_addon_configs = {
    authType = "workload"
    # Enable balancing of similar node groups
    balanceSimilarNodeGroups = "true"
    # We should never group by fault domain when balancing for similarity, only by AD
    balancingIgnoreLabel = "oci.oraclecloud.com/fault-domain"
    # Supported from OKE v1.30.10, autoscale based on freeform or defined tags in the node pools
    # DEFINE HERE YOUR AUTOSCALER POLICY, DEFAULT IS MIN: 0, MAX: 5
    nodeGroupAutoDiscovery = "compartmentId:${var.oke_compartment_id},nodepoolTags:cluster_autoscaler=enabled,min:0,max:5"
    # Make sure to schedule the cluster autoscaler in a node that it is NOT autoscaled, in the system node pool
    nodeSelectors = "{\"role\": \"system\"}"
  }
}


resource "oci_containerengine_addon" "oke_cert_manager" {
  addon_name                       = "CertManager"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  depends_on = [module.oke]
  count = local.enable_cert_manager ? 1 : 0
}

resource "oci_containerengine_addon" "oke_metrics_server" {
  addon_name                       = "KubernetesMetricsServer"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  dynamic "configurations" {
    for_each = local.metrics_server_addon_configs
    content {
      key = configurations.key
      value = configurations.value
    }
  }
  depends_on = [module.oke, oci_containerengine_addon.oke_cert_manager]
  count = local.enable_metrics_server ? 1 : 0
}

resource "oci_containerengine_addon" "oke_coredns" {
  addon_name                       = "CoreDNS"
  cluster_id                       = module.oke.cluster_id
  remove_addon_resources_on_delete = false
  override_existing = true
  dynamic "configurations" {
    for_each = local.coredns_addon_configs
    content {
      key = configurations.key
      value = configurations.value
    }
  }
  depends_on = [module.oke]
  count = var.cluster_type == "enhanced" && local.override_coredns ? 1 : 0
}

resource "oci_containerengine_addon" "oke_cluster_autoscaler" {
  addon_name = "ClusterAutoscaler"
  cluster_id = module.oke.cluster_id
  remove_addon_resources_on_delete = true
  dynamic "configurations" {
    for_each = local.cluster_autoscaler_addon_configs
    content {
      key = configurations.key
      value = configurations.value
    }
  }
  depends_on = [module.oke]
  count = local.enable_cluster_autoscaler ? 1 : 0
}