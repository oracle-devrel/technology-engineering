#!/usr/bin/env bash
# - 2025-06_17 : added Tofu support for LunaLab

if command -v terraform  &> /dev/null; then
  export TERRAFORM_COMMAND=terraform
elif command -v tofu  &> /dev/null; then
  export TERRAFORM_COMMAND=tofu
else
  error_exit "Command not found: terraform or tofu"
fi     
export VAR_FILE_PATH=$TARGET_DIR/resource_manager_variables.json
export ZIP_FILE_PATH=$TARGET_DIR/resource_manager_$TF_VAR_prefix.zip
export TERRAFORM_DIR=$PROJECT_DIR/src/terraform
# export TERRAFORM_DIR=$PROJECT_DIR

infra_as_code_plan() {
  cd $TERRAFORM_DIR    
  if [ "$TF_VAR_infra_as_code" == "terraform_object_storage" ]; then
    sed "s/XX_TERRAFORM_STATE_URL_XX/$TF_VAR_terraform_state_url/g" terraform.template.tf > terraform/terraform.tf
  fi  
  $TERRAFORM_COMMAND init -no-color -upgrade
  $TERRAFORM_COMMAND plan
}

# Before to run the build check the some resource with unique name in the tenancy does not exists already
# Run only once when the state file does not exist yet.
infra_as_code_precheck() {
  title "Infra As Code - Precheck"
  cd $TERRAFORM_DIR
  $TERRAFORM_COMMAND init -no-color -upgrade  
  $TERRAFORM_COMMAND plan -json -out=$TARGET_DIR/tfprecheck.plan > /dev/null 2>&1
  if [ "$?" != "0" ]; then
    # If there is an error in the plan phase, json output is not readable. 
    # Continue to apply to let apply fails and give a readable message
    echo "WARNING: infra_as_code_precheck: Terraform plan failed"
  else 
    # Buckets
    LIST_BUCKETS=`$TERRAFORM_COMMAND show -json $TARGET_DIR/tfprecheck.plan | jq -r '.resource_changes[] | select(.type == "oci_objectstorage_bucket") | .change.after.name'`
    for BUCKET_NAME in $LIST_BUCKETS; do
      echo "Bucket $BUCKET_NAME"
      BUCKET_CHECK=`oci os bucket get --bucket-name $BUCKET_NAME --namespace-name $TF_VAR_namespace 2> /dev/null | jq -r .data.name`
      if [ "$BUCKET_NAME" == "$BUCKET_CHECK" ]; then
        echo "PRECHECK ERROR: Bucket $BUCKET_NAME exists already in this tenancy."
        echo
        echo "Solution: There is probably another installation on this tenancy with the same prefix."
        echo "If you want to create a new installation, "
        echo "- edit the file terraform.tfvars"
        echo "- put a unique prefix in prefix. Ex:"
        echo  
        echo "prefix=xxx123"
        echo  
        error_exit "infra_as_code_precheck"
      fi
    done
  fi
  cd -
}

infra_as_code_apply() {
  title "Infra As Code - Apply" 
  cd $TERRAFORM_DIR  
  pwd
  if [ "$CALLED_BY_TERRAFORM" != "" ]; then 
    # Called from resource manager
    echo "WARNING: infra_as_code_apply (CALLED_BY_TERRAFORM=$CALLED_BY_TERRAFORM)"
    resource_manager_variables_json 
  elif [ "$TF_VAR_infra_as_code" == "build_resource_manager" ]; then
    resource_manager_create_or_update
    resource_manager_apply
    exit_on_error "infra_as_code_apply - build_resource_manager"
  elif [ "$TF_VAR_infra_as_code" == "create_resource_manager" ]; then
    resource_manager_create_or_update
    exit_on_error "infra_as_code_apply - create_resource_manager"
  elif [ "$TF_VAR_infra_as_code" == "distribute_resource_manager" ]; then
    resource_manager_create_or_update "YES"
    exit_on_error "infra_as_code_apply - distribute_resource_manager"    
  elif [ "$TF_VAR_infra_as_code" == "from_resource_manager" ]; then
    cd $PROJECT_DIR
    resource_manager_create_or_update
    resource_manager_apply
    exit_on_error "infra_as_code_apply - frm"
  else
    if [ "$TF_VAR_infra_as_code" == "terraform_object_storage" ]; then
      sed "s/XX_TERRAFORM_STATE_URL_XX/$TF_VAR_terraform_state_url/g" terraform.template.tf > terraform/terraform.tf
    fi  
    $TERRAFORM_COMMAND init -no-color -upgrade
    $TERRAFORM_COMMAND apply $@
    exit_on_error "infra_as_code_apply - other"
  fi
}

infra_as_code_destroy() {
  cd $TERRAFORM_DIR    
  # If resource_manager_stackid -> destroy the Resource Manager Stack
  # If from_resource_manager -> ask resource_manager to destroy its resources
  if [ -f $TARGET_DIR/resource_manager_stackid ] || [ "$TF_VAR_infra_as_code" == "from_resource_manager" ]; then
    resource_manager_destroy
  else
    $TERRAFORM_COMMAND init -upgrade
    $TERRAFORM_COMMAND destroy $@
    exit_on_error "infra_as_code_destroy"    
  fi
}

resource_manager_get_stack() {
  if [ ! -f $TARGET_DIR/resource_manager_stackid ]; then
    rs_echo "Stack does not exists ( file target/resource_manager_stackid not found )"
    exit
  fi    
  export STACK_ID=`cat $TARGET_DIR/resource_manager_stackid`
}

rs_echo() {
  echo "Resource Manager: $1"
}

resource_manager_variables_json () {
  rs_echo "Create $VAR_FILE_PATH"  
  # Transforms the variables in a JSON format
  # This is a complex way to get them. But it works for multi line variables like TF_VAR_private_key
  excluded=$(env | sed -n 's/^\([A-Z_a-z][0-9A-Z_a-z]*\)=.*/\1/p' | grep -v 'TF_VAR_')
  # Nasty WA trick for OCI Stack and OCI Devops (not a proper fix)
  excluded="$excluded maven.home OLDPWD"
  sh -c 'unset $1; export -p' sh "$excluded" > $TARGET_DIR/tf_var.sh 2>/dev/null

  echo -n "{" > $VAR_FILE_PATH
  cat $TARGET_DIR/tf_var.sh | sed "s/export TF_VAR_/\"/g" | sed "s/=\"/\": \"/g" | sed ':a;N;$!ba;s/\"\n/\", /g' | sed ':a;N;$!ba;s/\n/\\n/g' | sed 's/$/}/'>> $VAR_FILE_PATH  
}

# Used in both infra_as_code = resource_manager and from_resource_manager
resource_manager_create_or_update() {   
  DISTRIBUTE=$1
  rs_echo "Create Stack"
  if [ -f $ZIP_FILE_PATH ]; then
     echo "Stack exists already ( file target/resource_manager_stackid found )"
     mv $ZIP_FILE_PATH $ZIP_FILE_PATH.$DATE_POSTFIX
  fi    
  if [ -f $VAR_FILE_PATH ]; then
     mv $VAR_FILE_PATH $VAR_FILE_PATH.$DATE_POSTFIX
  fi    

  if [ -f $ZIP_FILE_PATH ]; then
    rm $ZIP_FILE_PATH
  fi  
  if [ -f "$TERRAFORM_DIR/.terraform" ]; then
    # Created during pre-check
    rm "$TERRAFORM_DIR/.terraform/*"
  fi 
  
  # Duplicate the directory in target/stack
  cd $PROJECT_DIR
  rm -Rf target/stack
  mkdir -p target/stack
  if command -v rsync &> /dev/null; then
    rsync -ax --exclude target . target/stack
  else
    find . -path '*/target' -prune -o -exec cp -r --parents {} target/stack \;
  fi
  cd target/stack
  # Move src/terraform to .
  mv src/terraform/* .
  rm terraform_local.tf
  rm -Rf src/terraform/
  if [ "$DISTRIBUTE" == "YES" ]; then
    # Comment all lines before -- FIXED
    sed -i '1,/-- Fixed/{/-- Fixed/!s/^[^#]/#&/}' terraform.tfvars
  fi
  # Add infra_as_code in terraform.tfvars
  if ! grep -q '="from_resource_manager"' terraform.tfvars; then
    echo >> terraform.tfvars
    echo 'infra_as_code="from_resource_manager"' >> terraform.tfvars
  fi
  # Create zip
  zip -r $ZIP_FILE_PATH * -x "target/*" -x "$TERRAFORM_DIR/.terraform/*"
  echo "Created Resource Manager Zip file - $ZIP_FILE_PATH"
  cd -

  if [ "$DISTRIBUTE" != "YES" ]; then
    resource_manager_variables_json
  fi

  if [ -f $TARGET_DIR/resource_manager_stackid ]; then
    if cmp -s $ZIP_FILE_PATH $ZIP_FILE_PATH.$DATE_POSTFIX; then
      rs_echo "Zip files are identical"
      if cmp -s $VAR_FILE_PATH $VAR_FILE_PATH.$DATE_POSTFIX; then
        rs_echo "Var files are identical"
        exit
      else 
        rs_echo "Var files are different"
      fi 
    else 
      rs_echo "Zip files are different"
    fi
    resource_manager_get_stack
    if [ "$DISTRIBUTE" == "YES" ]; then
      STACK_ID=$(oci resource-manager stack update --stack-id $STACK_ID --config-source $ZIP_FILE_PATH --force --query 'data.id' --raw-output)
    else 
   	  STACK_ID=$(oci resource-manager stack update --stack-id $STACK_ID --config-source $ZIP_FILE_PATH --variables file://$VAR_FILE_PATH --force --query 'data.id' --raw-output)
    fi
    rs_echo "Updated stack id: ${STACK_ID}"
  else 
    if [ "$DISTRIBUTE" == "YES" ]; then
      STACK_ID=$(oci resource-manager stack create --compartment-id $TF_VAR_compartment_ocid --config-source $ZIP_FILE_PATH --display-name $TF_VAR_prefix-resource-manager --query 'data.id' --raw-output)
    else 
      STACK_ID=$(oci resource-manager stack create --compartment-id $TF_VAR_compartment_ocid --config-source $ZIP_FILE_PATH --display-name $TF_VAR_prefix-resource-manager --variables file://$VAR_FILE_PATH --query 'data.id' --raw-output)
    fi
    echo "$STACK_ID" > $TARGET_DIR/resource_manager_stackid
    rs_echo "Created stack id: ${STACK_ID}"
  fi
  if [ "$DISTRIBUTE" == "YES" ]; then
    # Add tenancy_ocid and region since they are not detected by OCI CLI
    oci resource-manager stack update --stack-id $STACK_ID --variables "{\"tenancy_ocid\":\"$TF_VAR_tenancy_ocid\",\"compartment_ocid\":\"$TF_VAR_compartment_ocid\",\"current_user_ocid\":\"$TF_VAR_current_user_ocid\",\"region\":\"$TF_VAR_region\"}" --force
  fi
  rs_echo "URL: https://cloud.oracle.com/resourcemanager/stacks/${STACK_ID}?region=${TF_VAR_region}"
}

resource_manager_plan() {
  resource_manager_get_stack

  rs_echo "Create Plan Job"
  CREATED_PLAN_JOB_ID=$(oci resource-manager job create-plan-job --stack-id $STACK_ID --wait-for-state SUCCEEDED --wait-for-state FAILED --query 'data.id' --raw-output)
  echo "Created Plan Job Id: ${CREATED_PLAN_JOB_ID}"

  rs_echo "Get Job Logs"
  echo $(oci resource-manager job get-job-logs --job-id $CREATED_PLAN_JOB_ID) > $TARGET_DIR/plan_job_logs.txt
  echo "Saved Job Logs"
}

resource_manager_apply() {
  resource_manager_get_stack 
  
  rs_echo "Create Apply Job"
  # Max 2000 secs wait time (1200 secs is sometimes too short for OKE+DB)
  CREATED_APPLY_JOB_ID=$(oci resource-manager job create-apply-job --stack-id $STACK_ID --execution-plan-strategy=AUTO_APPROVED --wait-for-state SUCCEEDED --wait-for-state FAILED --wait-for-state CANCELED --max-wait-seconds 3000 --query 'data.id' --raw-output)
  echo "Created Apply Job Id: ${CREATED_APPLY_JOB_ID}"

  rs_echo "Get job"
  STATUS=$(oci resource-manager job get --job-id $CREATED_APPLY_JOB_ID  --query 'data."lifecycle-state"' --raw-output)
  
  oci resource-manager job get-job-logs-content --job-id $CREATED_APPLY_JOB_ID > $TARGET_DIR/tf_apply.log
  rs_echo "Apply Log"
  cat $TARGET_DIR/tf_apply.log | jq -r .data
  
  rs_echo "Get stack state"
  oci resource-manager stack get-stack-tf-state --stack-id $STACK_ID --file $TARGET_DIR/terraform.tfstate

  # Check the result of the destroy JOB and stop deletion if required
  if [ "$STATUS" != "SUCCEEDED" ]; then
    rs_echo "ERROR: Status ($STATUS) is not SUCCEEDED"

    exit 1 # Exit with error
  fi  
}

resource_manager_destroy() {
  resource_manager_get_stack 
  
  rs_echo "Create Destroy Job"
  CREATED_DESTROY_JOB_ID=$(oci resource-manager job create-destroy-job --stack-id $STACK_ID --execution-plan-strategy=AUTO_APPROVED --wait-for-state SUCCEEDED --wait-for-state FAILED --query 'data.id' --raw-output)
  echo "Created Destroy Job Id: ${CREATED_DESTROY_JOB_ID}"

  rs_echo "Get job"
  STATUS=$(oci resource-manager job get --job-id $CREATED_DESTROY_JOB_ID  --query 'data."lifecycle-state"' --raw-output)

  oci resource-manager job get-job-logs-content --job-id $CREATED_DESTROY_JOB_ID | tee > $TARGET_DIR/tf_destroy.log
  rs_echo "Destroy Log"
  cat $TARGET_DIR/tf_destroy.log | jq -r .data

  # Check the result of the destroy JOB and stop deletion if required
  if [ "$STATUS" != "SUCCEEDED" ]; then
    rs_echo "ERROR: Status ($STATUS) is not SUCCEEDED"
    exit 1 # Exit with error
  fi  

  rs_echo "Delete Stack"
  oci resource-manager stack delete --stack-id $STACK_ID --force
  echo "Deleted Stack Id: ${STACK_ID}"
  rm $TARGET_DIR/resource_manager_stackid
}

# echo "Creating Import Tf State Job"
# CREATED_IMPORT_JOB_ID=$(oci resource-manager job create-import-tf-state-job --stack-id $STACK_ID --tf-state-file "$JOB_TF_STATE" --wait-for-state SUCCEEDED --query 'data.id' --raw-output)
# echo "Created Import Tf State Job Id: ${CREATED_IMPORT_JOB_ID}"
