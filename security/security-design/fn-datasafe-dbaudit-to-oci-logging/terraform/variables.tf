################################################################################
# Copyright (c) 2023, Oracle and/or its affiliates. All rights reserved.
# This software is dual-licensed to you under the Universal Permissive 
# License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl
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

variable "deployment_name" {
    default = "test"
}


variable "release" {
  description = "Reference Data Safe DB Audit Log Exporter Release (OCI Logging)"
  default     = "1.0.0"
}

variable "ocir_repo_name" {
  default = "oci-datasafe-audit-to-logging"
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
variable "VCN-CIDR" {
  default = "10.0.0.0/22"
  description = "The CIDR block of VCN"
}

variable "fnsubnet-CIDR" {
  default = "10.0.1.0/24"
}

variable "fnvcndnslabelprefix" {
  default = "dnsepl"
}

variable "fnvcnnameprefix" {
  default = "vnc"
  description = "The prefix display name of VCN"
}

variable "fnvcnnameroutingtableprefix" {
  default = "rt"
}

variable "fnvcnroutingtabledescriptionservicegw" {
  default = "Route for Service Gateway"
}

variable "fnvcnnamedhcpopitonsprefix" {
  default = "dhcpo"
}

variable "fnsubnetnameprefix" {
  default = "sub"
}

variable "fnsubnetdnslabelprefix" {
  default = "dnsepl"
}

variable "fnvcnnamesecuritylistprefix" {
  default = "sl"
}
variable "fnvcnnameservicegatewayprefix" {
  default = "sgw"
}



###################################
# Policies Variables
###################################
variable "PolicyNamePrefix" {
  default = "pcy"
}

variable "PolicyDescription" {
  default = "Data Safe to Logging Function Policy"
}

variable "DynamicGroupNamePrefix" {
  default = "dgp"
}
variable "DynamicGroupDescription" {
  default = "Dynamic Group for function to manage DataSafe DB Audit to OCI Logging"
}

###################################
# Functions Variables
###################################
variable "FunctionAppNamePrefix" {
  default = "funApp"
}

variable "FunctionNamePrefix" {
  default = "funName"
}

variable "FunctionMemory" {
  default = "1024"
}

variable "FunctionInvokeOCILoggingName" {
  default = "fn-datasafe-dbaudit"
}

variable "FunctionTimeoutSec" {
  default = "300"
}


###################################
# Logging Variables
###################################
variable "LogGroupPrefix" {
  default = "loggr"
}

variable "LogDataSafeAuditDBNamePrefix" {
  default = "log"
}

###################################
# Notification Variables
###################################
variable "NotificationTopicNamePrefix" {
  default = "not"
}

variable "AlarmNamePrefix" {
  default = "alm"
}
