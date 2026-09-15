output "private_ips" {
  value =  module.containerinstance.private_ips
}

output "public_ip_lb" {
  value = module.loadbalancer.public_ip_lb
}