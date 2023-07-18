# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to define local variables.
# @author: Vijay Kokatnur

locals {
  all_protocols = "all"

  anywhere = "0.0.0.0/0"

  ssh_port = 22

  tcp_protocol = 6

}
