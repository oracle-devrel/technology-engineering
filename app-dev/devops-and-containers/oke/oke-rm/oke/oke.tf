# NOTE: OKE often requires some policies to work with depending on the use case. You can find a complete list at this link:
# https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/oke/oke-policies/policies.md

locals {
  volume_kms_key_id = ""  # kms OCID of the key used for in-transit and at-rest encryption of block volumes
  ssh_public_key = ""     # Insert the ssh public key to access worker nodes

  runcmd_bootstrap_ubuntu = "oke bootstrap"
  runcmd_growfs_oracle_linux = "sudo /usr/libexec/oci-growfs -y"
  # Kubelet extra args is mostly used to taint nodes at start up in a node pool
  kubelet_extra_args = "--register-with-taints=env=dev:NoSchedule,cluster=oke:PreferNoSchedule"

  # Use this cloud init script for Oracle Linux nodes, it is important to expand the boot volume in any case
  cloud_init_ol = {
    runcmd = compact([
      local.runcmd_growfs_oracle_linux,        # Modify here depending on the OS selected for the worker nodes
    ])
  }

  # UBUNTU NODES: use this cloud init, and make sure to disable the default cloud init
  cloud_init_ubuntu = {
    runcmd = compact([
      local.runcmd_bootstrap_ubuntu,        # Modify here depending on the OS selected for the worker nodes
    ])
  }

  # Cloud init to taint nodes using Oracle Linux nodes. Make sure to disable the default cloud init
  cloud_init_with_taint_ol = {
    runcmd = [
      "curl --fail -H \"Authorization: Bearer Oracle\" -L0 http://169.254.169.254/opc/v2/instance/metadata/oke_init_script | base64 --decode >/var/run/oke-init.sh",
      local.runcmd_growfs_oracle_linux,
      "bash /var/run/oke-init.sh --kubelet-extra-args \"${local.kubelet_extra_args}\""
    ]
  }

}

module "oke" {
  source  = "oracle-terraform-modules/oke/oci"
  version = "5.3.1"
  compartment_id = var.oke_compartment_id
  # IAM - Policies
  create_iam_autoscaler_policy = "never"
  create_iam_kms_policy = "never"
  create_iam_operator_policy = "never"
  create_iam_worker_policy = "never"
  # Network module - VCN
  subnets = {
    bastion = { create = "never"}
    operator = { create = "never" }
    pub_lb = { id = local.is_lb_subnet_private ? null : var.lb_subnet_id }
    int_lb = { id = local.is_lb_subnet_private ? var.lb_subnet_id : null }
    cp = { id = var.cp_subnet_id }
    workers = { id = var.worker_subnet_id }
    pods = { id = local.is_flannel ? null : var.pod_subnet_id }
  }
  nsgs = {
    bastion = { create = "never" }
    operator = { create = "never" }
    pub_lb = {create = "never" }
    int_lb = { create = "never"}
    cp = { id = var.cp_nsg_id }
    workers = { id = var.worker_nsg_id }
    pods = { create = "never", id = var.cni_type == "flannel" ? null : var.pod_nsg_id }
  }
  network_compartment_id = var.network_compartment_id
  assign_public_ip_to_control_plane = ! local.is_cp_subnet_private
  create_vcn = false
  vcn_id = var.vcn_id
  # Network module - security
  control_plane_allowed_cidrs = var.cp_allowed_cidr_list
  control_plane_is_public = ! local.is_cp_subnet_private
  load_balancers = local.is_lb_subnet_private ? "internal" : "public"
  preferred_load_balancer = local.is_lb_subnet_private ? "internal" : "public"
  # Cluster module
  create_cluster = true
  cluster_kms_key_id = var.cluster_kms_key_id
  cluster_name = var.cluster_name
  cluster_type = var.cluster_type
  cni_type = local.cni
  kubernetes_version = var.kubernetes_version
  services_cidr      = var.services_cidr
  pods_cidr = var.pods_cidr
  use_signed_images  = false
  use_defined_tags = false

  # OIDC
  oidc_discovery_enabled = local.oidc_discovery_enabled
  oidc_token_auth_enabled = local.oidc_authentication_enabled
  oidc_token_authentication_config = local.oidc_token_authentication_config

  cluster_freeform_tags = {
    cluster = var.cluster_name
  }

  # Bastion
  create_bastion = false

  # Operator
  create_operator = false

  # OKE data plane, node workers
  worker_pool_mode = "node-pool"
  worker_is_public = false
  #ssh_public_key = local.ssh_public_key    # De-comment if you want a ssh key to access the worker nodes, be sure to set the local variable
  worker_image_type = "oke"                 # NOTE: Better to use "custom" and specify the image id in a production environment
  #worker_image_id = ""                     # The image id to use for the worker nodes. For Oracle Linux images, check this link: https://docs.oracle.com/en-us/iaas/images/oke-worker-node-oracle-linux-8x/index.htm
                                            # For Ubuntu images, you need to import it in your tenancy, see: https://canonical-oracle.readthedocs-hosted.com/en/latest/oracle-how-to/deploy-oke-nodes-using-ubuntu-images/


  # Set this to true to enable in-transit encryption on all node pools by default
  # NOTE: in-transit encryption is supported only for paravirtualized attached block volumes (NOT boot volumes), hence you will need to create another StorageClass in the cluster as the default oci-bv StorageClass uses iSCSI
  # Also note that Bare Metal instances do not support paravirtualized volumes, so do not enable this in node pools that require BM instances
  worker_pv_transit_encryption = false
  # Enable encryption of volumes with a key managed by you, in your OCI Vault
  #worker_volume_kms_key_id = local.volume_kms_key_id

  # When using OCI_VCN_NATIVE_CNI, set the maximum number of pods for all nodes, must be between 1 and 110
  #max_pods_per_node = 31

  worker_disable_default_cloud_init = false # If set to true, will let you full control over the cloud init, set it when using ubuntu nodes or nodes with taints (can even be set individually at the node pool level)
  worker_cloud_init = [{ content_type = "text/cloud-config", content = yamlencode(local.cloud_init_ol)}]         # Cloud init is different, depending if you are using Ubuntu or Oracle Linux nodes. You can also set taints with the cloud init

  # GLOBAL TAGS TO BE APPLIED ON ALL NODES
  # NOTE: tags will be applied to both the node pool and the nodes
/*workers_freeform_tags = {
    "oke-cluster-name" = var.cluster_name
  }
  workers_defined_tags = {}
  */

  # GLOBAL NODE POOL LABELS TO BE APPLIED ON ALL NODES (Kubernetes labels)
  #worker_node_labels = {}

  worker_pools = {

    # SAMPLE NODE POOL, SET create = true TO PROVISION IT
    np-ad1 = {
      shape = "VM.Standard.E4.Flex"
      size = 1
      kubernetes_version = var.kubernetes_version   # You can set this value as fixed, so that control plane and data plane are upgraded separately
      placement_ads = ["1"]                 # As best practice, one node pool should be associated only to one specific AD
      ocpus = 1                             # No need to specify ocpus and memory if you are not using a Flex shape
      memory = 16
      #image_type = "custom"
      #image_id = ""                        # You can override global worker node parameters individually in the node pool
      node_cycling_enabled = false           # Option to enable/disable node pool cycling through Terraform. Only works with Enhanced clusters!
      node_cycling_max_surge = "50%"
      node_cycling_max_unavailable = "25%"

      node_cycling_mode = ["boot_volume"]   # Valid values are instance and boot_volume. Only works when (kubernetes_version, image_id, boot_volume_size, node_metadata, ssh_public_key, volume_kms_key_id) are modified. If you need to change something else, switch to instance
                                            # NOTE: boot_volume mode seems to work only for Flannel clusters for now
      boot_volume_size = 100                # For Oracle Linux, make sure the oci-growfs command is specified in the cloud-init script. This module already implements this
      freeform_tags = {                     # Nodes in the node pool will be tagged with these freeform tags
        "oke-cluster-name" = var.cluster_name
      }
      # max_pods_per_node = 10               # When using VCN_NATIVE CNI, configure maximum number of pods for each node in the node pool
      ignore_initial_pool_size = false       # If set to true, node pool size drift won't be accounted in Terraform, useful also if this pool is autoscaled by an external component (cluster-autoscaler) or manually by a user
      create = false                          # Set it to true so that the node pool is created
    }

    # SYSTEM NODE POOL TO BE ENABLED FOR THE CLUSTER AUTOSCALER
    np-system-ad1 = {
      shape = "VM.Standard.E4.Flex"
      size = 1
      placement_ads = ["1"]
      ocpus = 1
      memory = 16
      node_cycling_enabled = true         # Only works with Enhanced clusters!
      node_cycling_max_surge = "50%"
      node_cycling_max_unavailable = "25%"
      node_cycling_mode = ["boot_volume"]
      node_labels = {
        role = "system"
      }
      create = false
    }


    # SAMPLE NODE POOL WITH A CLOUD INIT TO SET NODE TAINTS
    np-taints = {         # An example of a node pool using a custom cloud-init script to define taints at the node pool level
      shape = "VM.Standard.E4.Flex"        # No need to specify ocpus and memory if you are not using a Flex shape
      size = 1
      placement_ads = ["1"]                # As best practice, one node pool should be associated only to one specific AD
      ocpus = 2
      memory = 16
      disable_default_cloud_init = true    # If you want to configure some kubelet arguments, make sure to disable the default cloud-init and remember to include it in your custom cloud-init
      cloud_init = [{ content_type = "text/cloud-config", content = yamlencode(local.cloud_init_with_taint_ol)}]
      node_cycling_enabled = true
      node_cycling_max_surge = "50%"
      node_cycling_max_unavailable = "25%"
      node_cycling_mode = ["boot_volume"]
      boot_volume_size = 100
      create = false
    }


    # SAMPLE AUTOSCALED NODE POOL
    # This is a sample pool where autoscaling is enabled, note the freeform tag
    # REQUIREMENTS FOR ENABLING THE CLUSTER AUTOSCALER
    # - THE CLUSTER AUTOSCALER ADDON MUST BE ENABLED
    # - POLICIES MUST BE IN PLACE FOR THE CLUSTER AUTOSCALER
    # - THE SYSTEM NODE POOL MUST BE CREATED, will feature nodes labelled with role:system
    # - THE "override_coredns" local variable must be set to true in addons.tf
    # - NODE POOLS with freeform_tags cluster_autoscaler = "enabled" will be autoscaled
    np-autoscaled-ad1 = {
      shape = "VM.Standard.E4.Flex"
      size = 0
      placement_ads = ["1"]
      ocpus = 1
      memory = 16
      node_cycling_enabled = true
      node_cycling_max_surge = "50%"
      node_cycling_max_unavailable = "25%"
      node_cycling_mode = ["boot_volume"]
      boot_volume_size = 100
      ignore_initial_pool_size = true
      freeform_tags = {
        cluster_autoscaler = "enabled"
      }
      create = false
    }

    # SAMPLE AUTOSCALED PREEMPTIBLE NODE POOL
    # Often, to save money it makes sense to provision preemptible instances, as autoscaled node pools are already very dynamic
    np-autoscaled-preemptible-ad1 = {
      shape = "VM.Standard.E4.Flex"
      size = 1
      placement_ads = ["1"]
      ocpus = 1
      memory = 16
      node_cycling_enabled = true
      node_cycling_max_surge = "50%"
      node_cycling_max_unavailable = "25%"
      node_cycling_mode = ["boot_volume"]
      boot_volume_size = 70
      ignore_initial_pool_size = true
      freeform_tags = {
        cluster_autoscaler = "enabled"
      }
      preemptible_config = {
        enable = true
        is_preserve_boot_volume = false
      }
      create = false
    }



  }

  providers = {
    oci.home = oci.home
  }
}