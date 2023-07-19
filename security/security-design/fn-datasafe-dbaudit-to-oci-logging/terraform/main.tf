###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

resource "null_resource" "Login2OCIR" {
  depends_on = [module.setup-network, oci_objectstorage_bucket.tracker-bucket, oci_identity_policy.DataSafetoLoggingFunctionsPolicy,
    oci_artifacts_container_repository.fn_container_repository, oci_functions_application.DataSafeAuditDBtoLoggingApp]

  provisioner "local-exec" {
    command = "fn list context"
  }
  provisioner "local-exec" {
    command = "echo '${var.ocir_user_password}' |  docker login ${local.ocir_docker_repository} --username ${local.namespace}/${var.ocir_user_name} --password-stdin"
  }
}

resource "null_resource" "DataSafeAuditDBtoLoggingPush2OCIR" {
  depends_on = [null_resource.Login2OCIR, oci_functions_application.DataSafeAuditDBtoLoggingApp]

  provisioner "local-exec" {
    command     = "image=$(docker images | grep oci-datasafe-audit-to-logging | awk -F ' ' '{print $3}') ; docker rmi -f $image &> /dev/null ; echo $image"
    working_dir = local.working_dir
  }

  provisioner "local-exec" {
    command     = "fn build --verbose"
    working_dir = local.working_dir
  }

  provisioner "local-exec" {
    command     = "image=$(docker images | grep oci-datasafe-audit-to-logging | awk -F ' ' '{print $3}') ; docker tag $image ${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}/${local.function_display_name}:0.0.1"
    working_dir = local.working_dir
 }

  provisioner "local-exec" {
    command     = "docker push ${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}/${local.function_display_name}:0.0.1"
    working_dir = local.working_dir
 }
}

module "setup-network" {
  source = "./modules/network"
  count  = var.create_network ? 1 : 0
  compartment_ocid = var.compartment_ocid
  VCN-CIDR = var.VCN-CIDR
  subnet-CIDR = var.subnet-CIDR
  vcndnslabelprefix = var.vcndnslabelprefix
  vcnnameprefix = var.vcnnameprefix
  vcnnameroutingtableprefix = var.vcnnameroutingtableprefix
  vcnroutingtabledescriptionservicegw = var.vcnroutingtabledescriptionservicegw
  vcnnamedhcpopitonsprefix = var.vcnnamedhcpopitonsprefix
  subnetnameprefix = var.subnetnameprefix
  subnetdnslabelprefix = var.subnetdnslabelprefix
  vcnnamesecuritylistprefix = var.vcnnamesecuritylistprefix
  vcnnameservicegatewayprefix = var.vcnnameservicegatewayprefix
  deployment_name = var.deployment_name
  region = var.region
  purpose = var.purpose
}
