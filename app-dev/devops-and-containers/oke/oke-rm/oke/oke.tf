# NOTE: OKE often requires some policies to work with depending on the use case. You can find a complete list at this link:
# https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/oke/oke-policies/policies.md

locals {
  volume_kms_key_id = "" # kms OCID of the key used for in-transit and at-rest encryption of block volumes
  ssh_public_key    = "" # Insert the ssh public key to access worker nodes

  # Cloud init to taint nodes using Oracle Linux nodes. Make sure to disable the default cloud init
  cloud_init_example = {
    runcmd = [
      "echo \"example cloud init\""
    ]
  }

}

module "oke" {
  source         = "oracle-terraform-modules/oke/oci"
  version        = "5.3.3"
  compartment_id = var.oke_compartment_id
  # Network module - VCN
  create_vcn                        = false
  vcn_id                            = var.vcn_id
  network_compartment_id            = var.network_compartment_id
  assign_public_ip_to_control_plane = !local.is_cp_subnet_private
  subnets = {
    bastion  = { create = "never" }
    operator = { create = "never" }
    pub_lb   = { id = local.is_lb_subnet_private ? null : var.lb_subnet_id }
    int_lb   = { id = local.is_lb_subnet_private ? var.lb_subnet_id : null }
    cp       = { id = var.cp_subnet_id }
    workers  = { id = var.worker_subnet_id }
    pods     = { id = local.is_flannel ? null : var.pod_subnet_id }
  }
  nsgs = {
    bastion  = { create = "never" }
    operator = { create = "never" }
    pub_lb   = { create = "never" }
    int_lb   = { create = "never" }
    cp       = { id = var.cp_nsg_id }
    workers  = { id = var.worker_nsg_id }
    pods     = { create = "never", id = var.cni_type == "flannel" ? null : var.pod_nsg_id }
  }
  # Network module - security
  control_plane_allowed_cidrs = var.cp_allowed_cidr_list
  control_plane_is_public     = !local.is_cp_subnet_private
  load_balancers              = local.is_lb_subnet_private ? "internal" : "public"
  preferred_load_balancer     = local.is_lb_subnet_private ? "internal" : "public"
  # Cluster module
  create_cluster     = true
  cluster_kms_key_id = var.cluster_kms_key_id
  cluster_name       = var.cluster_name
  cluster_type       = var.cluster_type
  cni_type           = local.cni
  kubernetes_version = var.kubernetes_version
  services_cidr      = var.services_cidr
  pods_cidr          = var.pods_cidr

  # OIDC
  oidc_discovery_enabled           = local.oidc_discovery_enabled
  oidc_token_auth_enabled          = local.oidc_authentication_enabled
  oidc_token_authentication_config = local.oidc_token_authentication_config

  cluster_freeform_tags = {
    cluster = var.cluster_name
  }

  # Bastion
  create_bastion = false
  # Operator
  create_operator = false

  ########################## OKE DATA PLANE (to configure) ##############################

  # These are global configurations valid for all the node pools declared. You can see that the prefix is "worker_" because they apply to all workers of the cluster
  # You can override these global configurations in the node pool definition, and it will have precedence over the global ones.

  worker_pool_mode = "node-pool" # Default mode should be node-pool for managed nodes, other modes are available for self-managed nodes, like instance and instance-pool, but be careful to have the required policy: https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengdynamicgrouppolicyforselfmanagednodes.htm
  #ssh_public_key = local.ssh_public_key    # De-comment if you want a ssh key to access the worker nodes, be sure to set the local variable
  worker_image_type = "oke" # NOTE: the oke mode will fetch the latest OKE Oracle Linux image released by the OKE team. If you want more control, better to use "custom" and specify the image id. This is because an image id is always fixed, and controlled by you.
  #worker_image_id = ""                     # The image id to use for the worker nodes. For Oracle Linux images, check this link: https://docs.oracle.com/en-us/iaas/images/oke-worker-node-oracle-linux-8x/index.htm
  # For Ubuntu images, you need to create an Ubuntu custom image in your tenancy first, and then set the OCID of the custom image here
  # NOTE: set worker_image_type to "custom" and specify an image id to use custom images for all workers

  # Set this to true to enable in-transit encryption on all node pools by default
  # NOTE: in-transit encryption is supported only for paravirtualized attached block volumes and boot volumes, hence you will need to create another StorageClass in the cluster to attach volume through paravirtualization, as the default oci-bv StorageClass uses iSCSI
  # Also note that Bare Metal instances do not support paravirtualized volumes, the oke module won't enable it on BM shapes, even if you set this to true
  worker_pv_transit_encryption = true

  # Enable encryption of volumes with a key managed by you, in your OCI Vault
  #worker_volume_kms_key_id = local.volume_kms_key_id

  /* ABOUT CLOUD INIT
  The OKE module will automatically generate an optimal cloud-init for both Oracle Linux and Ubuntu nodes. This auto-generated cloud-init is called "default cloud-init".
  There is the possibility to disable this and to define your own cloud-init. This is not suggested unless you know what you are doing.
  For Oracle Linux, the oci-growfs command is already inserted in the default cloud-init.
   */
  #worker_cloud_init = [{ content_type = "text/cloud-config", content = yamlencode(local.cloud_init_example)}]         # Cloud init to add to all node pools. This will be added to the default_cloud_init

  # GLOBAL TAGS TO BE APPLIED ON ALL NODES
  # NOTE: tags will be applied to both the node pool and the nodes
  /*workers_freeform_tags = {
    "oke-cluster-name" = var.cluster_name
  }
  workers_defined_tags = {}
  */

  # GLOBAL NODE POOL LABELS TO BE APPLIED ON ALL NODES (Kubernetes labels)
  #worker_node_labels = {}

  # Additional NSGs to ba attached to all pods
  # pod_nsg_ids = []

  # Additional NSGs to be attached to all workers
  #worker_nsg_ids = []

  # When using VCN_NATIVE_CNI, set the maximum number of pods for all nodes, must be between 1 and 110
  #max_pods_per_node = 31

  # Disable IMDSv1 endpoints for self-managed nodes
  worker_legacy_imds_endpoints_disabled = true

  # Disable IMDSv1 endpoints for managed nodes
  worker_node_metadata = {
    areLegacyImdsEndpointsDisabled : "true"
  }

  # This is a collection of example node pools that you can use with the OKE module. Set create = true to provision them
  worker_pools = {

    # ORACLE LINUX - MANAGED NODE POOL
    np-ad1 = {
      shape                        = "VM.Standard.E4.Flex"
      size                         = 1
      kubernetes_version           = var.kubernetes_version # You can set this variable with a constant, so that control plane and data plane are upgraded separately
      placement_ads                = ["1"]                  # As best practice, one node pool should be associated only to one specific AD
      ocpus                        = 1                      # No need to specify ocpus and memory if you are not using a Flex shape
      memory                       = 16
      node_cycling_enabled         = false                  # Option to enable/disable node pool cycling through Terraform. Only works with Enhanced clusters!
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      node_cycling_mode            = ["instance"]            # Valid values are instance and boot_volume. The boot_volume mode only works when (kubernetes_version, image_id, boot_volume_size, node_metadata, ssh_public_key, volume_kms_key_id) are modified.
      boot_volume_size             = 50
      # max_pods_per_node = 10                              # When using VCN_NATIVE CNI, configure maximum number of pods for each node in the node pool
      create = false                                        # Set it to true so that the node pool is created
    }

    # VIRTUAL NODE POOL
    oke-virtual = {
      description   = "OKE-managed Virtual Node Pool"
      shape         = "Pod.Standard.E4.Flex"
      mode          = "virtual-node-pool"
      placement_ads = ["1"]
      taints = {
        virtual-node-workload = {
          value  = "true"
          effect = "NoSchedule"
        }
      }
      size   = 1
      create = false
    }

    # UBUNTU - MANAGED NODE POOL
    np-ad1-ubuntu = {
      shape              = "VM.Standard.E4.Flex"
      size               = 1
      kubernetes_version = var.kubernetes_version
      placement_ads      = ["1"]
      ocpus              = 1
      memory             = 16
      # NOTE! The OKE module will automatically verify the image and install the OKE Ubuntu Node package. You just need to create a custom image based on Ubuntu 22.04 or 24.04. Ubuntu Minimal is recommended
      image_type                   = "custom"
      image_id                     = "ocid1.image..." # Put your custom Ubuntu image here
      node_cycling_enabled         = false
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      # NOTE! Make sure you create the original Ubuntu VM with a boot volume of size 50 (the default). Depending on the boot volume size of the original VM, the custom image will require that minimum storage
      boot_volume_size = 100
      create           = false
    }

    # ORACLE LINUX - MANAGED NODE POOL WITH TAINTS
    np-ad1-taints = { # An example of a node pool using a custom cloud-init script to define taints at the node pool level
      shape         = "VM.Standard.E4.Flex"
      size          = 1
      placement_ads = ["1"]
      ocpus         = 1
      memory        = 16
      taints = {
        my-taint = {
          value  = "true"
          effect = "NoSchedule"
        }
      }
      node_cycling_enabled         = false
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      boot_volume_size             = 100
      create                       = false
    }

    # ORACLE LINUX/UBUNTU - SELF-MANAGED NODE
    oke-instance = {
      shape              = "VM.Standard.E4.Flex"
      mode               = "instance"
      kubernetes_version = "v1.32.1"
      description        = "Self managed instance"
      size               = 1
      placement_ads      = ["1"]
      ocpus              = 1
      memory             = 16
      # ENABLE IT FOR UBUNTU NODES
      image_type       = "custom"
      image_id         = "ocid1.image..."
      boot_volume_size = 100
      # Self-managed node specific parameters
      boot_volume_vpus_per_gb = 10 # 10: Balanced, 20: High, 30-120: Ultra High (requires multipath)

      # Burstable instance
      #burst = "BASELINE_1_2" # Valid values BASELINE_1_8,BASELINE_1_2, only for Flex shapes!

      # Enable/disable compute plugins
      agent_config = {
        are_all_plugins_disabled = false
        is_management_disabled   = false
        is_monitoring_disabled   = false
        plugins_config = {
          "Bastion"                             = "DISABLED"
          "Block Volume Management"             = "DISABLED"
          "Compute HPC RDMA Authentication"     = "DISABLED"
          "Compute HPC RDMA Auto-Configuration" = "DISABLED"
          "Compute Instance Monitoring"         = "ENABLED"
          "Compute Instance Run Command"        = "DISABLED"
          "Compute RDMA GPU Monitoring"         = "DISABLED"
          "Custom Logs Monitoring"              = "DISABLED"
          "Management Agent"                    = "DISABLED"
          "Oracle Autonomous Linux"             = "DISABLED"
          "OS Management Service Agent"         = "DISABLED"
        }
      }
      create = false
    }

    ### CLUSTER AUTOSCALER
    # ORACLE LINUX SYSTEM NODES - MANAGED NODE POOL
    np-system-ad1 = {
      shape                        = "VM.Standard.E4.Flex"
      size                         = 1
      placement_ads                = ["1"]
      ocpus                        = 1
      memory                       = 16
      node_cycling_enabled         = false
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      node_labels = {
        role = "system"
      }
      create = false
    }

    # ORACLE LINUX AUTOSCALED - MANAGED NODE POOL
    /* This is a sample pool where autoscaling is enabled, note the freeform tag
     REQUIREMENTS FOR ENABLING THE CLUSTER AUTOSCALER
     - THE CLUSTER AUTOSCALER ADDON MUST BE ENABLED
     - POLICIES MUST BE IN PLACE FOR THE CLUSTER AUTOSCALER
     - THE SYSTEM NODE POOL MUST BE CREATED, will feature nodes labelled with role:system
     - THE "override_coredns" local variable must be set to true in addons.tf
     - NODE POOLS with freeform_tags cluster_autoscaler = "enabled" will be autoscaled
     - NODE POOL IS A MANAGED TYPE, CLUSTER AUTOSCALER DOES NOT WORK WITH SELF-MANAGED WORKER POOLS!
     */
    np-autoscaled-ad1 = {
      shape                        = "VM.Standard.E4.Flex"
      size                         = 0
      placement_ads                = ["1"]
      ocpus                        = 1
      memory                       = 16
      node_cycling_enabled         = false
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      boot_volume_size             = 100
      ignore_initial_pool_size     = true # If set to true, node pool size drift won't be accounted in Terraform, useful also if this pool is autoscaled by an external component (cluster-autoscaler) or manually by a user
      freeform_tags = {
        cluster_autoscaler = "enabled"
      }
      create = false
    }

    # ORACLE LINUX AUTOSCALED PREEMPTIBLE - MANAGED NODE POOL
    # Often, to save money it makes sense to provision preemptible instances, as autoscaled node pools are already very dynamic
    np-autoscaled-preemptible-ad1 = {
      shape                        = "VM.Standard.E4.Flex"
      size                         = 1
      placement_ads                = ["1"]
      ocpus                        = 1
      memory                       = 16
      node_cycling_enabled         = false
      node_cycling_max_surge       = "50%"
      node_cycling_max_unavailable = "25%"
      boot_volume_size             = 100
      ignore_initial_pool_size     = true # If set to true, node pool size drift won't be accounted in Terraform, useful also if this pool is autoscaled by an external component (cluster-autoscaler) or manually by a user
      freeform_tags = {
        cluster_autoscaler = "enabled"
      }
      preemptible_config = {
        enable                  = true
        is_preserve_boot_volume = false
      }
      create = false
    }

  }

  providers = {
    oci.home = oci.home
  }
}