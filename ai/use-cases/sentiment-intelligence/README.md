# Sentiment Intelligence

Sentiment Intelligence is a React and FastAPI demonstration application for
brand monitoring, customer-feedback analysis, and natural-language data access
with Oracle Autonomous AI Database, Select AI, and OCI Generative AI.

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/ai-quick-deploys/releases/latest/download/sentiment-intel-stack.zip)

> Click the button above to deploy this application directly to your OCI tenancy
> using **OCI Resource Manager**. It provisions a VCN, an OKE Kubernetes cluster,
> an Oracle Autonomous AI Database, and OCIR repositories, then rolls out the
> frontend and backend behind an OCI Load Balancer. See
> [Deploy to Oracle Cloud Infrastructure](#deploy-to-oracle-cloud-infrastructure)
> for details and the manual Terraform path.

The application uses a coordinated six-stage workflow. Each stage has a focused
responsibility and passes its result to the next stage; the stages are not six
independently deployed autonomous agents.

## Capabilities

- Search and scrape public customer-feedback sources.
- Ingest reviews into Oracle Autonomous AI Database.
- Run bounded concurrent sentiment inference with `DBMS_CLOUD_AI.GENERATE`.
- Calculate dashboard distributions, trends, alerts, and recommendations on demand.
- Ask natural-language data questions through the Select AI Python client.
- Query an existing Select AI RAG knowledge base.
- Stream pipeline progress to the React UI with Server-Sent Events.

## Repository layout
 
```text
sentiment-intelligence/
|-- frontend/          React 19, TypeScript, Vite, Tailwind and Chart.js (+ Dockerfile, nginx.conf)
|-- backend/    FastAPI, python-oracledb, Select AI and OCI SDK (+ Dockerfile)
|-- rag-documents/     Optional sample documents for a separately configured RAG index
|-- scripts/           Developer helper scripts (run.sh starts both services locally)
|-- terraform/         OCI infrastructure as code (OKE, Autonomous DB, OCIR) + Resource Manager schema
|-- README.md
`-- .gitignore
```

Generated frontend output, installed dependencies, Python virtual environments,
database wallets, OCI keys, real `.env` files, and AICoE deployment artifacts are
intentionally excluded.

## Prerequisites

- Python 3.11 or newer.
- Node.js 18 or newer and npm.
- An Oracle Autonomous AI Database reachable from the backend.
- An application database user and the tables referenced by the backend.
- An existing Select AI NL2SQL profile.
- An existing RAG profile named `OCI_SELECTAI_RAG` if the Knowledge Base mode is used.
- OCI Generative AI access and an OCI SDK authentication method for the application.

This repository does not provision the database schema, Select AI profiles, RAG
vector index, database credentials, or OCI policies. Those resources must already
exist in the target environment.

## Secure configuration

The repository includes example environment files containing placeholders only.
Create local files from them and never commit the resulting `.env` files.

### Backend

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `backend/.env` with the target environment's values.

For wallet-based mTLS, unzip the wallet outside the repository and set
`WALLET_LOCATION` to that directory. Do not copy the wallet into the project.

For walletless TLS, enable TLS for the Autonomous Database, set
`USE_WALLET=false`, and use the OCI Console's TLS connect descriptor as `DB_DSN`.

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env
```

The default `/api` value uses the Vite proxy and requires no credentials.

## Install and run

### Quickstart (macOS or Linux)

From the repository root, one command installs dependencies for both services,
creates `backend/.env` from the example if it is missing, and starts the
backend and frontend together:

```bash
./scripts/run.sh
```

The script resolves the project root from its own location, so it also works
when launched from inside `scripts/` (`cd scripts && ./run.sh`). It starts the
backend on `http://localhost:4060` and the frontend on `http://localhost:3060`,
and stops both on `Ctrl+C`. Edit `backend/.env` with real credentials
before relying on database or OCI features.

To run the services individually, or on Windows, use the manual steps below.

### Backend on Windows PowerShell

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

### Backend on macOS or Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

The backend listens on `http://localhost:4060`; OpenAPI documentation is at
`http://localhost:4060/docs`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The frontend listens on `http://localhost:3060` and proxies `/api` requests to
the backend on port `4060`.

## Tests and build

After configuring `backend/.env`, run the backend unit tests from that
directory:

```bash
python -m unittest discover -s tests -v
```

Build the frontend from `frontend/`:

```bash
npm run build
```

## Main API routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Database and application status |
| `GET` | `/api/dashboard` | Dashboard aggregates |
| `GET` | `/api/history` | Review volume and score history |
| `POST` | `/api/analyze` | Coordinated analysis workflow with SSE progress |
| `POST` | `/api/query` | Select AI natural-language data query |
| `POST` | `/api/rag-query` | Select AI RAG knowledge-base query |
| `POST` | `/api/generate-campaign` | Campaign variants from analyzed insights |

## Deploy to Oracle Cloud Infrastructure

The `terraform/` directory contains infrastructure as code that provisions a
complete runtime on Oracle Cloud Infrastructure:

- A VCN with public, private, and database subnets, gateways, and security lists.
- An Oracle Kubernetes Engine (OKE) cluster with a managed node pool.
- An Oracle Autonomous AI Database (Select AI enabled, walletless TLS).
- OCI Container Registry (OCIR) repositories for the backend and frontend images.
- Kubernetes deployments and services for both tiers, fronted by an OCI Load Balancer.

```
                         ┌──────────────────────────────────────────────────┐
                         │              Oracle Cloud Infrastructure          │
  ┌──────────┐           │  ┌─────────────────────────────────────────┐      │
  │  Users   │──HTTPS────│──│  OCI Load Balancer                       │      │
  └──────────┘           │  └─────────┬───────────────────────────────┘      │
                         │  ┌─────────┴───────────────────────────────┐      │
                         │  │  Oracle Kubernetes Engine (OKE)          │      │
                         │  │   frontend (nginx)  →  backend (FastAPI) │      │
                         │  └─────────┬───────────────────────────────┘      │
                         │  ┌─────────┴──────────┐   ┌──────────────────┐     │
                         │  │ Autonomous AI DB   │   │ OCI Generative AI│     │
                         │  │ (Select AI)        │   └──────────────────┘     │
                         │  └────────────────────┘                            │
                         └───────────────────────────────────────────────────┘
```

### Option 1: One-Click Deploy with OCI Resource Manager

The fastest way to deploy:

1. Click the **Deploy to Oracle Cloud** button at the top of this README.
2. Sign in to your OCI tenancy and accept the Terraform stack.
3. Fill in the Resource Manager stack configuration form:
   - **Compartment** and **Region** for the deployment.
   - **Database Admin Password** (min 12 chars, mixed case + a number).
   - Optionally adjust OKE sizing, Autonomous Database, Select AI profile name,
     and OCI Generative AI region/model.
4. Run **Plan**, then **Apply**.

Resource Manager creates the VCN, OKE cluster, Autonomous Database, OCIR
repositories, and Kubernetes deployments. After apply, push the application
images and complete the post-deploy steps below.

> The button's `zipUrl` must point to a publicly reachable archive of the
> `terraform/` directory. Generate one with
> `cd terraform && zip -r ../sentiment-intel-stack.zip . -x '*.terraform*' 'terraform.tfvars'`
> and host it (for example, as a GitHub release asset), then update the `zipUrl`
> in the button link to match.

### Option 2: Deploy with the Terraform CLI

**Prerequisites**

- [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) configured (`oci session authenticate` or `~/.oci/config`)
- [Terraform >= 1.5](https://developer.hashicorp.com/terraform/downloads)
- Docker, and `kubectl`

**Steps**

1. **Configure variables**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your OCI configuration and DB password
   ```

2. **Provision infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. **Configure kubectl** (command is printed in the Terraform output):
   ```bash
   oci ce cluster create-kubeconfig --cluster-id <oke_cluster_id> \
     --region <region> --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT
   ```

4. **Build and push images** to OCIR (the exact commands, with your namespace
   and region, are in the `build_push_images_command` Terraform output):
   ```bash
   docker login <region-key>.ocir.io
   docker build -t <ocir-url>/backend:latest ../backend/
   docker push <ocir-url>/backend:latest
   docker build -t <ocir-url>/frontend:latest --build-arg VITE_API_BASE_URL=/api ../frontend/
   docker push <ocir-url>/frontend:latest
   ```

5. **Create the OCIR pull secret** and restart the deployments so the pods pull
   the freshly pushed images:
   ```bash
   kubectl create secret docker-registry ocir-secret -n <app_namespace> \
     --docker-server=<region-key>.ocir.io \
     --docker-username='<namespace>/oracleidentitycloudservice/<your-email>' \
     --docker-password='<your-auth-token>' --docker-email='<your-email>'
   kubectl rollout restart deployment/backend -n <app_namespace>
   kubectl rollout restart deployment/frontend -n <app_namespace>
   ```

6. **Get the application URL**:
   ```bash
   kubectl get svc frontend-service -n <app_namespace>
   ```

### Option 3: Automated helper script

`terraform/build_and_deploy.sh` wraps the full flow:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # then edit it
./build_and_deploy.sh deploy       # build + push images, apply infra, wire up kubectl

# Individual steps:
./build_and_deploy.sh build        # Build Docker images
./build_and_deploy.sh push         # Push to OCIR
./build_and_deploy.sh infra        # Apply Terraform
./build_and_deploy.sh kubeconfig   # Configure kubectl
./build_and_deploy.sh destroy      # Tear down everything
```

### Post-deploy application setup

The Terraform provisions infrastructure only; it does not seed the application
schema or Select AI profiles (consistent with this repository's model that those
resources already exist). After the database is up, connect as `ADMIN` and:

1. Create the application schema and tables (`backend/schema.sql`).
2. Create the Select AI profile named by the `select_ai_profile` variable
   (default `SENTIMENT_PROFILE`) and, if the Knowledge Base mode is used, the
   `OCI_SELECTAI_RAG` RAG profile.
3. Optionally load sample data with `backend/seed_reviews.py`.
4. Grant the database/OCI policies required by `DBMS_CLOUD_AI` and OCI
   Generative AI. For pods to call OCI GenAI without embedding keys, configure
   OKE **instance principals**: create a dynamic group for the worker nodes and
   a policy allowing `generative-ai-family` usage in the compartment.

### Terraform configuration reference

| Variable | Description | Default |
|---|---|---|
| `compartment_ocid` | Target compartment | *required* |
| `region` | Deployment region | *required* |
| `adb_admin_password` | Autonomous DB admin password | *required* |
| `app_name` | Resource name prefix | `sentiment-intel` |
| `environment` | `dev` / `staging` / `prod` | `prod` |
| `node_pool_size` | OKE worker node count | `2` |
| `node_shape` | OKE worker shape | `VM.Standard.E4.Flex` |
| `adb_cpu_core_count` | Autonomous DB ECPU count | `2` |
| `select_ai_profile` | Select AI profile name the backend expects | `SENTIMENT_PROFILE` |
| `genai_region` | OCI Generative AI region | `eu-frankfurt-1` |
| `genai_model_id` | OCI Generative AI model | `cohere.command-a-03-2025` |
| `ocir_repo_name` | OCIR repository name | `sentiment-intel` |

## Security checklist before pushing

- Confirm `git status` does not list `.env`, wallet, certificate, or OCI key files.
- Keep database and wallet passwords in a secret manager or local environment only.
- Keep `~/.oci/config` and its referenced private key outside the repository.
- Use a least-privileged application database account.
- Review sample documents before publishing them to a public repository.

