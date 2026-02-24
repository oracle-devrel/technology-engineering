#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh ssh bastion"
  exit 1
fi  
cd $PROJECT_DIR
. starter.sh env

ssh opc@$BASTION_IP -i $TF_VAR_ssh_private_path
