# Get Compartment and region
curl -s -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ > /tmp/instance.json
export TF_VAR_compartment_ocid=`cat /tmp/instance.json | jq -r .compartmentId`
export TF_VAR_region=`cat /tmp/instance.json | jq -r .region`

# To replace in models.yaml
export TF_VAR_dac_endpoint_ocid="##TF_VAR_dac_endpoint_ocid##"
export TF_VAR_use_models_yaml="##TF_VAR_use_models_yaml##"

# Used by setting.py
if [ "$TF_VAR_use_models_yaml" != "true" ]; then
  # OCI_COMPARTMENT = "" -> Use models.yaml
  export OCI_COMPARTMENT=$TF_VAR_compartment_ocid
fi
export OCI_REGION=$TF_VAR_region
export DEFAULT_API_KEYS="##TF_VAR_default_api_keys##"
