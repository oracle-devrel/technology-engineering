resource "oci_identity_policy" "dbman_opsi" {
  count          = var.create_identity_policy ? 1 : 0
  compartment_id = var.tenancy_ocid
  name           = var.policy_name
  description    = var.policy_description
  statements     = var.policy_statements
}

resource "oci_core_vcn" "test" {
  count          = var.create_test_network ? 1 : 0
  compartment_id = var.compartment_ocid
  cidr_block     = var.test_vcn_cidr
  display_name   = "dbman-opsi-vcn"
  dns_label      = "dbmanopsi"
}

# The private subnet that hosts the Database Management / Ops Insights private
# endpoints must reach OCI services. Without a Service Gateway + route rule the
# endpoints create successfully but collection silently fails.
data "oci_core_services" "all" {
  count = var.create_test_network ? 1 : 0
}

locals {
  oci_all_services = var.create_test_network ? [
    for svc in data.oci_core_services.all[0].services :
    svc if can(regex("all-.*-services-in-oracle-services-network", svc.cidr_block))
  ] : []
}

resource "oci_core_service_gateway" "test" {
  count          = var.create_test_network ? 1 : 0
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.test[0].id
  display_name   = "dbman-opsi-sgw"

  services {
    service_id = local.oci_all_services[0].id
  }
}

resource "oci_core_route_table" "test" {
  count          = var.create_test_network ? 1 : 0
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.test[0].id
  display_name   = "dbman-opsi-rt"

  route_rules {
    destination       = local.oci_all_services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.test[0].id
  }
}

resource "oci_core_security_list" "test" {
  count          = var.create_test_network ? 1 : 0
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.test[0].id
  display_name   = "dbman-opsi-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # Oracle listener ports for monitoring connections within the subnet.
  ingress_security_rules {
    protocol = "6" # TCP
    source   = var.test_subnet_cidr

    tcp_options {
      min = 1521
      max = 1522
    }
  }
}

resource "oci_core_subnet" "test_private" {
  count                      = var.create_test_network ? 1 : 0
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.test[0].id
  cidr_block                 = var.test_subnet_cidr
  display_name               = "dbman-opsi-private-subnet"
  prohibit_public_ip_on_vnic = true
  dns_label                  = "dbmopsi"
  route_table_id             = oci_core_route_table.test[0].id
  security_list_ids          = [oci_core_security_list.test[0].id]
}

locals {
  selected_vcn_id      = var.create_test_network ? oci_core_vcn.test[0].id : var.vcn_ocid
  selected_subnet_id   = var.create_test_network ? oci_core_subnet.test_private[0].id : var.subnet_ocid
  provision_dbcs       = { for target in var.targets : target.name => target if target.provision && target.kind == "dbcs" }
  provision_autonomous = { for target in var.targets : target.name => target if target.provision && target.kind == "autonomous" }
}

resource "oci_database_management_db_management_private_endpoint" "dbmgmt" {
  compartment_id = var.compartment_ocid
  name           = "dbman_opsi_dbmgmt_pe"
  subnet_id      = local.selected_subnet_id
  description    = "Database Management private endpoint for dbman-opsi PoC."
}

resource "oci_kms_vault" "test" {
  count          = var.create_vault ? 1 : 0
  compartment_id = var.compartment_ocid
  display_name   = "dbman-opsi-vault"
  vault_type     = "DEFAULT"
}

resource "oci_database_db_system" "dbcs" {
  for_each            = local.provision_dbcs
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[var.availability_domain_index].name
  subnet_id           = local.selected_subnet_id
  display_name        = each.value.name
  shape               = var.dbcs_shape
  database_edition    = "ENTERPRISE_EDITION"
  ssh_public_keys     = var.ssh_public_keys
  license_model       = "LICENSE_INCLUDED"
  node_count          = 1
  # When the subnet has no DNS label, the DB system launch requires an explicit
  # network domain ("domain name cannot be null"). Reuse the subnet's existing
  # DB domain. null lets the provider derive it from a DNS-enabled subnet.
  domain = var.dbcs_domain
  # Flex shapes (e.g. VM.Standard.E4.Flex) require an explicit core count, and a
  # VM DB system requires a data storage size. Without these, apply fails with a
  # missing-required-attribute error.
  cpu_core_count          = var.dbcs_cpu_core_count
  data_storage_size_in_gb = var.dbcs_data_storage_gb
  hostname                = substr(replace(lower(each.value.name), "/[^a-z0-9]/", ""), 0, 12)

  db_home {
    db_version   = var.db_version
    display_name = "${each.value.name}-home"

    database {
      db_name        = substr(replace(each.value.name, "-", ""), 0, 8)
      admin_password = var.db_admin_password
      character_set  = "AL32UTF8"
      ncharacter_set = "AL16UTF16"
    }
  }
}

resource "oci_database_autonomous_database" "adb" {
  for_each                 = local.provision_autonomous
  compartment_id           = var.compartment_ocid
  display_name             = each.value.name
  db_name                  = substr(replace(each.value.name, "-", ""), 0, 14)
  admin_password           = var.adb_admin_password
  compute_count            = var.adb_compute_count
  compute_model            = "ECPU"
  data_storage_size_in_tbs = var.adb_storage_tbs
  db_workload              = "OLTP"
  is_free_tier             = false
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

output "vcn_ocid" {
  value = local.selected_vcn_id
}

output "subnet_ocid" {
  value = local.selected_subnet_id
}

output "db_management_private_endpoint_ocid" {
  value = oci_database_management_db_management_private_endpoint.dbmgmt.id
}

output "service_gateway_ocid" {
  value = var.create_test_network ? oci_core_service_gateway.test[0].id : null
}

output "provisioned_dbcs_ids" {
  value = { for name, system in oci_database_db_system.dbcs : name => system.id }
}

output "provisioned_autonomous_database_ids" {
  value = { for name, database in oci_database_autonomous_database.adb : name => database.id }
}

# Optional DBM + OPSI enablement (modular, off by default). service_name/host_ip
# are runtime-discovered, so populate var.observability_targets after the DB is up.
module "observability" {
  count  = var.enable_observability ? 1 : 0
  source = "../../modules/dbm-opsi-enablement"

  compartment_id           = var.compartment_ocid
  dbm_private_endpoint_id  = oci_database_management_db_management_private_endpoint.dbmgmt.id
  opsi_private_endpoint_id = var.opsi_private_endpoint_id
  password_secret_id       = var.dbsnmp_secret_id
  enable_ops_insights      = var.opsi_private_endpoint_id != null
  targets                  = var.observability_targets
}
