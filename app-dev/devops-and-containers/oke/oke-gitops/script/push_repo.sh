#!/bin/bash

cat >>~/.netrc <<EOF
machine devops.scmservice.$REGION.oci.oraclecloud.com
       login $GIT_USERNAME
       password $GIT_PASSWORD
EOF

git config --global user.email "resource-manager@oracle.com"
git config --global user.name "$GIT_USERNAME"
CLONED_DIR="$(basename "$REPO_CLONE_URL" .git)"
rm -rf ./$CLONED_DIR
git clone $REPO_CLONE_URL || exit
rm -rf ./$CLONED_DIR/*
cp -a ./$SOURCE_REPO/. ./$CLONED_DIR/
cd $CLONED_DIR || exit
git add . && \
git add -u && \
git commit -m "Committed by Terraform script" && \
git push origin main

# Cleanup
rm -rf $CLONED_DIR
rm -f $CLONED_DIR.zip