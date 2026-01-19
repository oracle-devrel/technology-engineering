# Environment Variables
# The values between ##xxx## will be filled during build.

# Generic
curl -s -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ > /tmp/instance.json
export TF_VAR_compartment_ocid=`cat /tmp/instance.json | jq -r .compartmentId`
export TF_VAR_region=`cat /tmp/instance.json | jq -r .region`
export TF_VAR_db_password="##TF_VAR_db_password##"

export LITELLM_MASTER_KEY=$TF_VAR_db_password
export LITELLM_SALT_KEY=$TF_VAR_db_password
export PORT=8080
export STORE_MODEL_IN_DB='True'

export UI_USERNAME=admin
export UI_PASSWORD=$TF_VAR_db_password
export DATABASE_URL="postgresql://litellm_user:$TF_VAR_db_password@localhost:5432/litellm_db"

# Config.yaml
export TF_VAR_current_user_ocid="##TF_VAR_current_user_ocid##"
export TF_VAR_tenancy_ocid="##TF_VAR_tenancy_ocid##"

