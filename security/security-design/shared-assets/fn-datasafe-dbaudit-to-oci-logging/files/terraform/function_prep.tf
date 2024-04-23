###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
###############################################################################



resource "null_resource" "functionapp_push2ocir" {
  depends_on = [module.setup-network, oci_objectstorage_bucket.tracker-bucket, oci_identity_policy.functionpolicy,
    oci_artifacts_container_repository.fn_container_repository, oci_functions_application.functionapp]
  
  provisioner "local-exec" {
    command = "echo '${var.ocir_user_password}' |  docker login ${local.ocir_docker_repository} --username '${local.namespace}/${var.ocir_user_name}' --password-stdin"
  }
  provisioner "local-exec" {
    command     = "image=$(docker images | grep ${var.functionname} | awk -F ' ' '{print $3}') ; docker rmi -f $image &> /dev/null ; echo $image"
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    #command     = "fn build --verbose"
    command     = "docker buildx build --platform linux/arm64/v8,linux/amd64 ${path.module}/${local.fn_working_dir}"
    working_dir ="${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    command     = "image=$(docker images | grep ${var.functionname} | awk -F ' ' '{print $3}') ; docker tag $image ${local.fn_image}"
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

  provisioner "local-exec" {
    command     = "docker manifest push ${local.fn_image}" 
    working_dir = "${path.module}/${local.fn_working_dir}"
  }

}
