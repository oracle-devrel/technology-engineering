#!/usr/bin/env bash
if [ "$PROJECT_DIR" = "" ]; then
  echo "Error: PROJECT_DIR not set. Please use ./starter.sh build"
  exit 1
fi
cd $PROJECT_DIR
SECONDS=0
BUILD_MODE="ALL"

before_terraform() {
  # Custom code before terraform
  if [ -f $PROJECT_DIR/src/before_terraform.sh ]; then
    $PROJECT_DIR/src/before_terraform.sh
  fi

  # Build all
  # Generate sshkeys if not part of a Common Resources project 
  if [ "$TF_VAR_ssh_private_path" == "" ]; then
    . $BIN_DIR/sshkey_generate.sh
  fi
  
  . starter.sh env
  if [ "$TF_VAR_tls" != "" ]; then
    title "Certificate"
    certificate_dir_before_terraform
  fi  
}

terraform() {
  title "Terraform Apply"
  $BIN_DIR/terraform_apply.sh $1 -no-color 
  exit_on_error "Terraform Apply"
}

. starter.sh env -no-auto
title "OCI Starter - Build"

if [ "$1" == "--before_terraform" ]; then
  before_terraform
else
  before_terraform
  terraform $1
  title "Done"
  $BIN_DIR/done.sh
fi

