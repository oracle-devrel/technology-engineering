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


variable "compartment_ocid" {
  description = "the OCID of the compartment where the environment will be created."
}

variable "VCN-CIDR" {
  default = "10.0.0.0/22"
  description = "The CIDR block of VCN"
}

variable "fnsubnet-CIDR" {
  default = "10.0.1.0/24"
}

variable "fnvcndnslabelprefix" {
  default = "fndslogvcn"
}

variable "fnvcnnameprefix" {
  default = "vcn_fn_ds_log-fndslog"
  description = "The prefix display name of VCN"
}

variable "fnvcnnameroutingtableprefix" {
  default = "function_ds_log_vcn_routetable"
}

variable "fnvcnroutingtabledescriptionervicegw" {
  default = "Route for Service Gateway"
}

variable "fnvcnnamedhcpopitonsprefix" {
  default = "function_ds_log_vcn_dhcpoptions1"
}

variable "fnsubnetnameprefix" {
  default = "private_fn_ds_log_vcn_subnet"
}

variable "fnsubnetdnslabelprefix" {
  default = "fndslogsub"
}

variable "fnvcnnamesecuritylistprefix" {
  default = "functions-security-list"
}
variable "fnvcnnameservicegatewayprefix" {
  default = "function_ds_log_vcn_sg"
}
