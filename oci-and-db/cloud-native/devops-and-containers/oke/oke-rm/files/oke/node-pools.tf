variable "worker_pools" {
  description = "Named worker-pool definitions passed to the OKE module. Set create=true to enable a pool. Omitted Kubernetes version and network settings inherit the cluster defaults."
  # Pool modes accept different attributes; retain the upstream module's flexible type.
  type     = any
  nullable = false

  default = {
    np-ad1 = {
      create           = false
      mode             = "node-pool"
      shape            = "VM.Standard.E5.Flex"
      size             = 1
      ocpus            = 1
      memory           = 8
      boot_volume_size = 100
    }

    # GVA is an optional networking feature of managed nodes.
    # Requires VCN-native CNI, an IPv4 multi-CIDR subnet, and a compatible shape.
    np-gva = {
      create              = false
      mode                = "node-pool"
      shape               = "VM.Standard.E5.Flex"
      size                = 1
      placement_ads       = ["1"]
      ocpus               = 1
      memory              = 8
      boot_volume_size    = 100
      network_launch_type = "PARAVIRTUALIZED"
      gva_secondary_vnics = {
        frontend = {
          display_name           = "gva-frontend"
          subnet_key             = "pods"
          ip_count               = 16
          application_resources  = ["frontend"]
          assign_public_ip       = false
          skip_source_dest_check = false
        }
      }
    }

    # Dedicated system nodes use the bundled cloud-init and a scheduling label.
    np-system = {
      create                     = false
      mode                       = "node-pool"
      shape                      = "VM.Standard.E5.Flex"
      size                       = 1
      ocpus                      = 1
      memory                     = 8
      boot_volume_size           = 100
      node_labels                = { "node-role/system" = "true" }
      disable_default_cloud_init = true
      cloud_init                 = [{ content_type = "text/cloud-config", content = "cloud-init/system.yml" }]
    }

    oke-virtual = {
      create = false
      mode   = "virtual-node-pool"
      shape  = "Pod.Standard.E4.Flex"
      size   = 1
      taints = {
        virtual-node-workload = {
          value  = "true"
          effect = "NoSchedule"
        }
      }
    }
  }

  validation {
    condition = try(alltrue([
      for pool in var.worker_pools :
      lookup(pool, "mode", "node-pool") == "virtual-node-pool" || length(lookup(pool, "taints", {})) == 0
    ]), false)
    error_message = "Taints are supported only for virtual-node-pool definitions."
  }

  validation {
    condition = try(alltrue([
      for pool in var.worker_pools :
      lookup(pool, "mode", "node-pool") == "node-pool" || length(lookup(pool, "gva_secondary_vnics", {})) == 0
    ]), false)
    error_message = "GVA secondary VNIC profiles are supported only for managed node-pool definitions."
  }

  validation {
    condition = can(keys(var.worker_pools)) && try(alltrue([
      for name, pool in var.worker_pools :
      trimspace(name) != "" && can(keys(pool)) && contains([true, false], pool.create)
    ]), false)
    error_message = "worker_pools must be an object keyed by nonempty pool names. Every pool must explicitly set create to true or false."
  }

  validation {
    condition = try(alltrue([
      for pool in var.worker_pools :
      contains(["node-pool", "virtual-node-pool"], lookup(pool, "mode", "node-pool"))
    ]), false)
    error_message = "Worker pool mode must be node-pool (managed nodes) or virtual-node-pool (virtual nodes)."
  }

  validation {
    condition = try(alltrue([
      for pool in var.worker_pools :
      lookup(pool, "size", 0) >= 0 && floor(lookup(pool, "size", 0)) == lookup(pool, "size", 0)
    ]), false)
    error_message = "Worker pool size must be a nonnegative integer."
  }

  validation {
    condition = try(alltrue(flatten([
      for pool in var.worker_pools : [
        for ad in lookup(pool, "placement_ads", []) :
        can(regex("^[1-9][0-9]*$", tostring(ad)))
      ]
    ])), false)
    error_message = "placement_ads must contain positive, one-based availability-domain numbers such as 1. Omit it to inherit defaults; blank entries are not allowed."
  }
}
