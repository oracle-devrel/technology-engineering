###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
###############################################################################

resource "null_resource" "FunctionInvoke" {
  depends_on = [oci_functions_function.fun1]
  
  provisioner "local-exec" {
    command     = "fn invoke ${oci_functions_application.FunctionApp.display_name} ${oci_functions_function.fun1.display_name}"
    working_dir = local.fn_working_dir
  }


}