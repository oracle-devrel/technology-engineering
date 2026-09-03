# CuOPT Frontend - OKE Deployment Plan

## Overview

This document outlines the deployment strategy for containerizing the CuOPT Frontend application and deploying it to Oracle Kubernetes Engine (OKE), integrated with the existing cuOPT Terraform infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Oracle Cloud Infrastructure                        │
│                           US-Phoenix Region                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                    OKE Cluster (cuopt namespace)                  │     │
│  │                                                                   │     │
│  │  ┌─────────────────┐    ┌─────────────────┐                      │     │
│  │  │  cuopt-frontend │    │  cuopt-frontend │  (2+ replicas)       │     │
│  │  │    Pod          │    │    Pod          │                      │     │
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │                      │     │
│  │  │  │  Nginx    │  │    │  │  Nginx    │  │                      │     │
│  │  │  │  (port 80)│  │    │  │  (port 80)│  │                      │     │
│  │  │  └───────────┘  │    │  └───────────┘  │                      │     │
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │                      │     │
│  │  │  │  Express  │  │    │  │  Express  │  │                      │     │
│  │  │  │(port 3001)│  │    │  │(port 3001)│  │                      │     │
│  │  │  └───────────┘  │    │  └───────────┘  │                      │     │
│  │  └────────┬────────┘    └────────┬────────┘                      │     │
│  │           │                      │                                │     │
│  │  ┌────────┴──────────────────────┴────────┐                      │     │
│  │  │           ClusterIP Service             │                      │     │
│  │  └────────────────────┬───────────────────┘                      │     │
│  │                       │                                           │     │
│  │  ┌────────────────────┴───────────────────┐                      │     │
│  │  │      OCI Load Balancer / Ingress        │                      │     │
│  │  └────────────────────┬───────────────────┘                      │     │
│  └───────────────────────┼───────────────────────────────────────────┘     │
│                          │                                                 │
│  ┌───────────────────────┼───────────────────────────────────────────┐     │
│  │                       ▼                                           │     │
│  │  ┌─────────────────────────────────────────────────────────────┐ │     │
│  │  │              cuOPT Server (GPU A10G)                        │ │     │
│  │  │              Existing Terraform Deployment                   │ │     │
│  │  └─────────────────────────────────────────────────────────────┘ │     │
│  │                                                                   │     │
│  │  ┌─────────────────────────────────────────────────────────────┐ │     │
│  │  │              OCI Generative AI Service                       │ │     │
│  │  │              US-Phoenix Endpoint                              │ │     │
│  │  └─────────────────────────────────────────────────────────────┘ │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **OCI CLI** configured with appropriate credentials
2. **kubectl** configured for your OKE cluster
3. **Docker** installed for building images
4. **Existing cuOPT Terraform deployment** with accessible endpoint
5. **OCI Container Registry (OCIR)** access

## Deployment Steps

### Step 1: Prepare OCI Container Registry

```bash
# Set variables
export OCI_REGION="us-phoenix-1"
export OCI_TENANCY_NAMESPACE="your-tenancy-namespace"
export OCIR_REPO="cuopt-frontend"

# Login to OCIR
docker login ${OCI_REGION}.ocir.io -u ${OCI_TENANCY_NAMESPACE}/your-username

# Create repository (if not exists)
oci artifacts container repository create \
  --compartment-id <compartment-ocid> \
  --display-name ${OCIR_REPO}
```

### Step 2: Build and Push Docker Image

```bash
# Navigate to the repository root
cd /path/to/fly_opt

# Build the Docker image (from the repository root)
docker build -t cuopt-frontend:latest -f deploy/Dockerfile .

# OR from deploy folder using docker-compose
cd deploy
docker-compose build

# Tag for OCIR
docker tag cuopt-frontend:latest \
  ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/${OCIR_REPO}:latest

docker tag cuopt-frontend:latest \
  ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/${OCIR_REPO}:v1.0.0

# Push to OCIR
docker push ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/${OCIR_REPO}:latest
docker push ${OCI_REGION}.ocir.io/${OCI_TENANCY_NAMESPACE}/${OCIR_REPO}:v1.0.0
```

### Step 3: Configure Kubernetes Secrets

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create OCIR pull secret
kubectl create secret docker-registry ocir-secret \
  --namespace cuopt \
  --docker-server=${OCI_REGION}.ocir.io \
  --docker-username="${OCI_TENANCY_NAMESPACE}/your-username" \
  --docker-password="your-auth-token" \
  --docker-email="your-email"

# Encode and update secrets
echo -n 'ocid1.compartment.oc1..xxxxx' | base64
# Update k8s/secret.yaml with encoded values

# Encode OCI config and private key
cat ~/.oci/config | base64 -w 0
cat ~/.oci/oci_api_key.pem | base64 -w 0
# Update k8s/secret.yaml with encoded values

# Apply secrets
kubectl apply -f k8s/secret.yaml
```

### Step 4: Update ConfigMap with cuOPT Endpoint

```bash
# Get cuOPT endpoint from Terraform output
cd /path/to/cuopt-terraform
export CUOPT_ENDPOINT=$(terraform output -raw cuopt_endpoint)

# Update k8s/configmap.yaml with the endpoint
sed -i "s|CUOPT_ENDPOINT:.*|CUOPT_ENDPOINT: \"${CUOPT_ENDPOINT}\"|" k8s/configmap.yaml

# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml
```

### Step 5: Deploy to OKE

```bash
# Update deployment.yaml with your OCIR image path
sed -i "s|\${OCI_REGION}|${OCI_REGION}|g" k8s/deployment.yaml
sed -i "s|\${OCI_TENANCY_NAMESPACE}|${OCI_TENANCY_NAMESPACE}|g" k8s/deployment.yaml

# Apply all manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Verify deployment
kubectl get pods -n cuopt
kubectl get svc -n cuopt
kubectl get ingress -n cuopt
```

### Step 6: Get External Access URL

```bash
# If using LoadBalancer service
kubectl get svc cuopt-frontend-lb -n cuopt -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# If using Ingress
kubectl get ingress cuopt-frontend-ingress -n cuopt
```

## Terraform Integration

### Option 1: Add Frontend Module to Existing Terraform

Create a new module `cuopt-frontend.tf`:

```hcl
# cuopt-frontend.tf

resource "kubernetes_namespace" "cuopt" {
  metadata {
    name = "cuopt"
  }
}

resource "kubernetes_config_map" "cuopt_frontend_config" {
  metadata {
    name      = "cuopt-frontend-config"
    namespace = kubernetes_namespace.cuopt.metadata[0].name
  }

  data = {
    CUOPT_ENDPOINT     = "http://${oci_core_instance.cuopt_server.private_ip}:80"
    OCI_GENAI_ENDPOINT = var.oci_genai_endpoint
    OCI_CONFIG_PROFILE = "DEFAULT"
    NODE_ENV           = "production"
    PORT               = "3001"
  }
}

resource "kubernetes_secret" "cuopt_frontend_secrets" {
  metadata {
    name      = "cuopt-frontend-secrets"
    namespace = kubernetes_namespace.cuopt.metadata[0].name
  }

  data = {
    OCI_COMPARTMENT_ID     = var.compartment_id
    OCI_GENAI_MODEL_ID     = var.genai_model_id
    OPENWEATHERMAP_API_KEY = var.weather_api_key
  }
}

resource "kubernetes_deployment" "cuopt_frontend" {
  metadata {
    name      = "cuopt-frontend"
    namespace = kubernetes_namespace.cuopt.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "cuopt-frontend"
      }
    }

    template {
      metadata {
        labels = {
          app = "cuopt-frontend"
        }
      }

      spec {
        container {
          name  = "cuopt-frontend"
          image = "${var.ocir_region}.ocir.io/${var.tenancy_namespace}/cuopt-frontend:latest"

          port {
            container_port = 80
          }

          port {
            container_port = 3001
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.cuopt_frontend_config.metadata[0].name
            }
          }

          env {
            name = "OCI_COMPARTMENT_ID"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.cuopt_frontend_secrets.metadata[0].name
                key  = "OCI_COMPARTMENT_ID"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "cuopt_frontend_lb" {
  metadata {
    name      = "cuopt-frontend-lb"
    namespace = kubernetes_namespace.cuopt.metadata[0].name
    annotations = {
      "service.beta.kubernetes.io/oci-load-balancer-shape" = "flexible"
    }
  }

  spec {
    type = "LoadBalancer"

    selector = {
      app = "cuopt-frontend"
    }

    port {
      port        = 80
      target_port = 80
    }
  }
}

output "cuopt_frontend_url" {
  value = "http://${kubernetes_service.cuopt_frontend_lb.status[0].load_balancer[0].ingress[0].ip}"
}
```

### Option 2: Reference Existing cuOPT Endpoint

```hcl
# variables.tf
variable "cuopt_endpoint" {
  description = "Endpoint of existing cuOPT deployment"
  type        = string
}

# Use in configmap
data = {
  CUOPT_ENDPOINT = var.cuopt_endpoint
}
```

## Environment Variables Reference

| Variable | Description | Source |
|----------|-------------|--------|
| `CUOPT_ENDPOINT` | cuOPT server URL | Terraform output / ConfigMap |
| `OCI_GENAI_ENDPOINT` | OCI GenAI service URL | ConfigMap |
| `OCI_COMPARTMENT_ID` | OCI Compartment OCID | Secret |
| `OCI_GENAI_MODEL_ID` | GenAI Model OCID | Secret |
| `OCI_CONFIG_PROFILE` | OCI config profile name | ConfigMap |
| `OPENWEATHERMAP_API_KEY` | Weather API key | Secret (optional) |

## Monitoring & Logging

### Enable OCI Logging

```bash
# Create log group
oci logging log-group create \
  --compartment-id <compartment-ocid> \
  --display-name "cuopt-frontend-logs"

# Enable container logging in OKE
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: oci-la-fluentd-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/cuopt-*.log
      tag kubernetes.*
    </source>
EOF
```

### Health Endpoints

- **Frontend Health**: `http://<service-ip>/`
- **API Health**: `http://<service-ip>/api/health`
- **cuOPT Health**: `http://<service-ip>/api/cuopt/health`
- **GenAI Health**: `http://<service-ip>/api/genai/health`

## Rollback Procedure

```bash
# View deployment history
kubectl rollout history deployment/cuopt-frontend -n cuopt

# Rollback to previous version
kubectl rollout undo deployment/cuopt-frontend -n cuopt

# Rollback to specific revision
kubectl rollout undo deployment/cuopt-frontend -n cuopt --to-revision=2
```

## Scaling

```bash
# Manual scaling
kubectl scale deployment cuopt-frontend -n cuopt --replicas=5

# HPA will auto-scale based on CPU/Memory (already configured)
kubectl get hpa -n cuopt
```

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n cuopt
kubectl describe pod <pod-name> -n cuopt

# View logs
kubectl logs -f deployment/cuopt-frontend -n cuopt

# Check connectivity to cuOPT
kubectl exec -it deployment/cuopt-frontend -n cuopt -- \
  wget -qO- http://cuopt-server:80/cuopt/health

# Check OCI config
kubectl exec -it deployment/cuopt-frontend -n cuopt -- \
  cat /root/.oci/config
```

## Security Considerations

1. **Network Policies**: Restrict pod-to-pod communication
2. **RBAC**: Limit service account permissions
3. **Secrets**: Use OCI Vault for production secrets
4. **TLS**: Enable HTTPS via Ingress with cert-manager
5. **Image Scanning**: Enable vulnerability scanning in OCIR

## Next Steps

1. [ ] Build and push Docker image to OCIR
2. [ ] Update secrets with actual values
3. [ ] Configure cuOPT endpoint in ConfigMap
4. [ ] Deploy to OKE
5. [ ] Configure DNS/domain (optional)
6. [ ] Enable TLS/HTTPS (recommended)
7. [ ] Set up monitoring dashboards
8. [ ] Configure backup/disaster recovery
