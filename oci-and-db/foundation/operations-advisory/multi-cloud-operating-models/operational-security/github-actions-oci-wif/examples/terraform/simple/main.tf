terraform {
  backend "local" {}

  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "9.8.0"
    }
  }
}

provider "oci" {
  auth   = "WorkloadIdentityFederation"
  region = var.region
}

variable "region" {
  type = string
}

variable "compartment_id" {
  type = string
}

variable "bucket_name" {
  type = string
}

data "oci_objectstorage_namespace" "this" {}

resource "oci_objectstorage_bucket" "demo" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = var.bucket_name
  access_type    = "NoPublicAccess"
}

output "namespace" {
  value = data.oci_objectstorage_namespace.this.namespace
}
