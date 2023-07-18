# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform provider and version definition.
# @author: Vijay Kokatnur

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.67.3"
      # pass oci home region provider explicitly for identity operations
      configuration_aliases = [oci.home]
    }
  }
  required_version = ">= 1.0.0"
}

provider "oci" {
  alias             = "home"
}