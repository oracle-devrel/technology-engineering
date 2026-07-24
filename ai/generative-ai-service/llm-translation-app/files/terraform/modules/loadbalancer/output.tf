output "public_ip_lb" {
  value =  oci_load_balancer.flex_lb.ip_address_details
}
