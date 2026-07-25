### Authentication details
$env:TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..YOUR_TENANCY_OCID"
$env:TF_VAR_user_ocid="ocid1.user.oc1..YOUR_USER_OCID"
$env:TF_VAR_fingerprint="xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
$env:TF_VAR_private_key_path="C:\Users\YOU\.oci\your_private_key.pem"
#$env:TF_VAR_private_api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

### Compartment
$env:TF_VAR_bastion_compartment_id="ocid1.compartment.oc1..YOUR_BASTION_COMPARTMENT_OCID"
$env:TF_VAR_network_compartment_id="ocid1.compartment.oc1..YOUR_NETWORK_COMPARTMENT_OCID"

$env:TF_VAR_compartment_ocid="ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID"

### Network
$env:TF_VAR_private_subnet_ocid="ocid1.subnet.oc1.eu-frankfurt-1.YOUR_PRIVATE_SUBNET_OCID"
$env:TF_VAR_public_subnet_ocid="ocid1.subnet.oc1.eu-frankfurt-1.YOUR_PUBLIC_SUBNET_OCID"
###

$env:TF_VAR_ci_count=1
$env:TF_VAR_ci_image_url="cdg.ocir.io/YOUR_NAMESPACE/YOUR_IMAGE:YOUR_TAG"

$env:TF_VAR_ci_registry_secret="ocid1.vaultsecret.oc1.eu-frankfurt-1.YOUR_VAULT_SECRET_OCID"
### Region
#$env:TF_VAR_region="eu-paris-1"
#$env:TF_VAR_region="eu-marseille-1"
$env:TF_VAR_region="eu-frankfurt-1"

$env:TF_VAR_ci_compartment_id_env="ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID"
$env:TF_VAR_ci_genai_endpoint="https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
$env:TF_VAR_ci_default_model="cohere.command-a-03-2025"


