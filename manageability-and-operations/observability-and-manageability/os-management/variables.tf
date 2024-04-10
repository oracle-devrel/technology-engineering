variable "tenancy_ocid" {}
variable "region" {
  type = string
}
variable "compartment_ocid" {
  type = string
  description = "all resources are created in this compartment"
}
variable "availability_domain_name" {
  type = string
  description = "value set by OCI Resource Manager"
}
variable "oci_profile_name" {
  description = "name of the profile in ~/.oci/config"
  default      = "DEFAULT"
}
# availability_domain_name is used with OCI Resource Manager instead
#variable "availability_domain" {
#  description = "the availability domain referenced by a number. Range is 1..<number of ADs in region>."
#  type = string
#  default = "3"
#  validation {
#    condition = contains(["1","2","3"],var.availability_domain)
#    error_message = "The availability_domain is out of range."
#  }
#}
variable "ignore_defined_tags" {
  description = "Ignore Tags not added by Terraform"
  type = list(string)
  default = []
}
variable "gi_state" {
  description = "The lifecycle state of Golden Instances"
  type = string
  default = "RUNNING"
}
variable "mi_state" {
  type = string
  description = "The lifecycle state of Managed Instances"
  default = "RUNNING"
}
variable "shape" {
  type = string
  default = "VM.Standard3.Flex"
}
variable "defined_tags" {
  description = "defined_tags for compute intances"
  type = map
}
variable "ssh_public_key" {
  description = "public SSH"
  type = string
  default = ""
}
variable "vcndef" {
  description = "basic parameters for a VCN with subnets"
  type = object({
    name = string
    cidr = list(string)
    subnets = map(object({
      name = string
      cidr = string
      private = bool
    }))
  })
}
variable "golden_instances" {
  type = list(object({
    name   = string,
    os     = string,
    subnet = string,
    state  = string
  }))
  default = [
    {name = "OL8GoldenInstance1", os = "OracleLinux8", subnet = "public", state = "RUNNING"},
    {name = "OL8GoldenInstance2", os = "OracleLinux8", subnet = "public", state = "RUNNING"},
    {name = "OL9GoldenInstance1", os = "OracleLinux9", subnet = "public", state = "RUNNING"},
    {name = "OL9GoldenInstance2", os = "OracleLinux9", subnet = "public", state = "RUNNING"},
  ]
}
variable "servers" {
  type = list(object({
    group  = string,
    name   = string,
    os     = string,
    subnet = string,
    state  = string,
    count  = number
  }))
  default = [
    {group = "OracleLinux8_ManagedInstanceGroup1",  name = "Tokyo8",      os = "OracleLinux8", subnet = "public", state="RUNNING", count = 4},
    {group = "OracleLinux8_ManagedInstanceGroup2",  name = "Toronto8",    os = "OracleLinux8", subnet = "public", state="RUNNING", count = 3},
    {group = "OracleLinux9_ManagedInstanceGroup1",  name = "NewYork9",    os = "OracleLinux9", subnet = "public", state="RUNNING", count = 2},
    {group = "OracleLinux9_ManagedInstanceGroup2",  name = "London9",     os = "OracleLinux9", subnet = "public", state="RUNNING", count = 2},
    {group = "Windows_ManagedInstanceGroup",        name = "Windows2019", os = "Windows2019",  subnet = "public", state="RUNNING", count = 0},
  ]
}

variable "python_update_software_source_script_path" {
  description = "Terraform will generate the python script at this path"
  type = string
  default = "./python/update_software_source.py"
}
variable "python_update_instances_script_path" {
  description = "Terraform will generate the python script at this path"
  type = string
  default = "./python/update_instances.py"
}
variable "bash_update_software_sources_script_path" {
  description = "Terraform will generate the bash script at this path"
  type = string
  default = "./bash_update_software_sources.bash"
}

variable "mig1_name" {
  type        = string
  description = "name of Managed Instance Group 1"
}
variable "mig1_miname" {
  type        = string
  description = "base name for Managed Intances in Managed Instance Group"
}
variable "mig1_os" {
  type        = string
  description = "OS for Managed Instances in Managed Instance Group"
}
variable "mig1_count" {
  type        = number
  description = "number of Managed Instances in Managed Instance Group"
}

variable "mig2_name" {
  type        = string
  description = "name of Managed Instance Group 2"
}
variable "mig2_miname" {
  type        = string
  description = "base name for Managed Intances in Managed Instance Group"
}
variable "mig2_os" {
  type        = string
  description = "OS for Managed Instances in Managed Instance Group"
}
variable "mig2_count" {
  type        = number
  description = "number of Managed Instances in Managed Instance Group"
}

variable "mig3_name" {
  type        = string
  description = "name of Managed Instance Group 3"
}
variable "mig3_miname" {
  type        = string
  description = "base name for Managed Intances in Managed Instance Group"
}
variable "mig3_os" {
  type        = string
  description = "OS for Managed Instances in Managed Instance Group"
}
variable "mig3_count" {
  type        = number
  description = "number of Managed Instances in Managed Instance Group"
}

variable "mig4_name" {
  type        = string
  description = "name of Managed Instance Group 4"
}
variable "mig4_miname" {
  type        = string
  description = "base name for Managed Intances in Managed Instance Group"
}
variable "mig4_os" {
  type        = string
  description = "OS for Managed Instances in Managed Instance Group"
}
variable "mig4_count" {
  type        = number
  description = "number of Managed Instances in Managed Instance Group"
}
