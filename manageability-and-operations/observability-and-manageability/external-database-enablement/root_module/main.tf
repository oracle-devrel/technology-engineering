module "container_connection" {
  source           = "./modules/container/container_connection"
  compartment_ocid = var.compartment_ocid

  for_each                                                      = local.dbsystem_def_map
  external_container_database_display_name                      = "${each.key}_${each.value.containerName}"
  external_cdb_connector_connection_credentials_credential_name = "${each.key}.${each.value.databaseCredentials}"
  external_cdb_connector_connection_credentials_credential_type = upper(each.value.protocol) == "TCPS" ? "SSL_DETAILS" : "DETAILS"
  external_cdb_connector_connection_credentials_password        = try(local.dbcred_def_map["${each.value.databaseCredentials}"].userPasswordSecretId, null) != null ? base64decode(module.password_secret["${each.value.databaseCredentials}"].password_secret_content) : local.dbcred_def_map["${each.value.databaseCredentials}"].userPassword
  external_cdb_connector_connection_credentials_role            = local.dbcred_def_map["${each.value.databaseCredentials}"].userRole
  external_cdb_connector_connection_credentials_username        = local.dbcred_def_map["${each.value.databaseCredentials}"].userName
  external_database_connector_connection_string_hostname        = each.value.host
  external_database_connector_connection_string_port            = each.value.port
  external_database_connector_connection_string_protocol        = upper(each.value.protocol)
  ssl_secret_id                                                 = upper(each.value.protocol) == "TCPS" ? local.dbcred_def_map["${each.value.databaseCredentials}"].sslSecretId : null
  external_cdb_connector_connection_string_service              = each.value.containerServiceName
  external_database_connector_agent_id                          = each.value.managementAgentId
}

module "container_services" {
  source           = "./modules/container/container_services"
  compartment_ocid = var.compartment_ocid

  for_each                                       = local.dbsystem_def_map
  external_database_connector_agent_id           = each.value.managementAgentId
  external_container_id                          = module.container_connection["${each.key}"].external_container_id
  external_container_display_name                = module.container_connection["${each.key}"].external_container_display_name
  external_container_connector_id                = module.container_connection["${each.key}"].external_container_connector_id
  enable_database_management_cdb                 = lower(each.value.containerDBManagement)
  external_container_database_management_license = upper(each.value.dbManagementLicense)
  enable_stack_monitoring_cdb                    = lower(each.value.containerStackMonitoring)
  enable_stack_monitoring_asm                    = lower(each.value.asmStackMonitoring)
  asm_hostname                                   = each.value.asmHost
  asm_port                                       = each.value.asmPort
  asm_service                                    = each.value.asmServiceName
  asm_credentials_role                           = lower(each.value.asmStackMonitoring == "enable") ? upper(local.dbcred_def_map["${each.value.asmCredentials}"].userRole) : ""
  asm_credentials_username                       = lower(each.value.asmStackMonitoring == "enable") ? local.dbcred_def_map["${each.value.asmCredentials}"].userName : ""
  asm_credentials_password_secret_id             = lower(each.value.asmStackMonitoring == "enable") ? local.dbcred_def_map["${each.value.asmCredentials}"].userPasswordSecretId : ""
}

module "pdb" {
  source           = "./modules/pdb"
  compartment_ocid = var.compartment_ocid

  for_each                                                      = { for pdb in local.pdb_flat_list : "${pdb.dbsystemKey}_${pdb.pdbServiceName}" => pdb }
  external_pluggable_database_display_name                      = "${each.value.dbsystemKey}_${each.value.pdbName}"
  oci_database_external_container_database_id                   = module.container_connection["${each.value.dbsystemKey}"].external_container_id
  external_pdb_connector_connection_credentials_credential_name = "${each.value.dbsystemKey}.${each.value.databaseCredentials}"
  external_pdb_connector_connection_credentials_credential_type = upper(local.dbsystem_def_map["${each.value.dbsystemKey}"].protocol) == "TCPS" ? "SSL_DETAILS" : "DETAILS"
  external_pdb_connector_connection_credentials_password        = try(local.dbcred_def_map["${each.value.databaseCredentials}"].userPasswordSecretId, null) != null ? base64decode(module.password_secret["${each.value.databaseCredentials}"].password_secret_content) : local.dbcred_def_map["${each.value.databaseCredentials}"].userPassword
  external_pdb_connector_connection_credentials_role            = local.dbcred_def_map["${each.value.databaseCredentials}"].userRole
  external_pdb_connector_connection_credentials_username        = local.dbcred_def_map["${each.value.databaseCredentials}"].userName
  external_database_connector_connection_string_hostname        = local.dbsystem_def_map["${each.value.dbsystemKey}"].host
  external_database_connector_connection_string_port            = local.dbsystem_def_map["${each.value.dbsystemKey}"].port
  external_database_connector_connection_string_protocol        = upper(local.dbsystem_def_map["${each.value.dbsystemKey}"].protocol)
  ssl_secret_id                                                 = upper(local.dbsystem_def_map["${each.value.dbsystemKey}"].protocol) == "TCPS" ? local.dbcred_def_map["${each.value.databaseCredentials}"].sslSecretId : null
  external_pdb_connector_connection_string_service              = each.value.pdbServiceName
  external_database_connector_agent_id                          = local.dbsystem_def_map["${each.value.dbsystemKey}"].managementAgentId
  enable_database_management_pdb                                = module.container_services["${each.value.dbsystemKey}"].database_management_cdb_status ? lower(each.value.pdbDBManagement) : "disable"
  enable_stack_monitoring_pdb                                   = lower(each.value.pdbStackMonitoring)
  enable_operations_insights_pdb                                = lower(each.value.pdbOPSI)
}

module "password_secret" {
  source = "./modules/password_secret"

  for_each           = { for cred_key, cred in local.dbcred_def_map : cred_key => cred.userPasswordSecretId if try(cred.userPasswordSecretId, null) != null }
  password_secret_id = each.value
}

locals {
  dbsystem_def_map = jsondecode(file("./db_systems.json"))
  dbcred_def_map   = jsondecode(file("./db_credentials.json"))
  pdb_flat_list = flatten([for dbsystem_key, dbsystem in local.dbsystem_def_map : [
    for pdb_key, pdb in dbsystem.pdbs : {
      dbsystemKey         = dbsystem_key
      pdbName             = pdb.pdbName
      databaseCredentials = pdb.databaseCredentials
      pdbServiceName      = pdb.pdbServiceName
      pdbDBManagement     = pdb.pdbDBManagement
      pdbOPSI             = pdb.pdbOPSI
      pdbStackMonitoring  = pdb.pdbStackMonitoring
    }
    ]
  ])
}