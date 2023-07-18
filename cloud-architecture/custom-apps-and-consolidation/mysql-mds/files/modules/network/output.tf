# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to define output data required from resources created in this module
# @author: Vijay Kokatnur

output "snevndtmdb_id" {
    value = oci_core_subnet.snevndtmdb.id
}