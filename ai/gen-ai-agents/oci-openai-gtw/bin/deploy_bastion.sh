#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh deploy bastion"
  exit 1
fi  
cd $PROJECT_DIR
. starter.sh env -silent

function scp_bastion() {
  if command -v rsync &> /dev/null; then
    # Using RSYNC allow to reapply the same command several times easily. 
    rsync -av -e "ssh -o StrictHostKeyChecking=no -i $TF_VAR_ssh_private_path" src/db opc@$BASTION_IP:.
  else
    scp -r -o StrictHostKeyChecking=no -i $TF_VAR_ssh_private_path src/db opc@$BASTION_IP:/home/opc/.
  fi
}

# Try 5 times to copy the files / wait 5 secs between each try
i=0
while [ true ]; do
 scp_bastion
 if [ $? -eq 0 ]; then
   break;
 elif [ "$i" == "5" ]; then
  echo "deploy_bastion.sh: Maximum number of scp retries, ending."
  error_exit
 fi
 sleep 5
 i=$(($i+1))
done

ssh -o StrictHostKeyChecking=no -i $TF_VAR_ssh_private_path opc@$BASTION_IP "export DB_USER=\"$TF_VAR_db_user\";export DB_PASSWORD=\"$TF_VAR_db_password\";export DB_URL=\"$DB_URL\"; bash db/db_init.sh 2>&1 | tee -a db/db_init.log"
exit_on_error "Deploy Bastion -"
