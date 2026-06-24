### Commmon functions
title() {
  line='-------------------------------------------------------------------------'
  NAME=$1
  echo
  echo "-- $NAME ${line:${#NAME}} ($SECONDS secs)"
  echo  
}

# Used in for loop for APP_DIR
app_dir_list() {
  ls -d $PROJECT_DIR/src/app* | sort -g | sed "s/.*src\///g"
}

# Java Build Common
java_build_common() {
  if [ "${OCI_CLI_CLOUD_SHELL,,}" == "true" ]; then
    # csruntimectl is a function defined in /etc/bashrc.cloudshell
    . /etc/bashrc.cloudshell
    export JAVA_ID=`csruntimectl java list | grep jdk-17 | sed -e 's/^.*\(graal[^ ]*\) .*$/\1/'`
    csruntimectl java set $JAVA_ID
  fi

  if [ -f $TARGET_DIR/jms_agent_deploy.sh ]; then
    cp $TARGET_DIR/jms_agent_deploy.sh $TARGET_DIR/compute/.
  fi

  if [ -f $PROJECT_DIR/../group_common/target/jms_agent_deploy.sh ]; then
    cp $PROJECT_DIR/../group_common/target/jms_agent_deploy.sh $TARGET_DIR/compute/.
  fi
}

build_ui() {
  cd $SCRIPT_DIR
  if is_deploy_compute; then
    mkdir -p ../../target/compute/ui
    cp -r ui/* ../../target/compute/ui/.
  elif [ "$TF_VAR_deploy_type" == "function" ]; then 
    oci os object bulk-upload -ns $TF_VAR_namespace -bn ${TF_VAR_prefix}-public-bucket --src-dir ui --overwrite --content-type auto
  else
    # Kubernetes and Container Instances
    docker image rm ${TF_VAR_prefix}-ui:latest
    docker build -t ${TF_VAR_prefix}-ui:latest .
  fi 
}

docker_login() {
  oci raw-request --region $TF_VAR_region --http-method GET --target-uri "https://${OCIR_HOST}/20180419/docker/token" | jq -r .data.token | docker login -u BEARER_TOKEN --password-stdin ${OCIR_HOST}
  exit_on_error "Docker Login"
}

build_function() {
  # Build the function
  fn create context ${TF_VAR_region} --provider oracle
  fn use context ${TF_VAR_region}
  fn update context oracle.compartment-id ${TF_VAR_compartment_ocid}
  fn update context api-url https://functions.${TF_VAR_region}.oraclecloud.com
  fn update context registry ${DOCKER_PREFIX}
  # Set pipefail to get the error despite pipe to tee
  set -o pipefail
  fn build -v | tee $TARGET_DIR/fn_build.log
  exit_on_error "build_function - fn build"

  if grep --quiet "built successfully" $TARGET_DIR/fn_build.log; then
     fn bump
     export TF_VAR_fn_image=`grep "built successfully" $TARGET_DIR/fn_build.log | sed "s/Function //" | sed "s/ built successfully.//"`
     # Push the image to docker
     docker_login
     oci artifacts container repository create --compartment-id $TF_VAR_compartment_ocid --display-name ${TF_VAR_fn_image} 2>/dev/null
     docker push $TF_VAR_fn_image
     exit_on_error "build_function - docker push"
     # Store the image name and DB_URL in files
     echo $TF_VAR_fn_image > $TARGET_DIR/fn_image.txt
  else 
     echo "build_function - built successfully not found"
     exit 1
  fi 

  if [ "$CALLED_BY_TERRAFORM" == "" ]; then
    # First create the Function using terraform
    # Run env.sh to get function image 
    cd $PROJECT_DIR
    . starter.sh env 
    $BIN_DIR/terraform_apply.sh --auto-approve
    exit_on_error "build_function - terraform apply"
  fi
}

# Create KUBECONFIG file
create_kubeconfig() {
  oci ce cluster create-kubeconfig --cluster-id $OKE_OCID --file $KUBECONFIG --region $TF_VAR_region --token-version 2.0.0  --kube-endpoint PUBLIC_ENDPOINT
  chmod 600 $KUBECONFIG
}

ocir_docker_push () {
  # Docker Login
  docker_login
  echo DOCKER_PREFIX=$DOCKER_PREFIX

  # Push image in registry
  if [ -n "$(docker images -q ${TF_VAR_prefix}-app 2> /dev/null)" ]; then
    docker tag ${TF_VAR_prefix}-app ${DOCKER_PREFIX}/${TF_VAR_prefix}-app:latest
    oci artifacts container repository create --compartment-id $TF_VAR_compartment_ocid --display-name ${DOCKER_PREFIX_NO_OCIR}/${TF_VAR_prefix}-app 2>/dev/null
    docker push ${DOCKER_PREFIX}/${TF_VAR_prefix}-app:latest
    exit_on_error "docker push APP"
    echo "${DOCKER_PREFIX}/${TF_VAR_prefix}-app:latest" > $TARGET_DIR/docker_image_app.txt
  fi

  # Push image in registry
  if [ -d $PROJECT_DIR/src/ui ]; then
    docker tag ${TF_VAR_prefix}-ui ${DOCKER_PREFIX}/${TF_VAR_prefix}-ui:latest
    oci artifacts container repository create --compartment-id $TF_VAR_compartment_ocid --display-name ${DOCKER_PREFIX_NO_OCIR}/${TF_VAR_prefix}-ui 2>/dev/null
    docker push ${DOCKER_PREFIX}/${TF_VAR_prefix}-ui:latest
    exit_on_error "docker push UI"
    echo "${DOCKER_PREFIX}/${TF_VAR_prefix}-ui:latest" > $TARGET_DIR/docker_image_ui.txt
  fi
}

replace_db_user_password_in_file() {
  # Replace DB_USER DB_PASSWORD
  CONFIG_FILE=$1
  if [ -f $CONFIG_FILE ]; then 
    sed -i "s/##DB_USER##/$TF_VAR_db_user/" $CONFIG_FILE
    sed -i "s/##DB_PASSWORD##/$TF_VAR_db_password/" $CONFIG_FILE
    sed -i "s%##JDBC_URL##%$JDBC_URL%" $CONFIG_FILE
  fi
}  

error_exit() {
  echo
  LEN=${#BASH_LINENO[@]}
  printf "%-40s %-10s %-20s\n" "STACK TRACE"  "LINE" "FUNCTION"
  for (( INDEX=${LEN}-1; INDEX>=0; INDEX--))
  do
     printf "   %-37s %-10s %-20s\n" ${BASH_SOURCE[${INDEX}]#$PROJECT_DIR/}  ${BASH_LINENO[$(($INDEX-1))]} ${FUNCNAME[${INDEX}]}
  done

  if [ "$1" != "" ]; then
    echo
    echo "ERROR: $1"
  fi
  exit 1
}

exit_on_error() {
  RESULT=$?
  if [ $RESULT -eq 0 ]; then
    echo "Success - $1"
  else
    title "EXIT ON ERROR - HISTORY - $1 "
    history 2 | cut -c1-256
    error_exit "Command Failed (RESULT=$RESULT)"
  fi  
}

auto_echo () {
  if [ -z "$SILENT_MODE" ]; then
    echo "$1"
  fi  
}

set_if_not_null () {
  if [ "$2" != "" ] && [ "$2" != "null" ]; then
    auto_echo "$1=$RESULT"
    export $1="$RESULT"
  fi  
}

get_attribute_from_tfstate () {
  RESULT=`jq -r '[.resources[] | select(.name=="'$2'") | .instances[0].attributes.'$3'][0]' $STATE_FILE`
  set_if_not_null $1 $RESULT
}

get_id_from_tfstate () {
  RESULT=`jq -r '.resources[] | select(.name=="'$2'") | select(.mode=="managed") | .instances[0].attributes.id' $STATE_FILE`
  set_if_not_null $1 $RESULT
}

get_output_from_tfstate () {
  output=$1
  if [ "${!output}" != "" ]; then
    echo "XXXXXX get_output_from_tfstate $1=${!output}"
  else 
    RESULT=`jq -r '.outputs."'$2'".value' $STATE_FILE | sed "s/ //"`
    set_if_not_null $1 $RESULT
  fi
}

# Check is the option '$1' is part of the TF_VAR_group_common
# If the app is not a group_common one, return 1==false
group_common_contain() {
  if [ "$TF_VAR_group_common" == "" ]; then
    return 1 
  fi  
  COMMON=,${TF_VAR_group_common},
  if [[ "$COMMON" == *",$1,"* ]]; then
    return 0
  else 
    return 1  
  fi
}


# Find the availability domain for a shape (ex: "VM.Standard.E2.1.Micro")
# ex: find_availabilty_domain_for_shape "VM.Standard.E2.1.Micro"
# find_availabilty_domain_for_shape() {
#   if [ "$TF_VAR_availability_domain_number" != "" ]; then
#     return 0
#   fi
#   echo "Searching for shape $1 in Availability Domains"  
#   i=1
#   for ad in `oci iam availability-domain list --compartment-id=$TF_VAR_tenancy_ocid | jq -r ".data[].name"` 
#   do
#     echo "Checking in $ad"
#     TEST=`oci compute shape list --compartment-id=$TF_VAR_compartment_ocid --availability-domain $ad | jq ".data[] | select( .shape==\"$1\" )"`
#     if [[ "$TEST" != "" ]]; then
#         echo "Found in $ad"
#         export TF_VAR_availability_domain_number=$i
#         return 0
#     fi
#     i=$((i+1))
#   done
#   echo "Error shape $1 not found" 
#   exit 1
# }

# # Guess the shape E6/E5/E4
# guess_available_shape() {
#   if [ -f $TARGET_DIR/shape.json ]; then  
#     export TF_VAR_instance_shape=`cat $TARGET_DIR/shape.json`
#     echo "Reading shape from $TARGET_DIR/shape.json ($TF_VAR_instance_shape)"
#   else
#     echo "Searching for compute shape..."  
#     i=1
#     for ad in `oci iam availability-domain list --compartment-id=$TF_VAR_tenancy_ocid | jq -r ".data[].name"` 
#     do
#         oci compute shape list --compartment-id=$TF_VAR_compartment_ocid --availability-domain $ad > $TARGET_DIR/shapes.json
#         for s in VM.Standard.E6.Flex VM.Standard.E5.Flex VM.Standard.E4.Flex; do
#         TEST=`cat $TARGET_DIR/shapes.json | jq ".data[] | select( .shape==\"$s\" )"`
#         if [[ "$TEST" != "" ]]; then
#             echo "Found Shape $s in $ad"
#             export TF_VAR_instance_shape=$s
#             echo $TF_VAR_instance_shape > $TARGET_DIR/shape.json
#             return 0
#         fi
#         done  
#         i=$((i+1))
#     done
#     error_exit "Error no shape not found" 
#   fi
# }

# Get User Details (username and OCID)
get_user_details() {
  if [ "$OCI_CLI_CLOUD_SHELL" == "True" ];  then
    if [ "$OCI_TENANCY" != "" ]; then 
      # Cloud Shell
      export TF_VAR_tenancy_ocid=$OCI_TENANCY
      export TF_VAR_region=$OCI_REGION
      # Good way to get the home_region is to get it via oci iam tenancy get --tenancy-id xxx -> home_region PREFIX (ex:FRA)
      # That needs then to be converted from prefix to name via the region list (->eu-frankfurt-1). See provider.tf.
      # export TF_VAR_home_region=`echo $OCI_CS_HOST_OCID | awk -F[/.] '{print $4}'`
      if [[ "$OCI_CS_USER_OCID" == *"ocid1.saml2idp"* ]]; then
        # Ex: ocid1.saml2idp.oc1..aaaaaaaaexfmggau73773/user@domain.com -> oracleidentitycloudservice/user@domain.com
        # Split the string in 2 
        IFS='/' read -r -a array <<< "$OCI_CS_USER_OCID"
        IDP_NAME=`oci iam identity-provider get --identity-provider-id=${array[0]} | jq -r .data.name`
        IDP_NAME_LOWER=${IDP_NAME,,}
        export TF_VAR_username="$IDP_NAME_LOWER/${array[1]}"
      elif [[ "$OCI_CS_USER_OCID" == *"ocid1.user"* ]]; then
        export TF_VAR_current_user_ocid="$OCI_CS_USER_OCID"
      else 
        export TF_VAR_username=$OCI_CS_USER_OCID
      fi
    else 
      echo "Called From Resource Manager"
      export CALLED_BY_TERRAFORM="TRUE"
      # Exported by build.tf
      export TF_VAR_ssh_private_path=$TARGET_DIR/ssh_key_starter
      export TF_VAR_ssh_public_key=$(cat $TARGET_DIR/ssh_key_starter.pub)
      export TF_VAR_ssh_private_key=$(cat $TARGET_DIR/ssh_key_starter)      
    fi
  elif [ -f $HOME/.oci/config ]; then
    ## Get the [DEFAULT] config
    if [ -z "$OCI_CLI_PROFILE" ]; then
      OCI_PRO=DEFAULT
    else 
      OCI_PRO=$OCI_CLI_PROFILE
    fi    
    sed -n -e "/\[$OCI_PRO\]/,$$p" $HOME/.oci/config > /tmp/ociconfig
    export TF_VAR_current_user_ocid=`sed -n 's/user=//p' /tmp/ociconfig |head -1`
    export TF_VAR_fingerprint=`sed -n 's/fingerprint=//p' /tmp/ociconfig |head -1`
    export TF_VAR_private_key_path=`sed -n 's/key_file=//p' /tmp/ociconfig |head -1`
    export TF_VAR_region=`sed -n 's/region=//p' /tmp/ociconfig |head -1`
    # Good way to get the home_region is to get it via oci iam tenancy get --tenancy-id xxx -> home_region PREFIX (ex:FRA)
    # That needs then to be converted from prefix to name via the region list (->eu-frankfurt-1). See provider.tf.
    # export TF_VAR_home_region=$TF_VAR_region
    export TF_VAR_tenancy_ocid=`sed -n 's/tenancy=//p' /tmp/ociconfig |head -1`  
    # echo TF_VAR_current_user_ocid=$TF_VAR_current_user_ocid
    # echo TF_VAR_fingerprint=$TF_VAR_fingerprint
    # echo TF_VAR_private_key_path=$TF_VAR_private_key_path
  elif [ "$OCI_AUTH" == "ResourcePrincipal" ]; then
    # OCI DevOps use resource principal
    # XXX Missing a lot of other variable... 
    # OCI_RESOURCE_PRINCIPAL_RPST=xxx.xxxbase64xxx.xxxx
    export TF_VAR_tenancy_ocid=`echo "${OCI_RESOURCE_PRINCIPAL_RPST#*\.}" | sed "s/\..*//" | base64 -d | jq -r .tenant`
    export TF_VAR_region=$OCI_RESOURCE_PRINCIPAL_REGION
  fi

  # Find TF_VAR_username based on TF_VAR_current_user_ocid or the opposite
  # In this order, else this is not reentrant. "oci iam user list" require more privileges.  
  if [ "$TF_VAR_current_user_ocid" != "" ]; then
    export TF_VAR_username=`oci iam user get --user-id $TF_VAR_current_user_ocid | jq -r '.data.name'`
  elif [ "$TF_VAR_username" != "" ]; then
    export TF_VAR_current_user_ocid=`oci iam user list --name $TF_VAR_username | jq -r .data[0].id`
  fi  
  auto_echo TF_VAR_username=$TF_VAR_username
  auto_echo TF_VAR_current_user_ocid=$TF_VAR_current_user_ocid
}

# Get the user interface URL
get_ui_url() {
  if [ "$TF_VAR_deploy_type" == "public_compute" ] || [ "$TF_VAR_deploy_type" == "private_compute" ] ; then
    if [ "$TF_VAR_dns_name" != "" ] && [ "$TF_VAR_tls" == "existing_ocid" ]; then
      # xx APEX ? xx
      export UI_URL=https://${TF_VAR_dns_name}/${TF_VAR_prefix}
    else 
      if [ "$TF_VAR_deploy_type" == "public_compute" ]; then
        export UI_URL=http://${COMPUTE_IP}
      else 
        export UI_URL=https://${APIGW_HOSTNAME}/${TF_VAR_prefix}
      fi    
      if [ "$TF_VAR_tls" != "" ] && [ "$TF_VAR_certificate_ocid" != "" ]; then
        export UI_HTTP=$UI_URL
        if [ "$TF_VAR_deploy_type" == "public_compute" ]; then
            export UI_URL=https://${TF_VAR_dns_name}
        else 
            export UI_URL=https://${TF_VAR_dns_name}/${TF_VAR_prefix}
        fi    
      fi
    fi  
  elif [ "$TF_VAR_deploy_type" == "instance_pool" ]; then
    export UI_URL=http://${INSTANCE_POOL_LB_IP}
    if [ "$TF_VAR_tls" != "" ] && [ "$TF_VAR_certificate_ocid" != "" ]; then
      export UI_HTTP=$UI_URL
      export UI_URL=https://${TF_VAR_dns_name}
    fi
  elif [ "$TF_VAR_deploy_type" == "kubernetes" ]; then
    if [ ! -f $KUBECONFIG ]; then
      create_kubeconfig  
    fi 
    export TF_VAR_ingress_ip=`kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath="{.status.loadBalancer.ingress[0].ip}"`
    export UI_URL=http://${TF_VAR_ingress_ip}/${TF_VAR_prefix}
    if [ "$TF_VAR_tls" != "" ] && [ "$TF_VAR_dns_name" != "" ]; then
      export UI_HTTP=$UI_URL
      export UI_URL=https://${TF_VAR_dns_name}/${TF_VAR_prefix}
    fi
  elif [ "$TF_VAR_deploy_type" == "function" ] || [ "$TF_VAR_deploy_type" == "container_instance" ]; then  
    export UI_URL=https://${APIGW_HOSTNAME}/${TF_VAR_prefix}
    if [ "$TF_VAR_tls" != "" ] && [ "$TF_VAR_certificate_ocid" != "" ]; then
      export UI_HTTP=$UI_URL
      export UI_URL=https://${TF_VAR_dns_name}/${TF_VAR_prefix}
    fi   
  fi
}

is_deploy_compute() {
  if [ "$TF_VAR_deploy_type" == "public_compute" ] || [ "$TF_VAR_deploy_type" == "private_compute" ] || [ "$TF_VAR_deploy_type" == "instance_pool" ]; then
    return 0
  else
    return 1
  fi
}

livelabs_green_button() {
  # Lot of tests to be sure we are in an Green Button LiveLabs
  # compartment_ocid still undefined ? 
  if grep -q 'compartment_ocid="__TO_FILL__"' $PROJECT_DIR/terraform.tfvars; then
    # vnc_ocid still undefined ? 
    if [ "$TF_VAR_vcn_ocid" != "__TO_FILL__" ]; then
      # Variables already set
      return
    fi
    # In cloud shell ? 
    if [ -z $OCI_CLI_CLOUD_SHELL ]; then 
      return
    fi
    # Whoami user format ? 
    W=$(whoami)
    W=${W^^}
    if [[ $W =~ ^LL.*_U.* ]]; then
      echo "LiveLabs - Green Button - whoami format detected"
    else
      return
    fi
    get_user_details
    # OCI User name format ? 
    if [[ $TF_VAR_username =~ ^LL.*-USER$ ]]; then
      echo "LiveLabs - Green Button - OCI User detected"
    else
      return
    fi

    export USER_BASE=`echo "${TF_VAR_username/-USER/}"` 
    echo USER_BASE=$USER_BASE

    export TF_VAR_compartment_ocid=`oci iam compartment list --compartment-id-in-subtree true --all | jq -c -r '.data[] | select(.name | contains("'$USER_BASE'")) | .id'`
    echo TF_VAR_compartment_ocid=$TF_VAR_compartment_ocid

    if [ "$TF_VAR_compartment_ocid" != "" ]; then
      sed -i "s&compartment_ocid=\"__TO_FILL__\"&compartment_ocid=\"$TF_VAR_compartment_ocid\"&" $PROJECT_DIR/terraform.tfvars
      echo "TF_VAR_compartment_ocid stored in terraform.tfvars"
    fi  

    export TF_VAR_vcn_ocid=`oci network vcn list --compartment-id $TF_VAR_compartment_ocid | jq -c -r '.data[].id'`
    echo TF_VAR_vcn_ocid=$TF_VAR_vcn_ocid  
    if [ "$TF_VAR_vcn_ocid" != "" ]; then
      sed -i "s&vcn_ocid=\"__TO_FILL__\"&vcn_ocid=\"$TF_VAR_vcn_ocid\"&" $PROJECT_DIR/terraform.tfvars
      echo "TF_VAR_vcn_ocid stored in terraform.tfvars"
    fi  

    export TF_VAR_subnet_ocid=`oci network subnet list --compartment-id $TF_VAR_compartment_ocid | jq -c -r '.data[].id'`
    echo TF_VAR_subnet_ocid=$TF_VAR_subnet_ocid  
    if [ "$TF_VAR_subnet_ocid" != "" ]; then
      sed -i "s&web_subnet_ocid=\"__TO_FILL__\"&web_subnet_ocid=\"$TF_VAR_subnet_ocid\"&" $PROJECT_DIR/terraform.tfvars
      sed -i "s&app_subnet_ocid=\"__TO_FILL__\"&app_subnet_ocid=\"$TF_VAR_subnet_ocid\"&" $PROJECT_DIR/terraform.tfvars
      sed -i "s&db_subnet_ocid=\"__TO_FILL__\"&db_subnet_ocid=\"$TF_VAR_subnet_ocid\"&" $PROJECT_DIR/terraform.tfvars
      echo "TF_VAR_subnet_ocid stored in terraform.tfvars"
      # Set the real variables such that the first "build" works too.
      export TF_VAR_web_subnet_ocid=$TF_VAR_subnet_ocid
      export TF_VAR_app_subnet_ocid=$TF_VAR_subnet_ocid
      export TF_VAR_db_subnet_ocid=$TF_VAR_subnet_ocid
    fi  
    
    # LiveLabs support only E4 Shapes
    sed -i '/compartment_ocid=/a\instance_shape="VM.Standard.E4.Flex"' $PROJECT_DIR/terraform.tfvars
    export TF_VAR_instance_shape=VM.Standard.E4.Flex
  fi
}

lunalab() {
  if [ "$USER" == "luna.user" ]; then  
     export SUPPRESS_LABEL_WARNING=True  
     if grep -q 'compartment_ocid="__TO_FILL__"' $PROJECT_DIR/terraform.tfvars; then    
      echo "LunaLab - Luna User detected"
      export TF_VAR_compartment_ocid=$OCI_COMPARTMENT_OCID
      sed -i "s&compartment_ocid=\"__TO_FILL__\"&compartment_ocid=\"$TF_VAR_compartment_ocid\"&" $PROJECT_DIR/terraform.tfvars     
      export TF_VAR_instance_shape="VM.Standard.E5.Flex"
      sed -i '/compartment_ocid=/a\instance_shape="VM.Standard.E5.Flex"' $PROJECT_DIR/terraform.tfvars     
      export TF_VAR_no_policy="true"      
      sed -i '/compartment_ocid=/a\no_policy="true"' $PROJECT_DIR/terraform.tfvars
    fi    
  fi 
}

create_deployment_in_apigw() {
# Publish the API with an API Deployment to API Gateway
  if [ "$APIGW_DEPLOYMENT_OCID" != "" ]; then
   cat > $TARGET_DIR/api_deployment.json << EOF
{
  "loggingPolicies": {
    "accessLog": {
      "isEnabled": true
    },
    "executionLog": {
      "isEnabled": true,
      "logLevel": "string"
    }
  },  
  "routes": [
    {
      "path": "/app/{pathname*}",
      "methods": [ "ANY" ],
      "backend": {
        "type": "HTTP_BACKEND",
        "url": "$UI_URL/app/dept"
      }
    }
  ]
}
EOF
   oci api-gateway deployment create --compartment-id $TF_VAR_compartment_ocid --display-name "${TF_VAR_prefix}-apigw-deployment" --gateway-id $APIGW_DEPLOYMENT_OCID \
      --path-prefix "/${TF_VAR_prefix}" --specification file://$TARGET_DIR/api_deployment.json
  fi
}

configure() {
  if cat env.sh | grep -q "__TO_FILL__"; then
    echo Found these variables:
    cat env.sh | grep -q "__TO_FILL__"
    echo
    echo "Configure Mode"
    echo 
    echo 
    if [ "$1" != "--auto-approve" ]; then
      read -p "Do you want to proceed? (yes/no) " yn

      case $yn in 
        yes ) echo Configuring;;
      no ) echo Exiting...;
        exit;;
      * ) echo Invalid response;
        exit 1;;
      esac
    fi
  fi
} 

java_get_version() {
  JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
  JAVA_VERSION_NUMBER=$(echo $JAVA_VERSION | awk -F '.' '{print $1}')
}

java_home_exists() {
  if [ -d /$1 ]; then
    export JAVA_HOME=$1
    export PATH=$JAVA_HOME/bin:$PATH
    java -version
    return 0 
  fi
  echo "Not Found $1"
  return 1
}

java_check_exact_version() {
  java_get_version
  if [[ "$1" = "$JAVA_VERSION_NUMBER" ]]; then
    echo "Check Java Version OK: Request: $1 = Found: $JAVA_VERSION_NUMBER"
  else 
    echo "Check Java Version FAILED: Request: $1 != Found $JAVA_VERSION_NUMBER"
    exit 1
  fi
}

java_find_version() {
  JAVA_REQUEST=$1
  java_get_version
  if [[ "$JAVA_VERSION_NUMBER" < "$JAVA_REQUEST" ]]; then
    echo "Java Version too small: Found $JAVA_VERSION_NUMBER < Request: $JAVA_REQUEST"
    echo "Trying to find version $1 in standard Java directory"
    if java_home_exists /usr/lib64/graalvm/graalvm-java$JAVA_REQUEST; then
       return;
    fi; 
    if java_home_exists /usr/java/jdk-$JAVA_REQUEST; then
       return;
    fi; 
    echo "Not found"
    exit 1
  else 
    echo "Check Java Version OK: Request: $JAVA_REQUEST <= Found: $JAVA_VERSION_NUMBER"
  fi
}

# Get the validity of the certificate $TF_VAR_certificate_ocid
get_certificate_validity() {
  CERT_DATE_VALIDITY=`oci certs-mgmt certificate get --certificate-id $TF_VAR_certificate_ocid | jq -r '.data["current-version"].validity["time-of-validity-not-after"]'`
  CERT_VALIDITY_DAY=`echo $((($(date -d $CERT_DATE_VALIDITY +%s) - $(date +%s))/86400))`
  echo "Certificate valid until: $CERT_DATE_VALIDITY"
  echo "Days left: $CERT_VALIDITY_DAY"
}

# Create or Update with name $TF_VAR_dns_name with the certificate contained in $TF_VAR_certificate_dir
certificate_create_update() {
  echo "Creating or Updating certificate $TF_VAR_dns_name"
  CERT_CERT=$(cat $TF_VAR_certificate_dir/cert.pem)
  CERT_CHAIN=$(cat $TF_VAR_certificate_dir/chain.pem)
  CERT_PRIVKEY=$(cat $TF_VAR_certificate_dir/privkey.pem)
  if [ "$TF_VAR_certificate_ocid" == "" ]; then
    oci certs-mgmt certificate create-by-importing-config --compartment-id=$TF_VAR_compartment_ocid  --name=$TF_VAR_dns_name --cert-chain-pem="$CERT_CHAIN" --certificate-pem="$CERT_CERT"  --private-key-pem="$CERT_PRIVKEY" --wait-for-state ACTIVE --wait-for-state FAILED
  else
    oci certs-mgmt certificate update-certificate-by-importing-config-details --certificate-id=$TF_VAR_certificate_ocid --cert-chain-pem="$CERT_CHAIN" --certificate-pem="$CERT_CERT"  --private-key-pem="$CERT_PRIVKEY" --wait-for-state ACTIVE --wait-for-state FAILED
  fi
  exit_on_error "oci certs-mgmt"
  TF_VAR_certificate_ocid=`oci certs-mgmt certificate list --all --compartment-id $TF_VAR_compartment_ocid --name $TF_VAR_dns_name | jq -r .data.items[0].id`
}

# Create a new certificate with DNS01
certificate_dns01_create () {
  $BIN_DIR/tls_dns01_create.sh 
  exit_on_error "certificate_dns01_create"
  export TF_VAR_certificate_dir=$PROJECT_DIR/src/tls/$TF_VAR_dns_name  
}

certificate_dir_before_terraform() {
  if [ "$TF_VAR_dns_name" == "" ]; then
    echo "ERROR: certificate_dir_before_terraform: TF_VAR_dns_name not defined"
    exit 1
  fi
  if [ -d $PROJECT_DIR/src/tls/$TF_VAR_dns_name ]; then
    export TF_VAR_certificate_dir=$PROJECT_DIR/src/tls/$TF_VAR_dns_name
    echo Using existing TF_VAR_certificate_dir=$TF_VAR_certificate_dir
  elif [ "$TF_VAR_certificate_dir" != "" ]; then
    # Check if the directory exists
    if [ -d $TF_VAR_certificate_dir ]; then
      echo Using existing TF_VAR_certificate_dir=$TF_VAR_certificate_dir
    else
      echo "ERROR: TF_VAR_certificate_dir directory does not exist ( $TF_VAR_certificate_dir )"
      exit 1
    fi
  elif [ "$TF_VAR_tls" == "new_dns_01" ]; then
    # If there is already a TF_VAR_certificate_ocid, check if it is still valid
    if [ "$TF_VAR_certificate_ocid" != "" ]; then
      get_certificate_validity
      if [ "$CERT_VALIDITY_DAY" -lt "0" ]; then
        echo "Certificate $TF_VAR_certificate_ocid expired. Need to renew it."
      fi
      certificate_dns01_create 
      certificate_create_update
    else
      certificate_dns01_create 
    fi
  fi

  if [ "$TF_VAR_deploy_type" == "public_compute" ] || [ "$TF_VAR_deploy_type" == "private_compute" ]; then
    if [ -d target/compute/certificate ]; then
      echo "Certificate Directory exists already" 
    elif [ "$TF_VAR_certificate_dir" != "" ]; then
      mkdir -p target/compute/certificate
      cp $TF_VAR_certificate_dir/* target/compute/certificate/.
      cp src/tls/nginx_tls.conf target/compute/.
      sed -i "s/##DNS_NAME##/$TF_VAR_dns_name/" target/compute/nginx_tls.conf
    elif [ "$TF_VAR_tls" == "new_http_01" ]; then
      echo "New Certificate will be created after the deployment."      
    else 
      echo "ERROR: compute: certificate_dir_before_terraform: missing variables TF_VAR_certificate_dir"
      exit 1
    fi
  elif [ "$TF_VAR_deploy_type" == "kubernetes" ]; then
    if [ "$TF_VAR_tls" == "new_http_01" ]; then
      echo "New Certificate will be created after the deployment."      
    elif [ "$TF_VAR_certificate_dir" == "" ]; then
      echo "ERROR: kubernetes: certificate_dir_before_terraform: missing variables TF_VAR_certificate_dir"
      exit 1
    fi    
  elif [ "$TF_VAR_certificate_ocid" == "" ] && [ "$TF_VAR_certificate_dir" != "" ] ;  then
    certificate_create_update
  elif [ "$TF_VAR_certificate_ocid" != "" ]; then
    get_certificate_validity
    if [ "$CERT_VALIDITY_DAY" -lt "0" ]; then
      error_exit "Invalid Certificate $TF_VAR_certificate_ocid. Delete or renew the certificate."
    fi
  else 
    error_exit "certificate_dir_before_terraform: missing variables TF_VAR_certificate_ocid or TF_VAR_certificate_dir"
  fi  
}

# Certificate - Post Deploy
certificate_post_deploy() {
  if [ "$TF_VAR_tls" == "new_http_01" ]; then
    if [ "$TF_VAR_deploy_type" == "public_compute" ] || [ "$TF_VAR_deploy_type" == "private_compute" ]; then
      certificate_run_certbot_http_01
    elif [ "$TF_VAR_deploy_type" == "kubernetes" ]; then
      echo "Skip: TLS - Kubernetes - HTTP_01"
    fi
  elif [ "$TF_VAR_deploy_type" == "kubernetes"  ]; then
    # Set the TF_VAR_ingress_ip
    get_ui_url 
    $BIN_DIR/terraform_apply.sh --auto-approve -no-color
    exit_on_error "certificate_post_deploy - terraform apply"
  fi  
}

# Generate a certificate on compute
certificate_run_certbot_http_01()
{
  if [ -z "$TF_VAR_certificate_email" ]; then
    error_exit "TF_VAR_certificate_email is not defined."
  fi   

  # Generate the certificate with Let'Encrypt on the COMPUTE
  scp_via_bastion src/tls opc@$COMPUTE_IP:/home/opc/.
  ssh -o StrictHostKeyChecking=no -oProxyCommand="$BASTION_PROXY_COMMAND" opc@$COMPUTE_IP "export TF_VAR_dns_name=\"$TF_VAR_dns_name\";export TF_VAR_certificate_email=\"$TF_VAR_certificate_email\"; bash tls/certbot_http_01.sh 2>&1 | tee -a tls/certbot_http_01.log"
  scp_via_bastion opc@$COMPUTE_IP:tls/certificate target/.
  export TF_VAR_certificate_dir=$PROJECT_DIR/target/certificate/$TF_VAR_dns_name
}

# SCP via Bastion
function scp_via_bastion() {
  eval "$(ssh-agent -s)"
  ssh-add $TF_VAR_ssh_private_path

  # Try 5 times to copy the files / wait 5 secs between each try
  echo "scp_via_bastion"
  i=0
  while [ true ]; do
    if command -v rsync &> /dev/null; then
      # Using RSYNC allow to reapply the same command several times easily. 
      rsync -av -e "ssh -o StrictHostKeyChecking=no -oProxyCommand=\"$BASTION_PROXY_COMMAND\"" $1 $2
    else
      scp -r -o StrictHostKeyChecking=no -oProxyCommand="$BASTION_PROXY_COMMAND" $1 $2
    fi  
    if [ $? -eq 0 ]; then
      echo "-- done"
      break;
    elif [ "$i" == "5" ]; then
      echo "scp_via_bastion: Maximum number of scp retries, ending."
      error_exit
    fi
  sleep 5
  i=$(($i+1))
  done
}

# Function to replace ##VARIABLES## in a file
file_replace_variables() {
  local file="$1"
  local temp_file=$(mktemp)

  echo "Replace variables in file: $1"
  while IFS= read -r line; do
    while [[ $line =~ (.*)##(.*)##(.*) ]]; do
      local var_name="${BASH_REMATCH[2]}"
      echo "- variable: ${var_name}"
      local var_value="${!var_name}"

      if [[ -z "$var_value" ]]; then
        echo "ERROR: Environment variable '${var_name}' is not defined."
        error_exit
      fi

      line=${line/"##${var_name}##"/${var_value}}
    done

    echo "$line" >> "$temp_file"
  done < "$file"

  mv "$temp_file" "$file"
}

# done.txt
FILE_DONE=$TARGET_DIR/done.txt
append_done() {
  echo "$1" >> $FILE_DONE
}