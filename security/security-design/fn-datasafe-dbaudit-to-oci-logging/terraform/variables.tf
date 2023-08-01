###############################################################################
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl.
###############################################################################
#
# Author: Fabrizio Zarri
#
################################################################################

variable "tenancy_ocid" {}

#comment for stack zip file
variable "user_ocid" {
  default =""
}
#comment for stack zip file
variable "fingerprint" {
  default =""
}
#comment for stack zip file
variable "private_key_path" {
  default =""
}

variable "compartment_ocid" {}
variable "region" {}
variable "ocir_user_name" {}
variable "ocir_user_password" {}

variable "purpose" {
  default ="fn_ds_to_ol"
}


variable "deployment_name" {
    default = "test"
}


variable "release" {
  description = "Reference Data Safe DB Audit Log Exporter Release (OCI Logging)"
  default     = "1.0.0"
}

variable "ocir_repo_name" {
  default = "rep"
}

variable "setup_policies" {
  default = true
}

###################################
# Bucket Variables
###################################
variable "tracker-bucket" {
  default = "bkt"
}

###################################
# Network Variables
###################################

variable "subnet_ocid" {
  default = "replace"
}
variable "create_network" {
  default = true
}
variable "vcn_cidr" {
  default = "10.0.0.0/22"
  description = "The cidr block of VCN"
}

variable "subnet_cidr" {
  default = "10.0.1.0/24"
}

variable "vcndnslabelprefix" {
  default = "dnsepl"
}

variable "vcnnameprefix" {
  default = "vnc"
  description = "The prefix display name of VCN"
}

variable "vcnnameroutingtableprefix" {
  default = "rt"
}

variable "vcnroutingtabledescriptionservicegw" {
  default = "Route for Service Gateway"
}

variable "vcnnamedhcpopitonsprefix" {
  default = "dhcpo"
}

variable "subnetnameprefix" {
  default = "sub"
}

variable "subnetdnslabelprefix" {
  default = "dnsepl"
}

variable "vcnnamesecuritylistprefix" {
  default = "sl"
}
variable "vcnnameservicegatewayprefix" {
  default = "sgw"
}



###################################
# Policies Variables
###################################
variable "policynameprefix" {
  default = "pcy"
}

variable "policydescription" {
  default = "Data Safe to Logging Function Policy"
}

variable "dynamicgroupnameprefix" {
  default = "dgp"
}
variable "DynamicGroupDescription" {
  default = "Dynamic Group for function to manage DataSafe DB Audit to OCI Logging"
}

###################################
# Functions Variables
###################################
variable "functionappnameprefix" {
  default = "funApp"
}

variable "functionnameprefix" {
  default = "fun"
}

variable "functionmemory" {
  default = "1024"
}

variable "functioninvokeociloggingname" {
  default = "fn-datasafe-dbaudit"
}

variable "functiontimeoutsec" {
  default = "300"
}

variable "functionname" {
  default = "oci-datasafe-audit-to-logging"
}


###################################
# Logging Variables
###################################
variable "loggrouprefix" {
  default = "loggr"
}

variable "log_datafafeauditdbnameprefix" {
  default = "log"
}

###################################
# Notification Variables
###################################
variable "notificationtopicnameprefix" {
  default = "not"
}

variable "alarmnameprefix" {
  default = "alm"
}
