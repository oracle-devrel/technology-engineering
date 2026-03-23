#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh."
  exit 1
fi  
cd $PROJECT_DIR

# Shared BASH Functions
. $BIN_DIR/shared_bash_function.sh

if grep -q 'auth_token="__TO_FILL__"' $PROJECT_DIR/terraform.tfvars; then
  get_user_details
  echo "TF_VAR_tenancy_ocid=$TF_VAR_tenancy_ocid"
  export TF_VAR_home_region_key=`oci iam tenancy get --tenancy-id $TF_VAR_tenancy_ocid | jq -r '.data["home-region-key"]'`
  export TF_VAR_home_region=`oci iam region list --all | jq -r '.data[] | select(.key=="'$TF_VAR_home_region_key'") | .name'`

  echo "Generating a new AUTH_TOKEN (Home Region=$TF_VAR_home_region)"
  oci iam auth-token create --description "OCI_STARTER_TOKEN" --user-id $TF_VAR_current_user_ocid --region $TF_VAR_home_region > auth_token.log 2>&1
  STATUS="$?"
  cat auth_token.log
  if [ "$STATUS" != "0" ]; then
     echo
     echo "ERROR: Generation of the OCI Auth Token failed"
     echo
     echo "Please try this:"   
     echo "- Login in the OCI Console"
     echo "- Click on the User Icon on the top/right."
     echo "- Choose Profile/<your name>"
     echo "- Go to tab Tokens and Key."
     echo "- Try to generate an Auth Token"
     echo "- and place it in terraform.tfvars"
     exit 1
  fi      
  export TF_VAR_auth_token=`cat auth_token.log | jq -r '.data.token'`
  rm auth_token.log
  if [ "$TF_VAR_auth_token" != "" ]; then
    sed -i "s&auth_token=\"__TO_FILL__\"&auth_token=\"$TF_VAR_auth_token\"&" $PROJECT_DIR/terraform.tfvars
    echo "AUTH_TOKEN stored in terraform.tfvars"
    echo "> auth_token=$TF_VAR_auth_token"
  fi  
else
  echo 'File terraform.tfvars does not contain: auth_token="__TO_FILL__"'  
fi

