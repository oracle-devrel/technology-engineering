#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh upgrade"
  exit 1
fi  
cd $PROJECT_DIR


if cat env.sh | grep -q "PROJECT_DIR="; then
  . env.sh -no-auto
else
  . starter.sh env -no-auto
fi

title "OCI Starter - Upgrade"

export UPGRADE_DIR=$PROJECT_DIR/upgrade
if [ -d upgrade ]; then
  echo "ERROR: $UPGRADE_DIR exists already"
  exit
fi

if [ "$1" != "--auto-approve" ]; then
  echo "Warning: Use at your own risk."
  echo "Upgrade the bin directory (OCI-Starter) to the latest one."
  read -p "Do you want to proceed? (yes/no) " yn

  case $yn in 
  	yes ) echo Upgrading;;
	no ) echo Exiting...;
		exit;;
	* ) echo Invalid response;
		exit 1;;
  esac
fi

# if cat env.sh | grep -q "PROJECT_DIR="; then
#   . env.sh
# else
#   . starter.sh env
# fi

if [ -d $TARGET_DIR ]; then
  echo
  read -p "Warning: Target dir detected. Are you sure that you want to continue (yes/no) " yn
  case $yn in 
  	yes ) echo Upgrading;;
	no ) echo Exiting...;
		exit;;
	* ) echo Invalid response;
		exit 1;;
  esac
fi

title "Remove variable that should not be exposed"

# Version 4.0
if [ -f src/terraform/build.tf ]; then
  # PARSING_STATE:
  # 0 = Before finding '# Fixed'
  # 1 = Currently parsing 'echo_export' lines
  # 2 = Parsing complete (stop state)
  PARSING_STATE=0

  # Read the file line by line
  while IFS= read -r LINE;do
    # --- State 0: Looking for the starting point ---
    if [ "$PARSING_STATE" -eq 0 ]; then
      if [[ "$LINE" == *"# Fixed"*  ]]; then
        PARSING_STATE=1
        continue
      fi
      continue
    fi

    # --- State 1: Currently Parsing ---
    if [ "$PARSING_STATE" -eq 1 ]; then
      if [[ "$LINE" =~ echo_export[[:space:]]+\"([^\"]+)\"[[:space:]]+\"([^\"]+)\"$ ]]; then
        # BASH_REMATCH[1] holds the content of the first capture group (KEY)
        KEY="${BASH_REMATCH[1]}"
        # BASH_REMATCH[2] holds the content of the second capture group (VALUE)
        VALUE="${BASH_REMATCH[2]}"
        # Output the required export command
        echo "export $KEY=\"$VALUE\""
        export $KEY=$VALUE
      else
        # Stop reading when a line does not match the expected pattern
        PARSING_STATE=2
        break
      fi
    fi
  done < "src/terraform/build.tf"
fi

# Version 4.0
if grep -q OCI_STARTER_VERSION terraform.tfvars; then
  export LINE_OCI_STARTER_CREATION_DATE=`grep "OCI_STARTER_CREATION_DATE=" terraform.tfvars`
  export LINE_OCI_STARTER_VERSION=`grep "OCI_STARTER_VERSION=" terraform.tfvars`
fi

export `compgen -A variable | grep _ocid | grep _ocid | sed 's/$/=__TO_FILL__/'`
export TF_VAR_db_password=__TO_FILL__
export TF_VAR_auth_token=__TO_FILL__

# Version 3.0
if [ "$TF_VAR_OCI_STARTER_PARAMS" != "" ]; then
  OCI_STARTER_PARAMS=$TF_VAR_OCI_STARTER_PARAMS
fi

PARAM_LIST=""

IFS=','
read -ra ARR <<<"$OCI_STARTER_PARAMS" 
for p in "${ARR[@]}"; 
do  
  VAR_NAME="TF_VAR_${p}"
  VAR_VALUE=${!VAR_NAME}
  echo "$p - $VAR_NAME - $VAR_VALUE"
  if [ "$VAR_VALUE" != "" ]; then
    PARAM_LIST="${PARAM_LIST}${p}=${!VAR_NAME}&"
  fi
done
PARAM_LIST=`echo $PARAM_LIST|sed 's/&$//'`

title "Call OCI Starter Website to get the latest OCI starter script with the same parameters"
echo "curl -k https://www.ocistarter.com/app/zip?$PARAM_LIST"


cd $PROJECT_DIR
mkdir $UPGRADE_DIR
cd $UPGRADE_DIR
curl -k "https://www.ocistarter.com/app/zip?$PARAM_LIST" --output upgrade.zip
unzip upgrade.zip
rm upgrade.zip
mv $TF_VAR_prefix/* $TF_VAR_prefix/.*  .
rmdir $TF_VAR_prefix

title "Upgrade directory"
mkdir not_used
mv src not_used
echo "Saved $UPGRADE_DIR/src to $UPGRADE_DIR/not_used/src"

if [ -f env.sh ]; then
  mv env.sh not_used
  echo "Saved $UPGRADE_DIR/env.sh to $UPGRADE_DIR/not_used/env.sh"
else
  mv terraform.tfvars not_used
  echo "Saved $UPGRADE_DIR/terraform.tfvars to $UPGRADE_DIR/not_used/terraform.tfvars"
fi

cp -r ../src .
echo "Replaced the $UPGRADE_DIR/src directory by src"

if [ -f ../env.sh ]; then
  cp ../env.sh .
  echo "Replaced the $UPGRADE_DIR/env.sh directory by env.sh"
  # Remove lines in env.sh
  title "Removing unneeded lines in env.sh"
  sed -i "/PROJECT_DIR=/d" env.sh
  sed -i "/export BIN_DIR=/d" env.sh
  sed -i "/# Get other env variables/d" env.sh 
  sed -i '/. $BIN_DIR\/auto_env.sh/d' env.sh   
else
  cp ../terraform.tfvars .
  echo "Replaced the $UPGRADE_DIR/terraform.tfvars directory by terraform.tfvars"
  sed -i 's/deploy_type="compute"/deploy_type="public_compute"/' terraform.tfvars
fi

# Calls to env.sh
title "Replacing calls to env.sh"
function upgrade_calls_to_env_sh()
{
  FILE_NAME=$1
  FILE_PATH=`dirname -- "$FILE_NAME"`
  if [ -f $FILE_NAME ]; then
     echo "Replacing env.sh by starter.sh env in $FILE_NAME" 
     mkdir -p not_used/env/$FILE_PATH
     cp $FILE_NAME not_used/env/$FILE_PATH/.
     sed -i "s/env.sh/starter.sh env/" $FILE_NAME 
     diff not_used/env/$FILE_PATH $FILE_NAME  
  fi  
}

# Replace env.sh by starter.sh env  
for APP_DIR in `app_dir_list`; do
  upgrade_calls_to_env_sh src/$APP_DIR/build_app.sh
done
upgrade_calls_to_env_sh src/ui/build_ui.sh
# upgrade_calls_to_env_sh src/after_done.sh

# before_build.sh
if [ -f src/before_build.sh ]; then
  mv src/before_build.sh src/before_terraform.sh
fi

# after_done.sh
if [ -f src/after_done.sh ]; then
  mv src/after_done.sh src/after_build.sh
fi

# Remove *.sh from src/terraform
rm src/terraform/*.sh

if [ -f ../build.sh ]; then
  echo "Adding build.sh and destroy.sh pointing to starter.sh"
  echo './starter.sh build $@' > build.sh
  echo './starter.sh destroy $@' > destroy.sh
  chmod 755 *.sh
fi

# Repository.tf
if [ ! -f src/terraform/repository.tf ]; then
  cp not_used/src/terraform/repository.tf src/terraform/.
  echo "Container Repository in compartment: copied the new file repository.tf"
fi

echo "Done. New version in directory upgrade"
echo 

read -p "Do you want to replace the current directory by the upgrade directory ? (yes/no) " yn
echo 
case $yn in 
	yes ) cd ..
          mkdir orig
          mv * orig
          mv orig/upgrade/* .
          echo "\norig" >> .gitignore
          echo "Next steps:"
          ;;
    no ) echo "Next steps:"
         echo "cd upgrade"
         ;;
esac
echo "./starter.sh build"




