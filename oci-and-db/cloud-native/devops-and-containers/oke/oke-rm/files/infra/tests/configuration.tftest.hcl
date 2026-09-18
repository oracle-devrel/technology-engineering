mock_provider "oci" {
  override_during = plan

  mock_data "oci_core_services" {
    defaults = {
      services = [
        {
          cidr_block = "all-fra-services-in-oracle-services-network"
        }
      ]
    }
  }

  mock_resource "oci_core_network_security_group" {
    defaults = {
      id = "ocid1.networksecuritygroup.oc1.eu-frankfurt-1.test"
    }
  }
}

mock_provider "random" {
  override_during = plan

  mock_resource "random_uuid" {
    defaults = {
      result = "123e4567-e89b-42d3-a456-426614174000"
    }
  }
}

variables {
  tenancy_ocid           = "ocid1.tenancy.oc1..test"
  region                 = "eu-frankfurt-1"
  compartment_ocid       = "ocid1.compartment.oc1..test"
  network_compartment_id = "ocid1.compartment.oc1..network"
}

run "database_subnet_does_not_require_database_nsgs" {
  command = plan

  variables {
    create_vcn           = true
    create_db_subnet     = true
    create_database_nsgs = false
    db_service_list      = []
  }

  assert {
    condition     = module.network.db_subnet_created
    error_message = "The database subnet must be created independently from database NSG selection."
  }

  assert {
    condition = (
      module.network.karpenter_worker_role_tag_value == "worker-123e4567" &&
      module.network.karpenter_pod_role_tag_value == "pod-123e4567"
    )
    error_message = "Karpenter network role tag values must include the persistent stack UUID."
  }

  assert {
    condition = (
      module.network.nsg_names.control_plane == "cp-123e4567" &&
      module.network.nsg_names.worker == "worker-123e4567"
    )
    error_message = "Generated NSG names must include the persistent stack UUID."
  }
}

run "drg_is_rejected_for_an_existing_vcn" {
  command = plan

  variables {
    create_vcn = false
    vcn_id     = "ocid1.vcn.oc1.eu-frankfurt-1.test"
    enable_drg = true
  }

  expect_failures = [output.vcn_id]
}

run "all_generated_nsg_names_use_the_stack_uuid" {
  command = plan

  variables {
    create_vcn           = true
    create_database_nsgs = true
    db_service_list      = ["postgres", "cache", "oracledb", "mysql"]
    separate_db_nsg      = true
    create_streaming_nsg = true
  }

  assert {
    condition = alltrue([
      for name in values(module.network.nsg_names) : endswith(name, "-123e4567")
    ])
    error_message = "Every generated NSG name must end with the persistent stack UUID."
  }

  assert {
    condition = (
      module.network.gateway_names.service == "SG-123e4567" &&
      module.network.gateway_names.nat == "NAT-123e4567" &&
      module.network.gateway_names.internet == "IGW-123e4567"
    )
    error_message = "Every gateway with a standard name must end with the persistent stack UUID."
  }

  assert {
    condition = (
      module.network.pod_fss_rule_counts.pod_nsg == 10 &&
      module.network.pod_fss_rule_counts.fss_nsg == 10
    )
    error_message = "FSS support with VCN-native pod networking must create all ten stateless rules on both the pod and FSS NSGs."
  }

  assert {
    condition     = output.fss_nsg_id == module.network.fss_nsg_id
    error_message = "The root stack must expose the FSS NSG OCID needed by mount targets."
  }
}

run "pod_fss_rules_are_disabled_without_fss_support" {
  command = plan

  variables {
    create_vcn = true
    create_fss = false
  }

  assert {
    condition = (
      module.network.pod_fss_rule_counts.pod_nsg == 0 &&
      module.network.pod_fss_rule_counts.fss_nsg == 0
    )
    error_message = "Pod-to-FSS rules must not be created when FSS support is disabled."
  }
}

run "invalid_cni_is_rejected" {
  command = plan

  variables {
    cni_type = "unsupported"
  }

  expect_failures = [var.cni_type]
}
run "multiple_control_plane_cidrs" {
  command = plan
  variables {
    cp_subnet_private      = false
    cp_allowed_source_cidr = ["192.0.2.0/24", "198.51.100.0/24", "192.0.2.0/24"]
    cp_egress_cidr         = ["203.0.113.0/25", "203.0.113.128/25"]
  }
  assert {
    condition = (
      tolist(module.network.control_plane_external_cidr_rules.ingress) == tolist(["192.0.2.0/24", "198.51.100.0/24"]) &&
      module.network.control_plane_external_cidr_rules.replies == module.network.control_plane_external_cidr_rules.ingress &&
      length(module.network.control_plane_external_cidr_rules.egress) == 2
    )
    error_message = "Each distinct source must get ingress and return rules, and each destination must get an egress rule."
  }
}

run "empty_control_plane_cidrs" {
  command = plan
  variables {
    cp_subnet_private      = false
    cp_allowed_source_cidr = []
    cp_egress_cidr         = []
  }
  assert {
    condition = alltrue([
      for rules in values(module.network.control_plane_external_cidr_rules) : length(rules) == 0
    ])
    error_message = "Empty lists must create no external CIDR rules."
  }
}

run "disabled_external_egress" {
  command = plan
  variables {
    cp_subnet_private         = false
    allow_external_cp_traffic = false
    cp_egress_cidr            = ["192.0.2.0/24", "198.51.100.0/24"]
  }
  assert {
    condition     = length(module.network.control_plane_external_cidr_rules.egress) == 0
    error_message = "The egress toggle must suppress every configured external destination."
  }
}

run "invalid_control_plane_cidr_entry" {
  command = plan
  variables {
    cp_allowed_source_cidr = ["192.0.2.0/24", "invalid"]
    cp_egress_cidr         = ["198.51.100.0/24", "300.0.0.0/24"]
  }
  expect_failures = [var.cp_allowed_source_cidr, var.cp_egress_cidr]
}
