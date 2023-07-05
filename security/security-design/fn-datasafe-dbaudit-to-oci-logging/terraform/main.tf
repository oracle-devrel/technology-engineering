################################################################################
#Copyright (c) 2023 Oracle and/or its affiliates.
# 
#The Universal Permissive License (UPL), Version 1.0
# 
#Subject to the condition set forth below, permission is hereby granted to any
#person obtaining a copy of this software, associated documentation and/or data
#(collectively the "Software"), free of charge and under any and all copyright
#rights in the Software, and any and all patent rights owned or freely
#licensable by each licensor hereunder covering either (i) the unmodified
#Software as contributed to or provided by such licensor, or (ii) the Larger
#Works (as defined below), to deal in both
# 
#(a) the Software, and
#(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
#one is included with the Software (each a "Larger Work" to which the Software
#is contributed by such licensors),
 
#without restriction, including without limitation the rights to copy, create
#derivative works of, display, perform, and distribute the Software and make,
#use, sell, offer for sale, import, export, have made, and have sold the
#Software and the Larger Work(s), and to sublicense the foregoing rights on
#either these or other terms.
 
#This license is subject to the following condition:
#The above copyright notice and either this complete permission notice or at
#a minimum a reference to the UPL must be included in all copies or
#substantial portions of the Software.
 
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
################################################################################

resource "null_resource" "Login2OCIR" {
  depends_on = [module.setup-network, oci_objectstorage_bucket.tracker-bucket, oci_identity_policy.DataSafetoLoggingFunctionsPolicy,
    oci_artifacts_container_repository.fn_container_repository, oci_functions_application.DataSafeAuditDBtoLoggingApp]
 

  provisioner "local-exec" {
    command = "echo '${var.ocir_user_password}' |  docker login ${local.ocir_docker_repository} --username ${local.namespace}/${var.ocir_user_name} --password-stdin"
  }
}

resource "null_resource" "DataSafeAuditDBtoLoggingPush2OCIR" {
  depends_on = [null_resource.Login2OCIR, oci_functions_application.DataSafeAuditDBtoLoggingApp]

  provisioner "local-exec" {
    command     = "image=$(docker images | grep oci-datasafe-audit-to-logging | awk -F ' ' '{print $3}') ; docker rmi -f $image &> /dev/null ; echo $image"
    working_dir = "function/oci-datasafe-audit-to-logging"
  }

  provisioner "local-exec" {
    command     = "fn build --verbose"
    working_dir = "function/oci-datasafe-audit-to-logging"
  }

  provisioner "local-exec" {
    command     = "image=$(docker images | grep oci-datasafe-audit-to-logging | awk -F ' ' '{print $3}') ; docker tag $image ${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}/oci-datasafe-audit-to-logging:0.0.1"
    working_dir = "function/oci-datasafe-audit-to-logging"
 }

  provisioner "local-exec" {
    command     = "docker push ${local.ocir_docker_repository}/${local.namespace}/${oci_artifacts_container_repository.fn_container_repository.display_name}/oci-datasafe-audit-to-logging:0.0.1"
    working_dir = "function/oci-datasafe-audit-to-logging"
 }
}

module "setup-network" {
  source = "./modules/network"
  count  = var.create_network ? 1 : 0
  compartment_ocid = var.compartment_ocid
  VCN-CIDR = var.VCN-CIDR
  fnsubnet-CIDR = var.fnsubnet-CIDR
}
