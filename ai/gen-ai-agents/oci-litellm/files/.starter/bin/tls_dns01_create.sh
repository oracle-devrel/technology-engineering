#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh"
  exit 1
fi  
cd $PROJECT_DIR

. starter.sh env -silent
. $BIN_DIR/tls/dns_shared_function.sh
title "Certificate - Create using DNS01"

# Start OCI Commands in Backgroud waiting from files coming from certbot 
# (Since Certbot Docker has not OCI CLI access)
$BIN_DIR/tls/dns_oci_background.sh > $TARGET_DIR/dns_oci_background.log 2>&1 &

if [ "$TF_VAR_dns_name" == "" ]; then
  echo "ERROR: TF_VAR_dns_name not defined"
  exit 1
fi

# Delete the directory in case of a previous run
if [ -d $TARGET_DIR/certbot_shared ]; then
  rm -Rf $TARGET_DIR/certbot_shared
fi   
mkdir -p $TARGET_DIR/certbot_shared
cp $BIN_DIR/tls/dns* $TARGET_DIR/certbot_shared/.

# docker run -it --rm --name certbot --entrypoint /bin/sh certbot/certbot
docker run -it --rm --name certbot -v "$TARGET_DIR/certbot_shared:/certbot_shared" --entrypoint /bin/sh certbot/certbot /certbot_shared/dns_certbot_entrypoint.sh $TF_VAR_dns_name

# Copy the certificate directory to src/tls
if [ -d $TARGET_DIR/certbot_shared/$TF_VAR_dns_name ]; then
  mkdir -p $PROJECT_DIR/src/tls
  cp -R $TARGET_DIR/certbot_shared/$TF_VAR_dns_name $PROJECT_DIR/src/tls/.
  rm -R $TARGET_DIR/certbot_shared/$TF_VAR_dns_name
else
  echo "ERROR: certificate not found. Check for errors before."
  exit 1
fi