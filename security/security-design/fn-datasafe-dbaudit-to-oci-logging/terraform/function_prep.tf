###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
###############################################################################


resource "null_resource" "Login2OCIR" {
  depends_on = [module.setup-network, oci_objectstorage_bucket.tracker-bucket, oci_identity_policy.FunctionPolicy,
    oci_artifacts_container_repository.fn_container_repository, oci_functions_application.FunctionApp]

  provisioner "local-exec" {
    command = "echo '${var.ocir_user_password}' |  docker login ${local.ocir_docker_repository} --username ${local.namespace}/${local.identity_name} --password-stdin"
  }
}

resource "null_resource" "FunctionAppPush2OCIR" {
  depends_on = [null_resource.Login2OCIR, oci_functions_function.fun1]

  provisioner "local-exec" {
    command     = "image=$(docker images | grep ${var.FunctionName} | awk -F ' ' '{print $3}') ; docker rmi -f $image &> /dev/null ; echo $image"
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    command     = "fn build --verbose"
    working_dir ="${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    command     = "image=$(docker images | grep ${var.FunctionName} | awk -F ' ' '{print $3}') ; docker tag $image ${local.fn_image}"
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    command     = "docker push ${local.fn_image}"
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

}
