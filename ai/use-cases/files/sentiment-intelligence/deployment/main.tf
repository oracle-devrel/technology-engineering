# =============================================================================
# Sentiment Intelligence Application — OCI Infrastructure
#
# Deploys:
#   1. VCN with public/private/database subnets
#   2. OKE cluster with a managed node pool
#   3. Oracle Autonomous Database (Select AI enabled, walletless TLS)
#   4. OCI Container Registry repositories
#   5. Kubernetes manifests for the frontend & backend micro-services
# =============================================================================

# ---------- Networking ----------
module "network" {
  source = "./modules/network"

  compartment_ocid    = var.compartment_ocid
  resource_prefix     = local.resource_prefix
  vcn_cidr_block      = var.vcn_cidr_block
  public_subnet_cidr  = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr
  db_subnet_cidr      = var.db_subnet_cidr
  freeform_tags       = local.common_tags
}

# ---------- OKE Cluster ----------
module "oke" {
  source = "./modules/oke"

  compartment_ocid     = var.compartment_ocid
  resource_prefix      = local.resource_prefix
  vcn_id               = module.network.vcn_id
  public_subnet_id     = module.network.public_subnet_id
  private_subnet_id    = module.network.private_subnet_id
  kubernetes_version   = var.kubernetes_version
  node_pool_size       = var.node_pool_size
  node_shape           = var.node_shape
  node_ocpus           = var.node_ocpus
  node_memory_in_gbs   = var.node_memory_in_gbs
  node_pool_image_type = var.node_pool_image_type
  availability_domain  = data.oci_identity_availability_domains.ads.availability_domains[0].name
  freeform_tags        = local.common_tags
}

# ---------- Autonomous Database ----------
module "adb" {
  source = "./modules/adb"

  compartment_ocid        = var.compartment_ocid
  resource_prefix         = local.resource_prefix
  db_display_name         = var.adb_display_name
  db_name                 = var.adb_db_name
  admin_password          = var.adb_admin_password
  cpu_core_count          = var.adb_cpu_core_count
  data_storage_size_in_gb = var.adb_data_storage_size_in_gb
  db_workload             = var.adb_db_workload
  is_free_tier            = var.adb_is_free_tier
  license_model           = var.adb_license_model
  subnet_id               = module.network.db_subnet_id
  nsg_id                  = module.network.db_nsg_id
  freeform_tags           = local.common_tags
}

# ---------- Container Registry ----------
module "registry" {
  source = "./modules/registry"

  compartment_ocid = var.compartment_ocid
  repo_name        = var.ocir_repo_name
  freeform_tags    = local.common_tags
}

# ---------- Kubernetes Deployments ----------
resource "kubernetes_namespace_v1" "app" {
  depends_on = [module.oke]

  metadata {
    name = local.resource_prefix
    labels = {
      app         = var.app_name
      environment = var.environment
    }
  }
}

resource "kubernetes_secret_v1" "app_config" {
  depends_on = [kubernetes_namespace_v1.app]

  metadata {
    name      = "${local.resource_prefix}-config"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  data = {
    # Oracle Autonomous Database — walletless TLS (mTLS disabled on the ADB).
    DB_USER    = "ADMIN"
    DB_PASSWORD = var.adb_admin_password
    DB_DSN      = module.adb.connection_string
    USE_WALLET  = "false"

    # Select AI profile (create it in the database as a post-deploy step).
    SELECT_AI_PROFILE = var.select_ai_profile

    # OCI Generative AI.
    OCI_COMPARTMENT_ID = var.compartment_ocid
    OCI_GENAI_ENDPOINT = local.genai_endpoint
    OCI_GENAI_MODEL    = var.genai_model_id
  }
}

# --- Backend Deployment ---
resource "kubernetes_deployment_v1" "backend" {
  depends_on = [kubernetes_secret_v1.app_config]

  metadata {
    name      = "backend"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    labels = {
      app  = "backend"
      tier = "api"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "backend"
      }
    }

    template {
      metadata {
        labels = {
          app  = "backend"
          tier = "api"
        }
      }

      spec {
        container {
          name  = "backend"
          image = "${local.ocir_url}/backend:${var.backend_image_tag}"

          port {
            container_port = 8000
          }

          env_from {
            secret_ref {
              name = kubernetes_secret_v1.app_config.metadata[0].name
            }
          }

          env {
            name  = "APP_NAME"
            value = "Sentiment Intelligence"
          }

          env {
            name  = "API_HOST"
            value = "0.0.0.0"
          }

          env {
            name  = "API_PORT"
            value = "8000"
          }

          env {
            name  = "CORS_ORIGINS"
            value = "[\"*\"]"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1"
              memory = "1Gi"
            }
          }

          liveness_probe {
            http_get {
              path = "/api/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/api/health"
              port = 8000
            }
            initial_delay_seconds = 15
            period_seconds        = 5
          }
        }

        image_pull_secrets {
          name = "ocir-secret"
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "backend" {
  metadata {
    name      = "backend-service"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  spec {
    selector = {
      app = "backend"
    }

    port {
      port        = 8000
      target_port = 8000
      protocol    = "TCP"
    }

    type = "ClusterIP"
  }
}

# --- Frontend Deployment ---
resource "kubernetes_deployment_v1" "frontend" {
  depends_on = [kubernetes_service_v1.backend]

  metadata {
    name      = "frontend"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    labels = {
      app  = "frontend"
      tier = "web"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "frontend"
      }
    }

    template {
      metadata {
        labels = {
          app  = "frontend"
          tier = "web"
        }
      }

      spec {
        container {
          name  = "frontend"
          image = "${local.ocir_url}/frontend:${var.frontend_image_tag}"

          port {
            container_port = 80
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "256Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 10
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }

        image_pull_secrets {
          name = "ocir-secret"
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "frontend" {
  metadata {
    name      = "frontend-service"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    annotations = {
      "oci.oraclecloud.com/load-balancer-type" = "lb"
    }
  }

  spec {
    selector = {
      app = "frontend"
    }

    port {
      port        = 80
      target_port = 80
      protocol    = "TCP"
    }

    type = "LoadBalancer"
  }
}
