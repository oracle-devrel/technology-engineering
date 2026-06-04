#!/usr/bin/env bash
if [ "$PROJECT_DIR" = "" ]; then
  echo "Error: PROJECT_DIR not set. Please use starter.sh."
  exit 1
fi

if declare -p | grep -q "__TO_FILL__"; then
  title "CONFIG.SH"
  
  accept_request() {
    if [ "$ACCEPT_ALL" == "TRUE" ]; then
      return 0;
    fi
    echo "$REQUEST"
    echo ""  
    read -r -p "Please confirm. [Yes/No] " response
    case "$response" in
        [aA][lL][lL])
            export ACCEPT_ALL="TRUE"
            return 0
            ;;
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            echo "Skipping $1"
            return 1 
    esac
  }

  store_terraform_tfvars() {
    echo "$1=$2"            
    sed -i "s&$1=\"__TO_FILL__\"&$1=\"$2\"&" $PROJECT_DIR/terraform.tfvars              
    echo "$1 stored in terraform.tfvars"            
    echo       
  }

  read_ocid() {
    while [ "${!1}" == "__TO_FILL__" ]; do    
      title "Config - $2 OCID"  
      read -r -p "Enter your $2 OCID (Format: $3.xxxxx): " response
      if [[ $response == $3* ]]; then
        export $1=$response
        without_prefix="${1#TF_VAR_}"
        store_terraform_tfvars $without_prefix ${!1}
      else
        echo "Wrong format $response"
        echo            
      fi
    done    
  }

  # Livelabs Green Button (Autodetect compartment/vcn/subnet)
  livelabs_green_button 

  # LunaLab (Autodetect compartment)
  lunalab

  # PREFIX
  if [ "$TF_VAR_prefix" == "__TO_FILL__" ]; then
    DEFAULT_PREFIX=starter
    title "Prefix"
    echo "Each resource name will start the same prefix."
    echo "Ex: prefix: $DEFAULT_PREFIX -> $DEFAULT_PREFIX-instance, $DEFAULT_PREFIX-db, ..."
 
    export REQUEST="Keep the default prefix (TF_VAR_prefix="$DEFAULT_PREFIX") ?"
    if accept_request; then
        export TF_VAR_prefix=$DEFAULT_PREFIX
    else
      while [ "$TF_VAR_prefix" == "__TO_FILL__" ]; do    
        echo
        echo "Rule: Maximum 8 characters, only lowercase or numbers. No UPPERCASE or special characters. Ex: starter"  
        read -r -p "Enter your prefix: " response
        # Check if the length is 8 characters or less
        if [[ ${#response} -le 8 ]]; then
          # Check if the variable contains only lowercase letters and numbers
          if [[ "${response}" =~ ^[a-z0-9]+$ ]]; then
            export TF_VAR_prefix=$response
            echo "OK: The prefix meets all the requirements."
          else
            echo "ERROR: The prefix should contain only lowercase characters and numbers."
          fi
        else
          echo "ERROR: Maximum 8 characters."
        fi
      done         
    fi 
    store_terraform_tfvars prefix $TF_VAR_prefix
  fi

  # DB_PASSWORD
  if [ "$TF_VAR_db_password" == "__TO_FILL__" ]; then
    title "Config - Database Password"
    export REQUEST="Generate password for the database ? (TF_VAR_db_password) ?"
    if accept_request; then
        echo "Generating password for the database"
        export TF_VAR_db_password=`python3 $BIN_DIR/gen_password.py`
    else
        echo
        echo "Rule: Minimum 12 characters, 2 in lowercase, 2 in uppercase, 2 numbers, 2 special characters. Ex: LiveLab__12345"  
        echo "To avoid issues: for special characters use only ['#', '_', '-']"
        read -r -p "Enter your database password: " TF_VAR_db_password
        echo TF_VAR_db_password=$TF_VAR_db_password
        if [[ "${TF_VAR_db_password}" =~ ^.{12,}$ ]]; then
          # Check for length
          echo TF_VAR_db_password=$TF_VAR_db_password
          if [[ "${TF_VAR_db_password}" =~ (.*[A-Z].*[A-Z]) ]]; then
            # Check for uppercase letters
            if [[ "${TF_VAR_db_password}" =~ (.*[a-z].*[a-z]) ]]; then
              # Check for lowercase letters
              if [[ "${TF_VAR_db_password}" =~ (.*[-_#].*[-_#]) ]]; then
              # Check for special characters
                if [[ "${TF_VAR_db_password}" =~ (.*[0-9].*[0-9]) ]]; then
                  # Check for numbers
                  echo "The password meets all the requirements."
                else
                  error_exit "The password does not contain enough numbers."
                fi
              else
                error_exit "The password does not contain enough special characters."
              fi
            else
              error_exit "The password does not contain enough lowercase letters."
            fi
          else
            error_exit "The password does not contain enough uppercase letters."
          fi
        else
        error_exit "The password is too short."
        fi        
    fi 
    store_terraform_tfvars db_password $TF_VAR_db_password
  fi

  # AUTH_TOKEN
  if [ "$TF_VAR_auth_token" == "__TO_FILL__" ]; then
    title "Config - Authentication Token"
    export REQUEST="Generate OCI Auth token ? (TF_VAR_auth_token) ?"
    if accept_request; then
      echo "Generating OCI Auth token"
      . $BIN_DIR/gen_auth_token.sh
    else 
      read -r -p "Enter your OCI Auth token (TF_VAR_auth_token) " TF_VAR_auth_token 
      store_terraform_tfvars auth_token $TF_VAR_auth_token
    fi      
  fi

  # LICENSE_MODEL
  if [ "$TF_VAR_license_model" == "__TO_FILL__" ]; then
    title "Config - License Model"  
    echo "License Model (TF_VAR_license_model): BRING_YOUR_OWN_LICENSE or LICENSE_INCLUDED"
    while [ "$TF_VAR_license_model" == "__TO_FILL__" ]; do
      read -r -p "Enter BRING_YOUR_OWN_LICENSE or LICENSE_INCLUDED: " response
      if [[ $response == "BRING_YOUR_OWN_LICENSE" ]] || [[ $response == "LICENSE_INCLUDED" ]] ; then
        export TF_VAR_license_model=$response
        store_terraform_tfvars license_model $response
      else
        echo "Wrong value $response"
        echo            
      fi
    done     
  fi

  # OIC_APPID
  if [ "$TF_VAR_oic_appid" == "__TO_FILL__" ]; then
    title "Config - Oracle Integration Confidential App ID"    
    export REQUEST="Enter the OIC APPID ? (TF_VAR_oic_appid) ?"
    read -r -p "Enter the OIC APPID ? (TF_VAR_oic_appid): " TF_VAR_oic_appid
    if [[ "${TF_VAR_oic_appid}" =~ ^.*_APPID$ ]]; then
      echo "TF_VAR_oic_appid ends with _APPID"
    else
      error_exit "TF_VAR_oic_appid does not end with _APPID"
    fi    
    store_terraform_tfvars oic_appid $TF_VAR_oic_appid
  fi  

  # API_KEY
  if [ "$TF_VAR_api_key" == "__TO_FILL__" ]; then
    title "Config - API Key"     
    read -r -p "Enter the value of the API_KEY (ex: MY_long_KEY_123456) ? (TF_VAR_api_key) " TF_VAR_api_key 
    store_terraform_tfvars api_key $TF_VAR_api_key
  fi  

  # COMPARTMENT_ID
  if [ "$TF_VAR_compartment_ocid" == "__TO_FILL__" ]; then
    title "Config - Compartment"       
    export REQUEST="Create a new Compartment ? (<No> will ask to reuse an existing one) ?"
    if accept_request; then
      echo "Check if 'oci-starter' compartment exists"
      STARTER_OCID=`oci iam compartment list --name oci-starter | jq .data[0].id -r`
      if [ -z "$STARTER_OCID" ]; then
        echo "Creating a new 'oci-starter' compartment"
        oci iam compartment create --compartment-id $TF_VAR_tenancy_ocid --description oci-starter --name oci-starter --wait-for-state ACTIVE > $TARGET_DIR/compartment.log 2>&1
        STARTER_OCID=`cat $TARGET_DIR/compartment.log | grep \"id\" | sed 's/"//g' | sed "s/.*id: //g" | sed "s/,//g"`
        while [ "$NAME" != "oci-starter" ]
        do
            oci iam compartment get --compartment-id=$STARTER_OCID > $TARGET_DIR/waiting.log 2>&1
            if grep -q "NotAuthorizedOrNotFound" $TARGET_DIR/waiting.log; then
              echo "Waiting"
              sleep 2
            else
              NAME=`cat $TARGET_DIR/waiting.log | jq -r .data.name`
            fi
        done
        echo "Compartment created"
      else
        echo "Using the existing 'oci-starter' Compartment"
      fi 
      export TF_VAR_compartment_ocid=$STARTER_OCID
      store_terraform_tfvars compartment_ocid $TF_VAR_compartment_ocid
      echo            
    else
      read_ocid TF_VAR_compartment_ocid "Compartment" ocid1.compartment 
    fi     
    # echo "        The components will be created in the root compartment."
    # export TF_VAR_compartment_ocid=$TF_VAR_tenancy_ocid
  fi
  
  # Vault
  if [ "$TF_VAR_vault_ocid" == "__TO_FILL__" ]; then
    title "Config - Vault"       
    export REQUEST="Create a new vault ? (<No> will ask for the ocid of an existing one) ?"
    if accept_request; then  
      # Comment the 2 lines. The vault will be created.
      sed -i "s/^[ ]*vault_ocid/# vault_ocid/" $PROJECT_DIR/terraform.tfvars     
      sed -i "s/^[ ]*vault_key_ocid/# vault_key_ocid/" $PROJECT_DIR/terraform.tfvars        
      unset TF_VAR_vault_ocid
      unset TF_VAR_vault_key_ocid
    else
      read_ocid TF_VAR_vault_ocid "Vault" ocid1.vault
      read_ocid TF_VAR_vault_key_ocid "Vault" ocid1.key
    fi     
  fi    

  # OCIDs
  read_ocid TF_VAR_vcn_ocid "Virtual Cloud Network (VCN)" ocid1.vcn 
  read_ocid TF_VAR_web_subnet_ocid "Web Subnet" ocid1.subnet
  read_ocid TF_VAR_app_subnet_ocid "App Private Subnet" ocid1.subnet
  read_ocid TF_VAR_db_subnet_ocid "Database Private Subnet" ocid1.subnet
  # XXXXX
  read_ocid TF_VAR_oke_ocid "Kubernetes Cluster (OKE)" ocid1.cluster
  read_ocid TF_VAR_atp_ocid "Autonomous Datababase" ocid1.autonomousdatabase
  read_ocid TF_VAR_db_ocid "Base Database" ocid1.dbsystem
  read_ocid TF_VAR_mysql_ocid "MySQL" ocid1.mysqldbsystem
  read_ocid TF_VAR_psql_ocid "PostgreSQL" ocid1.postgresqldbsystem
  read_ocid TF_VAR_opensearch_ocid "OpenSearch" ocid1.opensearchcluster
  read_ocid TF_VAR_nosql_ocid "NoSQL Table" ocid1.nosqltable
  read_ocid TF_VAR_oic_ocid "Integration" ocid1.integrationinstance
  read_ocid TF_VAR_apigw_ocid "API Gateway" ocid1.apigateway
  read_ocid TF_VAR_fnapp_ocid "Function Application" ocid1.fnapp
  read_ocid TF_VAR_log_group_ocid "Log Group" ocid1.loggroup
  read_ocid TF_VAR_bastion_ocid "Bastion Instance" ocid1.instance
  # ? # read_ocid TF_VAR_vault_secret_authtoken_ocid "Enter your Private Subnet OCID" ocid1.subnet

  # -- terraform.tfvars
  # Do not stop if __TO_FILL__ are not replaced if TF_VAR_group_name exist in env variable
  # XXX -> It would be safer to check also for TF_VAR_xxx containing __TO_FILL__ too

  if declare -p | grep -q "__TO_FILL__"; then
    echo
    echo "ERROR: missing environment variables"
    echo
    declare -p | grep __TO_FILL__
    echo
    echo "Edit the file terraform.tfvars. Some variables needs to be filled:" 
    cat terraform.tfvars | grep __TO_FILL__
    error_exit "Missing environment variables."
  fi 
fi 
