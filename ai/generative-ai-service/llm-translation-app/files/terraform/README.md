# Terraform — Container Instances (private subnet) + Load Balancer (public subnet)

Deploys N Container Instances running the translation API on a private subnet,
fronted by a public Load Balancer. Designed for OCI Resource Manager Stacks, but
it also runs with the Terraform CLI (uncomment the security variables that
Resource Manager would otherwise inject).

## Deploy with the Terraform CLI

```bash
cd terraform

# provide the required variables (copy the example and fill in your values)
cp env-vars-exemple.sh env-vars.sh   # then edit; on Windows use env-vars-exemple.ps1
source env-vars.sh

terraform init
terraform plan
terraform apply
```

Prefer OCI Resource Manager? Create a Stack from this folder
(**Resource Manager → Stacks → Create Stack → source your Terraform
configuration**) and supply the same variables.

## Prerequisites

Create a Secret in OCI Vault so the Container Instances can log in to OCIR (where
your translator image is stored):

1. Create an **Auth Token** for logging in to the OCIR registry.
2. Create the secret as a JSON string:
   ```json
   {
     "username": "<ocir-username>",
     "password": "<your-auth-token>"
   }
   ```
3. Create a **Dynamic Group** for the Container Instances (so they can read the secret):
   ```
   Any {resource.type = 'computecontainerinstance', resource.compartment.id = '<your-compartment-ocid>'}
   ```
4. Create a **Policy** allowing that dynamic group to read secrets:
   ```
   allow dynamic-group <dynamic-group-name> to read secret-bundles in compartment <compartment-name>
   ```
5. Create a **VCN** (use the VCN Wizard): a **public** subnet for the Load Balancer
   and a **private** subnet for the Container Instances.
6. Add an **ingress rule for port 8000** to the security lists of both subnets.

## Variables

Some variables have defaults you can override; others are mandatory and specific
to your tenancy:

- `compartment_ocid`
- `region`
- `private_subnet_ocid`
- `public_subnet_ocid`
- `ci_image_url`
- `ci_registry_secret` (secret OCID)
- …and so on (see `variables.tf`)

## Scale

Set `ci_count` to the number of Container Instances you want.

> After `apply`, wait a short time before hitting the Load Balancer — it needs a
> moment to validate the backends, otherwise you'll get a temporary "Bad Gateway".
