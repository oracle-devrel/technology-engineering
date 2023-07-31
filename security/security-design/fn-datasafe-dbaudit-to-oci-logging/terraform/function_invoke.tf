###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
###############################################################################

provisioner "local-exec" {
    depends_on = [oci_functions_function.fun1]
    command = "sleep 60"
  }

resource "oci_functions_invoke_function" "FunctionInvoke" {
    function_id = oci_functions_function.fun1.id
}