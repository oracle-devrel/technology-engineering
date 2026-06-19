#######################################
# Network Security Group for Container Instance Monitoring
# Provides secure access from specific IP addresses
#######################################

locals {
  # Security rules for different deployment scenarios
  common_egress_rules = [
    {
      description = "Allow all outbound traffic"
      protocol    = "all"
      destination = "0.0.0.0/0"
      stateless   = false
    }
  ]

  # Ingress rules for container instance
  container_ingress_rules = [
    {
      description = "HTTP access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 80
      port_max    = 80
      stateless   = false
    },
    {
      description = "HTTPS access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 443
      port_max    = 443
      stateless   = false
    },
    {
      description = "cAdvisor metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 8080
      port_max    = 8080
      stateless   = false
    },
    {
      description = "Node Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9100
      port_max    = 9100
      stateless   = false
    },
    {
      description = "Prometheus metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9090
      port_max    = 9090
      stateless   = false
    },
    {
      description = "Grafana web interface from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 3000
      port_max    = 3000
      stateless   = false
    },
    {
      description = "Nginx Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9113
      port_max    = 9113
      stateless   = false
    },
    {
      description = "Blackbox Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9115
      port_max    = 9115
      stateless   = false
    },
    {
      description = "MySQL Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9104
      port_max    = 9104
      stateless   = false
    },
    {
      description = "Redis Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9121
      port_max    = 9121
      stateless   = false
    },
    {
      description = "PostgreSQL Exporter metrics from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9187
      port_max    = 9187
      stateless   = false
    }
  ]

  # Ingress rules for monitoring VM
  vm_ingress_rules = [
    {
      description = "SSH access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 22
      port_max    = 22
      stateless   = false
    },
    {
      description = "Grafana access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 3000
      port_max    = 3000
      stateless   = false
    },
    {
      description = "Prometheus access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 9090
      port_max    = 9090
      stateless   = false
    },
    {
      description = "HTTP access from allowed IPs"
      protocol    = "6" # TCP
      source      = var.allowed_cidr
      port_min    = 80
      port_max    = 80
      stateless   = false
    }
  ]
}

#######################################
# NSG for Container Instances
#######################################
resource "oci_core_network_security_group" "container_nsg" {
  count = var.create_container_nsg ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_ocid
  display_name   = "${var.resource_prefix}-container-nsg"

  freeform_tags = var.freeform_tags
  defined_tags  = var.defined_tags
}

# Ingress rules for container NSG
resource "oci_core_network_security_group_security_rule" "container_ingress" {
  count = var.create_container_nsg ? length(local.container_ingress_rules) : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = local.container_ingress_rules[count.index].protocol
  source                    = local.container_ingress_rules[count.index].source
  source_type               = "CIDR_BLOCK"
  stateless                 = local.container_ingress_rules[count.index].stateless
  description               = local.container_ingress_rules[count.index].description

  tcp_options {
    destination_port_range {
      min = local.container_ingress_rules[count.index].port_min
      max = local.container_ingress_rules[count.index].port_max
    }
  }
}

# Egress rules for container NSG
resource "oci_core_network_security_group_security_rule" "container_egress" {
  count = var.create_container_nsg ? length(local.common_egress_rules) : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "EGRESS"
  protocol                  = local.common_egress_rules[count.index].protocol
  destination               = local.common_egress_rules[count.index].destination
  destination_type          = "CIDR_BLOCK"
  stateless                 = local.common_egress_rules[count.index].stateless
  description               = local.common_egress_rules[count.index].description
}

#######################################
# NSG for Monitoring VM
#######################################
resource "oci_core_network_security_group" "monitoring_vm_nsg" {
  count = var.create_vm_nsg ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_ocid
  display_name   = "${var.resource_prefix}-monitoring-vm-nsg"

  freeform_tags = var.freeform_tags
  defined_tags  = var.defined_tags
}

# Ingress rules for VM NSG
resource "oci_core_network_security_group_security_rule" "vm_ingress" {
  count = var.create_vm_nsg ? length(local.vm_ingress_rules) : 0

  network_security_group_id = oci_core_network_security_group.monitoring_vm_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = local.vm_ingress_rules[count.index].protocol
  source                    = local.vm_ingress_rules[count.index].source
  source_type               = "CIDR_BLOCK"
  stateless                 = local.vm_ingress_rules[count.index].stateless
  description               = local.vm_ingress_rules[count.index].description

  tcp_options {
    destination_port_range {
      min = local.vm_ingress_rules[count.index].port_min
      max = local.vm_ingress_rules[count.index].port_max
    }
  }
}

# Egress rules for VM NSG
resource "oci_core_network_security_group_security_rule" "vm_egress" {
  count = var.create_vm_nsg ? length(local.common_egress_rules) : 0

  network_security_group_id = oci_core_network_security_group.monitoring_vm_nsg[0].id
  direction                 = "EGRESS"
  protocol                  = local.common_egress_rules[count.index].protocol
  destination               = local.common_egress_rules[count.index].destination
  destination_type          = "CIDR_BLOCK"
  stateless                 = local.common_egress_rules[count.index].stateless
  description               = local.common_egress_rules[count.index].description
}

#######################################
# Additional rules: Allow VM to scrape metrics from containers
#######################################

# Allow VM to scrape cAdvisor metrics (port 8080) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_cadvisor" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape cAdvisor metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 8080
      max = 8080
    }
  }
}

# Allow VM to scrape Node Exporter metrics (port 9100) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_node_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape Node Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9100
      max = 9100
    }
  }
}

# Allow VM to scrape Nginx Exporter metrics (port 9113) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_nginx_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape Nginx Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9113
      max = 9113
    }
  }
}

# Allow VM to scrape Blackbox Exporter metrics (port 9115) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_blackbox_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape Blackbox Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9115
      max = 9115
    }
  }
}

# Allow VM to scrape MySQL Exporter metrics (port 9104) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_mysql_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape MySQL Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9104
      max = 9104
    }
  }
}

# Allow VM to scrape Redis Exporter metrics (port 9121) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_redis_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape Redis Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9121
      max = 9121
    }
  }
}

# Allow VM to scrape PostgreSQL Exporter metrics (port 9187) from containers
resource "oci_core_network_security_group_security_rule" "vm_to_container_postgres_exporter" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.container_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.monitoring_vm_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus to scrape PostgreSQL Exporter metrics from Monitoring VM"

  tcp_options {
    destination_port_range {
      min = 9187
      max = 9187
    }
  }
}

# Legacy rule: Allow container to VM communication (port 9090)
# This is for backward compatibility with app-level Prometheus exporters
resource "oci_core_network_security_group_security_rule" "container_to_vm" {
  count = var.create_vm_nsg && var.create_container_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.monitoring_vm_nsg[0].id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = oci_core_network_security_group.container_nsg[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow Prometheus scraping from container instances"

  tcp_options {
    destination_port_range {
      min = 9090
      max = 9090
    }
  }
}
