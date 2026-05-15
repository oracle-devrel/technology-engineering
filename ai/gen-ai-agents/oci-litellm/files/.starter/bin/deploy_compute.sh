#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh deploy compute"
  exit 1
fi  
cd $PROJECT_DIR
. starter.sh env -silent

echo "COMPUTE_IP=$COMPUTE_IP"

scp_via_bastion "target/compute/*" opc@$COMPUTE_IP:/home/opc/.
ssh -o StrictHostKeyChecking=no -oProxyCommand="$BASTION_PROXY_COMMAND" opc@$COMPUTE_IP "export TF_VAR_java_version=\"$TF_VAR_java_version\";export TF_VAR_java_vm=\"$TF_VAR_java_vm\";export TF_VAR_language=\"$TF_VAR_language\";export JDBC_URL=\"$JDBC_URL\";export DB_URL=\"$DB_URL\";bash compute/compute_init.sh 2>&1 | tee -a compute/compute_init.log"
exit_on_error "Deploy Compute - ssh"
