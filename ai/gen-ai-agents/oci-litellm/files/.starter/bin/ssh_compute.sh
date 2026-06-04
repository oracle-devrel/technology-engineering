#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh ssh compute"
  exit 1
fi  
cd $PROJECT_DIR
. starter.sh env

eval "$(ssh-agent -s)"
ssh-add $TF_VAR_ssh_private_path
ssh -o StrictHostKeyChecking=no -oProxyCommand="$BASTION_PROXY_COMMAND" opc@$COMPUTE_IP