variable "compartment_ocid" {
  type = string

}

variable "tenancy_ocid" {
  type = string

}

variable "subnet_ocid" {
  type = string

}

variable "sidecar_image" {
  type = string
}

variable "ad_number" {
  type    = number
  default = 1

}

variable "log_ocid" {
  type    = string

}

variable "log_mount_path" {
  type    = string
  default = "/var/log/nginx"
}

variable "log_mount_name" {
  type    = string
  default = "nginxlogs"
}

variable "log_file" {
  type    = string
  default = "access.log"
}

variable "www_mount_path" {
  type    = string
  default = "/usr/share/nginx/html"
}

variable "www_mount_name" {
  type    = string
  default = "nginxdata"
}

variable "www_data_bucket" {
  type    = string
}

