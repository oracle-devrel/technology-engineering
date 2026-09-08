variable "compartment_ocid" {
    description = "The OCI Compartment ocid"
    type        = string
}

variable "public_subnet_ocid" {
    description = "The OCI Public Subnet ocid"
    type        = string
}

variable "load_balancer_shape_details_maximum_bandwidth_in_mbps" {
    description = "The OCI LB Max Bandwith"  
    type        = number
    default = 100
}

variable "load_balancer_shape_details_minimum_bandwidth_in_mbps" {
    description = "The OCI LB Max Bandwith"  
    type = number
    default = 10
}

variable "private_ips" {
    description = "The OCI List of Container Instance Private IP Address "
    type        = list
}

variable "lb_name" {
    description = "The OCI LB Name"
    type        = string
    default     = "CI_TRANSLATOR_LB"
}


variable "lb_checker_health_port" {
    description = "The OCI LB Health Checker Port"
    type        = string
    default     = "8000"
}

variable "lb_checker_url_path" {
    description = "The OCI LB Health Checker URL"
    type        = string
    default     = "/actuator/health"
}

variable "lb_listener_port" {
    description = "The OCI LB Listener Port"
    type        = number
    default     = 8000
}

variable "lb_backend_port" {
    description = "The OCI LB Backend Port"
    type        = number
    default     = 8000
}

resource "oci_load_balancer" "flex_lb" {
  shape          = "flexible"
  compartment_id = var.compartment_ocid
  is_private = false

  subnet_ids = [
    var.public_subnet_ocid
  ]

  shape_details {
    #Required
    maximum_bandwidth_in_mbps = var.load_balancer_shape_details_maximum_bandwidth_in_mbps
    minimum_bandwidth_in_mbps = var.load_balancer_shape_details_minimum_bandwidth_in_mbps
  }

  display_name = var.lb_name
}

resource "oci_load_balancer_backend_set" "lb-bes1" {
  name             = "lb-bes1"
  load_balancer_id = oci_load_balancer.flex_lb.id
  policy           = "ROUND_ROBIN"

  health_checker {
    port                = var.lb_checker_health_port
    protocol            = "HTTP"
    response_body_regex = ".*"
    url_path            = var.lb_checker_url_path
  }
}

resource "oci_load_balancer_backend" "lb-be1" {
  count = length(var.private_ips)  
  load_balancer_id = oci_load_balancer.flex_lb.id
  backendset_name  = oci_load_balancer_backend_set.lb-bes1.name
  ip_address       = element(var.private_ips, count.index)
  port             = var.lb_backend_port
  backup           = false
  drain            = false
  offline          = false
  weight           = 1
}

resource "oci_load_balancer_listener" "lb-listener1" {
  load_balancer_id         = oci_load_balancer.flex_lb.id
  name                     = "http"
  default_backend_set_name = oci_load_balancer_backend_set.lb-bes1.name
  port                     = var.lb_listener_port
  protocol                 = "HTTP"

  connection_configuration {
    idle_timeout_in_seconds = "60"
  }
}