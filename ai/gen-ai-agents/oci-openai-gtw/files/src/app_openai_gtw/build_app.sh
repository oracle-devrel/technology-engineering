#!/usr/bin/env bash
# Build_app.sh
#
# Compute:
# - build the code 
# - create a $ROOT/target/compute/$APP_DIR directory with the compiled files
# - and a start.sh to start the program
# Docker:
# - build the image
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. $SCRIPT_DIR/../../starter.sh env -no-auto
. $BIN_DIR/build_common.sh

## XXXXX Check Language version

if is_deploy_compute; then
  mkdir -p ../../target/compute/$APP_DIR
  cp -r src/* ../../target/compute/$APP_DIR/.
  # Replace the user and password in the start file
  replace_db_user_password_in_file ../../target/compute/$APP_DIR/start.sh
  if [ -f $TARGET_DIR/compute/$APP_DIR/env.sh ]; then 
    file_replace_variables $TARGET_DIR/compute/$APP_DIR/env.sh
  fi 
else
  docker image rm ${TF_VAR_prefix}-app:latest
  docker build -t ${TF_VAR_prefix}-app:latest .
  exit_on_error "docker build"
fi  