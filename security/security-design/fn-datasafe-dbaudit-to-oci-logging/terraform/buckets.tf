################################################################################
# Copyright (c) 2023, Oracle and/or its affiliates. All rights reserved.
# This software is dual-licensed to you under the Universal Permissive 
# License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl
################################################################################


data "oci_objectstorage_namespace" "bucket_namespace" {
  compartment_id = var.compartment_ocid
}

resource "oci_objectstorage_bucket" "tracker-bucket" {
  compartment_id        = var.compartment_ocid
  name                  = "${var.tracker-bucket}-${var.deployment_name}-${random_id.tag.hex}"
  namespace             = data.oci_objectstorage_namespace.bucket_namespace.namespace

}
