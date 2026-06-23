variable tenancy_ocid {}
variable region {}
variable compartment_name {}
variable bucket_name {}
variable vcn_name {}
variable public_subnet_name {}
variable command_server_name {
  description = "the name of the command server"
  type        = string
  default     = "command"
}
variable zone_name {
  description = "the DNS domain"
  type        = string
  default     = "katogana.de"
}
variable rpiconnect_name {
  description = "DNS name of server which is queried by raspberrys"
  type        = string
  default     = "rpiconnect"
}

#variable vcn_id {}
#variable compartment_id {}

variable "instances" {
  type = map(object({
    os    = string,
    arch  = string,
    osmh  = bool,
    phase = string
  }))
  default = {}
#  default = {
#     "ol8amd" = { os= "OracleLinux8", arch="amd", osmh=false, phase="development"}
#     "ol8arm" = { os= "OracleLinux8", arch="arm", osmh=false, phase="development"}
#     "ol8x86" = { os= "OracleLinux8", arch="x86", osmh=false, phase="development"}
#     "ol9amd" = { os= "OracleLinux9", arch="amd", osmh=false, phase="development"}
#     "ol9arm" = { os= "OracleLinux9", arch="arm", osmh=false, phase="development"}
#     "ol9x86" = { os= "OracleLinux9", arch="x86", osmh=false, phase="development"}
#    "ol10amd" = { os="OracleLinux10", arch="amd", osmh=false, phase="development"}
#    "ol10arm" = { os="OracleLinux10", arch="arm", osmh=false, phase="development"}
#    "ol10x86" = { os="OracleLinux10", arch="x86", osmh=false, phase="development"}
#  }
}

