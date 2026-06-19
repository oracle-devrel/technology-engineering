#######################################
# OCI Container Instance Module
# Creates and configures Container Instances with monitoring
#######################################

# Random password for Management Agent credential wallet
resource "random_password" "mgmt_agent_wallet_password" {
  count   = var.enable_management_agent_sidecar ? 1 : 0
  length  = 16
  special = true
  override_special = "!@#$%^&*"
}

# Get availability domain
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

locals {
  # Select availability domain based on input
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[var.availability_domain - 1].name

  # Image pull secret (if using private OCIR)
  use_image_pull_secret = var.ocir_username != "" && var.ocir_auth_token != ""

  # Calculate total exporter resource overhead
  # Base exporters (cAdvisor + Node Exporter): 0.8GB, 0.2 OCPU
  # Optional exporters: calculated based on enabled flags
  exporter_memory_overhead = (
    var.enable_prometheus_exporters ? 0.8 : 0.0  # cAdvisor + Node Exporter
  ) + (
    var.enable_nginx_exporter ? 0.1 : 0.0
  ) + (
    var.enable_redis_exporter ? 0.1 : 0.0
  ) + (
    var.enable_postgres_exporter ? 0.15 : 0.0
  ) + (
    var.enable_mysql_exporter ? 0.15 : 0.0
  ) + (
    var.enable_blackbox_exporter ? 0.1 : 0.0
  )

  exporter_cpu_overhead = (
    var.enable_prometheus_exporters ? 0.2 : 0.0  # cAdvisor + Node Exporter
  ) + (
    var.enable_nginx_exporter ? 0.05 : 0.0
  ) + (
    var.enable_redis_exporter ? 0.05 : 0.0
  ) + (
    var.enable_postgres_exporter ? 0.05 : 0.0
  ) + (
    var.enable_mysql_exporter ? 0.05 : 0.0
  ) + (
    var.enable_blackbox_exporter ? 0.05 : 0.0
  )

  # Application resources = Total - Exporter overhead
  app_memory_gb = var.container_memory_gb - local.exporter_memory_overhead
  app_ocpus = var.container_ocpus - local.exporter_cpu_overhead
}

#######################################
# Image Pull Secret (for private OCIR images)
# Note: Disabled to avoid conflicts with existing repositories
# Using direct OCIR authentication via image_pull_secrets instead
#######################################
resource "oci_artifacts_container_repository" "image_pull_secret" {
  count          = 0  # Disabled - using direct OCIR authentication
  compartment_id = var.compartment_ocid
  display_name   = "${var.container_instance_name}-secret"
  is_public      = false

  freeform_tags = var.freeform_tags
}

#######################################
# Container Instance
#######################################
resource "oci_container_instances_container_instance" "main" {
  compartment_id      = var.compartment_ocid
  availability_domain = local.availability_domain
  display_name        = var.container_instance_name

  # Shape configuration
  shape = var.container_shape
  shape_config {
    ocpus         = var.container_ocpus
    memory_in_gbs = var.container_memory_gb
  }

  # VCN configuration
  vnics {
    subnet_id = var.subnet_ocid

    # Public IP assignment
    is_public_ip_assigned = var.assign_public_ip

    # Network Security Groups
    nsg_ids = var.nsg_ocids

    # Skip source/destination check for container networking
    skip_source_dest_check = true
  }

  # Graceful shutdown timeout
  graceful_shutdown_timeout_in_seconds = 30

  # DNS configuration
  dns_config {
    nameservers = ["169.254.169.254"]
  }

  # Main Application Container
  containers {
    display_name = "${var.container_instance_name}-app"
    image_url    = var.container_image

    # Command to redirect stdout/stderr to log file for log forwarder
    # Starts the default application and redirects all output to log file using tee
    # This preserves both stdout (for container logs) and writes to shared volume
    command = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [
      "/bin/sh",
      "-c",
      <<-EOT
        # Create log file if it doesn't exist
        touch /logs/application.log
        # Start metrics generator in background
        /usr/local/bin/generate-metrics.sh 2>&1 | tee -a /logs/application.log &
        # Start nginx and redirect logs to file
        exec nginx -g 'daemon off;' 2>&1 | tee -a /logs/application.log
      EOT
    ] : null

    # Environment variables (as map)
    environment_variables = var.container_env_vars

    # Resource limits - allocate resources to app container
    # Application gets: Total resources - Exporter overhead (calculated dynamically)
    # Exporter overhead depends on which exporters are enabled
    resource_config {
      memory_limit_in_gbs = local.app_memory_gb
      vcpus_limit         = local.app_ocpus
    }

    # Health check
    health_checks {
      health_check_type = "HTTP"
      port              = var.container_port
      path              = var.health_check_path
      interval_in_seconds = 30
      timeout_in_seconds  = 10
      failure_threshold   = 3
    }

    # Shared volume mounts for sidecar pattern
    dynamic "volume_mounts" {
      for_each = var.enable_shared_volumes ? [1] : []
      content {
        mount_path  = "/metrics"
        volume_name = "metrics-volume"
        is_read_only = false
      }
    }

    dynamic "volume_mounts" {
      for_each = var.enable_shared_volumes ? [1] : []
      content {
        mount_path  = "/logs"
        volume_name = "logs-volume"
        is_read_only = false
      }
    }

    # Additional volume mounts (user-defined)
    dynamic "volume_mounts" {
      for_each = var.volume_mounts
      content {
        mount_path  = volume_mounts.value.mount_path
        volume_name = volume_mounts.value.volume_name
        is_read_only = lookup(volume_mounts.value, "is_read_only", false)
      }
    }
  }

  # cAdvisor Container - Collects container metrics (Docker monitoring)
  # Exposes metrics on port 8080 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_prometheus_exporters ? [1] : []
    content {
      display_name = "${var.container_instance_name}-cadvisor"
      image_url    = "gcr.io/cadvisor/cadvisor:latest"

      # Command to redirect stdout/stderr to log file for log forwarder
      command = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [
        "/bin/sh",
        "-c",
        <<-EOT
          # Create log file if it doesn't exist
          touch /logs/cadvisor.log
          # Redirect stderr to stdout and pipe through tee to log file
          exec 2>&1
          # Run cadvisor with arguments and tee output to log file
          /usr/bin/cadvisor --port=8080 --housekeeping_interval=10s --docker_only=true --store_container_labels=false 2>&1 | tee -a /logs/cadvisor.log
        EOT
      ] : null

      # cAdvisor command arguments (used when log redirection is disabled)
      arguments = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [] : [
        "--port=8080",
        "--housekeeping_interval=10s",
        "--docker_only=true",
        "--store_container_labels=false"
      ]

      # Resource limits - minimal resources for cAdvisor
      resource_config {
        memory_limit_in_gbs = 0.5
        vcpus_limit         = 0.1
      }

      # Health check for cAdvisor
      health_checks {
        health_check_type = "HTTP"
        port              = 8080
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }

      # Shared volume mount for log forwarding
      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes && var.enable_log_forwarder_sidecar ? [1] : []
        content {
          mount_path  = "/logs"
          volume_name = "logs-volume"
          is_read_only = false
        }
      }
    }
  }

  # Node Exporter Container - Collects host/node metrics
  # Exposes metrics on port 9100 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_prometheus_exporters ? [1] : []
    content {
      display_name = "${var.container_instance_name}-node-exporter"
      image_url    = "prom/node-exporter:latest"

      # Command to redirect stdout/stderr to log file for log forwarder
      command = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [
        "/bin/sh",
        "-c",
        <<-EOT
          # Create log file if it doesn't exist
          touch /logs/node-exporter.log
          # Redirect stderr to stdout and pipe through tee to log file
          exec 2>&1
          # Run node_exporter WITHOUT host paths (not available in OCI Container Instances)
          # This will collect container-level metrics only
          /bin/node_exporter 2>&1 | tee -a /logs/node-exporter.log
        EOT
      ] : null

      # Node exporter arguments (used when log redirection is disabled)
      arguments = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [] : [
        "--path.rootfs=/host",
        "--path.procfs=/host/proc",
        "--path.sysfs=/host/sys",
        "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
      ]

      # Resource limits - minimal resources for node exporter
      resource_config {
        memory_limit_in_gbs = 0.3
        vcpus_limit         = 0.1
      }

      # Health check for Node Exporter
      health_checks {
        health_check_type = "HTTP"
        port              = 9100
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }

      # Shared volume mount for log forwarding
      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes && var.enable_log_forwarder_sidecar ? [1] : []
        content {
          mount_path  = "/logs"
          volume_name = "logs-volume"
          is_read_only = false
        }
      }
    }
  }

  #######################################
  # Application-Specific Exporters
  #######################################

  # Nginx Exporter Container - Collects nginx metrics
  # Exposes metrics on port 9113 for Prometheus scraping
  # Requires nginx with stub_status module enabled
  dynamic "containers" {
    for_each = var.enable_nginx_exporter ? [1] : []
    content {
      display_name = "${var.container_instance_name}-nginx-exporter"
      image_url    = "nginx/nginx-prometheus-exporter:latest"

      # Nginx exporter arguments
      # Point to nginx stub_status endpoint on main container
      arguments = [
        "-nginx.scrape-uri=http://localhost:80/stub_status"
      ]

      # Resource limits
      resource_config {
        memory_limit_in_gbs = 0.1
        vcpus_limit         = 0.05
      }

      # Health check
      health_checks {
        health_check_type = "HTTP"
        port              = 9113
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # Redis Exporter Container - Collects redis metrics
  # Exposes metrics on port 9121 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_redis_exporter ? [1] : []
    content {
      display_name = "${var.container_instance_name}-redis-exporter"
      image_url    = "oliver006/redis_exporter:latest"

      # Environment variables for redis connection
      environment_variables = {
        REDIS_ADDR = "localhost:6379"
        REDIS_PASSWORD = ""
      }

      # Resource limits
      resource_config {
        memory_limit_in_gbs = 0.1
        vcpus_limit         = 0.05
      }

      # Health check
      health_checks {
        health_check_type = "HTTP"
        port              = 9121
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # PostgreSQL Exporter Container - Collects postgres metrics
  # Exposes metrics on port 9187 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_postgres_exporter ? [1] : []
    content {
      display_name = "${var.container_instance_name}-postgres-exporter"
      image_url    = "prometheuscommunity/postgres-exporter:latest"

      # Environment variables for postgres connection
      environment_variables = {
        DATA_SOURCE_NAME = "postgresql://localhost:5432/postgres?sslmode=disable"
      }

      # Resource limits
      resource_config {
        memory_limit_in_gbs = 0.15
        vcpus_limit         = 0.05
      }

      # Health check
      health_checks {
        health_check_type = "HTTP"
        port              = 9187
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # MySQL Exporter Container - Collects mysql metrics
  # Exposes metrics on port 9104 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_mysql_exporter ? [1] : []
    content {
      display_name = "${var.container_instance_name}-mysql-exporter"
      image_url    = "prom/mysqld-exporter:latest"

      # Environment variables for mysql connection
      environment_variables = {
        DATA_SOURCE_NAME = "exporter:password@(localhost:3306)/"
      }

      # Resource limits
      resource_config {
        memory_limit_in_gbs = 0.15
        vcpus_limit         = 0.05
      }

      # Health check
      health_checks {
        health_check_type = "HTTP"
        port              = 9104
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # Blackbox Exporter Container - Probes endpoints over HTTP, HTTPS, DNS, TCP, ICMP
  # Exposes metrics on port 9115 for Prometheus scraping
  dynamic "containers" {
    for_each = var.enable_blackbox_exporter ? [1] : []
    content {
      display_name = "${var.container_instance_name}-blackbox-exporter"
      image_url    = "prom/blackbox-exporter:latest"

      # Blackbox exporter config file can be provided via volume mount if needed
      # Default configuration probes HTTP/HTTPS endpoints

      # Resource limits
      resource_config {
        memory_limit_in_gbs = 0.1
        vcpus_limit         = 0.05
      }

      # Health check
      health_checks {
        health_check_type = "HTTP"
        port              = 9115
        path              = "/metrics"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  #######################################
  # Sidecar Containers - New Architecture
  #######################################

  # Management Agent Sidecar Container (New Architecture)
  # Uses official Oracle Management Agent container image
  # Integrates with OCI Monitoring via Prometheus plugin
  dynamic "containers" {
    for_each = var.enable_management_agent_sidecar && var.mgmt_agent_sidecar_image != "" ? [1] : []
    content {
      display_name = "${var.container_instance_name}-mgmt-agent-sidecar"
      image_url    = var.mgmt_agent_sidecar_image

      # Command to redirect stdout/stderr to log file for log forwarder
      # The entrypoint script already handles log management, so we wrap it to redirect all output
      command = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [
        "/bin/bash",
        "-c",
        <<-EOT
          # Create log file if it doesn't exist
          touch /logs/mgmt-agent.log
          # Run the default entrypoint and redirect all output to log file
          # This captures the entire setup, registration, and monitoring lifecycle
          exec /entrypoint.sh 2>&1 | tee -a /logs/mgmt-agent.log
        EOT
      ] : null

      # Environment variables for Management Agent configuration
      environment_variables = {
        # Required environment variables for the custom entrypoint script
        MGMT_AGENT_INSTALL_KEY      = var.mgmt_agent_install_key
        OCI_REGION                  = var.region
        METRICS_NAMESPACE           = var.metrics_namespace
        PROMETHEUS_SCRAPE_INTERVAL  = tostring(var.prometheus_scrape_interval)
        PROMETHEUS_SCRAPE_TIMEOUT   = tostring(var.prometheus_scrape_timeout)
      }

      # Mount input.rsp configuration directory
      # Oracle Management Agent expects input.rsp at /opt/oracle/mgmtagent_secret/input.rsp
      volume_mounts {
        mount_path   = "/opt/oracle/mgmtagent_secret"
        volume_name  = "mgmt-agent-config"
        is_read_only = true
      }

      # Volume mounts for shared data
      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/metrics"
          volume_name = "metrics-volume"
          is_read_only = false
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/logs"
          volume_name = "logs-volume"
          is_read_only = false
        }
      }

      # Resource allocation for Management Agent sidecar
      resource_config {
        memory_limit_in_gbs = var.mgmt_agent_sidecar_memory_gb
        vcpus_limit         = var.mgmt_agent_sidecar_ocpus
      }

      # Note: No health check for Management Agent sidecar
      # It's a monitoring component and doesn't affect application availability
      # The agent has internal health monitoring and logging
    }
  }

  # Prometheus Sidecar Container (New Architecture)
  # Aggregates metrics from all exporters on localhost
  # Provides unified endpoint for Management Agent to scrape
  dynamic "containers" {
    for_each = var.enable_prometheus_sidecar && var.prometheus_sidecar_image != "" ? [1] : []
    content {
      display_name = "${var.container_instance_name}-prometheus-sidecar"
      image_url    = var.prometheus_sidecar_image

      # Command to redirect stdout/stderr to log file for log forwarder
      command = var.enable_log_forwarder_sidecar && var.enable_shared_volumes ? [
        "/bin/sh",
        "-c",
        <<-EOT
          # Create log file if it doesn't exist
          touch /logs/prometheus.log
          # Run prometheus with proper configuration and tee output to log file
          exec /bin/prometheus \
            --config.file=/etc/prometheus/prometheus.yml \
            --storage.tsdb.path=/prometheus \
            --web.console.libraries=/usr/share/prometheus/console_libraries \
            --web.console.templates=/usr/share/prometheus/consoles \
            --web.enable-lifecycle 2>&1 | tee -a /logs/prometheus.log
        EOT
      ] : null

      # Volume mounts for shared data
      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/metrics"
          volume_name = "metrics-volume"
          is_read_only = false
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/logs"
          volume_name = "logs-volume"
          is_read_only = false
        }
      }

      # Resource allocation for Prometheus sidecar
      resource_config {
        memory_limit_in_gbs = var.prometheus_sidecar_memory_gb
        vcpus_limit         = var.prometheus_sidecar_ocpus
      }

      # Health check for Prometheus
      health_checks {
        health_check_type = "HTTP"
        port              = 9090
        path              = "/-/healthy"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # Log Forwarder Sidecar Container (New Architecture)
  # Monitors application logs in shared volume and forwards to OCI Logging service
  # Uses Resource Principal authentication for secure access
  dynamic "containers" {
    for_each = var.enable_log_forwarder_sidecar && var.log_forwarder_sidecar_image != "" ? [1] : []
    content {
      display_name = "${var.container_instance_name}-log-forwarder-sidecar"
      image_url    = var.log_forwarder_sidecar_image

      # Environment variables for log forwarder configuration
      environment_variables = {
        LOG_MOUNT_PATH = "/logs"
        # LOG_FILE is no longer needed - forwarder auto-detects all log files
        LOG_OCID       = var.log_ocid != "" ? var.log_ocid : ""
        LOG_HEADER     = "container-logs"
        BATCH_SIZE     = "100"
        FLUSH_INTERVAL = "5"
      }

      # Volume mounts for shared logs
      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/logs"
          volume_name = "logs-volume"
          is_read_only = false
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_shared_volumes ? [1] : []
        content {
          mount_path  = "/metrics"
          volume_name = "metrics-volume"
          is_read_only = false
        }
      }

      # Resource allocation for Log Forwarder sidecar
      resource_config {
        memory_limit_in_gbs = var.log_forwarder_sidecar_memory_gb
        vcpus_limit         = var.log_forwarder_sidecar_ocpus
      }
    }
  }

  # Grafana Sidecar Container  # Provides visualization for Prometheus metrics and OCI Logs
  # Includes OCI Logs datasource plugin for unified observability dashboard
  dynamic "containers" {
    for_each = var.enable_grafana_sidecar && var.grafana_sidecar_image != "" ? [1] : []
    content {
      display_name = "${var.container_instance_name}-grafana-sidecar"
      image_url    = var.grafana_sidecar_image

      # Environment variables for Grafana configuration
      environment_variables = {
        GF_SECURITY_ADMIN_USER     = var.grafana_admin_user
        GF_SECURITY_ADMIN_PASSWORD = var.grafana_admin_password
        GF_SERVER_HTTP_PORT        = "3000"
        OCI_TENANCY_OCID           = var.tenancy_ocid
        OCI_REGION                 = var.region
      }

      # Resource allocation for Grafana sidecar
      resource_config {
        memory_limit_in_gbs = var.grafana_sidecar_memory_gb
        vcpus_limit         = var.grafana_sidecar_ocpus
      }

      # Health check for Grafana
      health_checks {
        health_check_type = "HTTP"
        port              = 3000
        path              = "/api/health"
        interval_in_seconds = 30
        timeout_in_seconds  = 10
        failure_threshold   = 3
      }
    }
  }

  # Management Agent Sidecar Container (Legacy - for backward compatibility)
  # NOTE: This does NOT work in Container Instances (containers lack systemd)
  # Use Monitoring VM with Management Agent instead
  dynamic "containers" {
    for_each = var.enable_management_agent ? [1] : []
    content {
      display_name = "${var.container_instance_name}-agent"
      # Using Oracle Linux with Java for Management Agent
      image_url    = "container-registry.oracle.com/os/oraclelinux:8"

      # Command to install and run Management Agent
      command = ["/bin/bash"]
      arguments = [
        "-c",
        <<-EOT
          set -e
          echo "Installing Management Agent..."

          # Install required packages
          yum install -y java-11-openjdk wget curl unzip

          # Download and install Management Agent
          curl -o agent.rpm "https://objectstorage.${var.region}.oraclecloud.com/n/idtskf8cjzhp/b/installer/o/ManagementAgent/latest/oracle.mgmt_agent.rpm"
          rpm -ivh agent.rpm

          # Configure agent with install key
          echo "INSTALL_KEY=${var.mgmt_agent_install_key}" > /opt/oracle/mgmt_agent/agent_inst/config/mgmt_agent_install.properties

          # Configure Prometheus scraping
          cat > /opt/oracle/mgmt_agent/agent_inst/config/prometheus.yml <<EOF
          global:
            scrape_interval: ${var.prometheus_scrape_interval}s
            scrape_timeout: ${var.prometheus_scrape_timeout}s

          scrape_configs:
            - job_name: 'container-app'
              static_configs:
                - targets: ['localhost:${var.prometheus_metrics_port}']
              metrics_path: '${var.prometheus_metrics_path}'
          EOF

          # Start Management Agent
          /opt/oracle/mgmt_agent/agent_inst/bin/setup.sh -responseFile /opt/oracle/mgmt_agent/agent_inst/config/mgmt_agent_install.properties

          # Keep container running
          tail -f /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log
        EOT
      ]

      # Environment variables for agent
      environment_variables = {
        JAVA_HOME           = "/usr/lib/jvm/java-11-openjdk"
        MGMT_AGENT_KEY      = var.mgmt_agent_install_key
        OCI_REGION          = var.region
        PROMETHEUS_PORT     = tostring(var.prometheus_metrics_port)
        METRICS_NAMESPACE   = var.metrics_namespace
      }

      # Resource limits - allocate 30% of resources to agent container
      resource_config {
        memory_limit_in_gbs = var.container_memory_gb * 0.3
        vcpus_limit         = var.container_ocpus * 0.3
      }

      # Note: No health check for agent - it's a monitoring sidecar
      # The main container has health checks to ensure the instance is healthy
    }
  }

  # Image pull secrets for private registries
  dynamic "image_pull_secrets" {
    for_each = local.use_image_pull_secret ? [1] : []
    content {
      secret_type  = "BASIC"
      registry_endpoint = var.ocir_endpoint
      username     = base64encode(var.ocir_username)
      password     = base64encode(var.ocir_auth_token)
    }
  }

  #######################################
  # Shared Volumes for Sidecar Pattern
  #######################################
  # Metrics volume - shared between application, Prometheus, and Management Agent
  dynamic "volumes" {
    for_each = var.enable_shared_volumes ? [1] : []
    content {
      name        = "metrics-volume"
      volume_type = "EMPTYDIR"
    }
  }

  # Logs volume - shared between all containers for centralized logging
  dynamic "volumes" {
    for_each = var.enable_shared_volumes ? [1] : []
    content {
      name        = "logs-volume"
      volume_type = "EMPTYDIR"
    }
  }

  # Management Agent configuration volume - contains input.rsp file
  # Mounted at /opt/oracle/mgmtagent_secret in the container
  dynamic "volumes" {
    for_each = var.enable_management_agent_sidecar ? [1] : []
    content {
      name        = "mgmt-agent-config"
      volume_type = "CONFIGFILE"

      configs {
        file_name = "input.rsp"
        data      = base64encode(<<-EOF
ManagementAgentInstallKey=${var.mgmt_agent_install_key}
AgentDisplayName=${var.container_instance_name}-mgmt-agent
CredentialWalletPassword=${random_password.mgmt_agent_wallet_password[0].result}
Service.plugin.prometheus.download=true
EOF
        )
      }
    }
  }

  # Additional volumes (user-defined)
  dynamic "volumes" {
    for_each = var.volumes
    content {
      name = volumes.value.name
      volume_type = volumes.value.volume_type

      # Empty dir volume
      dynamic "configs" {
        for_each = volumes.value.volume_type == "EMPTYDIR" ? [1] : []
        content {
          data = volumes.value.data
        }
      }
    }
  }

  # Container restart policy
  container_restart_policy = var.container_restart_policy

  freeform_tags = var.freeform_tags
  defined_tags  = var.defined_tags
}

#######################################
# Wait for Container Instance to be Running
#######################################
resource "time_sleep" "wait_for_container" {
  depends_on = [oci_container_instances_container_instance.main]

  create_duration = "30s"
}

#######################################
# Data source to get container instance details
#######################################
data "oci_container_instances_container_instance" "main" {
  container_instance_id = oci_container_instances_container_instance.main.id

  depends_on = [time_sleep.wait_for_container]
}

#######################################
# Data source to get VNIC details (for public IP)
# Container instances always have at least one VNIC
#######################################
data "oci_core_vnic" "container_vnic" {
  vnic_id = data.oci_container_instances_container_instance.main.vnics[0].vnic_id
}
