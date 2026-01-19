#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

STARTER_DIR=".starter"
if [ -f $STARTER_DIR/starter.sh ]; then
  echo "-- Synchronizing the source files with directory $STARTER_DIR --"
  if [ -d app ]; then
    rsync -avh app/ $STARTER_DIR/src/app
  fi
  if [ -d src ]; then
    rsync -avh src/ $STARTER_DIR/src/app/src
    if [ -f build_app.sh ]; then
      cp build_app.sh $STARTER_DIR/src/app/.
    fi
  fi
  if [ -d db ]; then
    rsync -avh db/ $STARTER_DIR/src/db
  fi
  if [ -d ui ]; then
    rsync -avh ui/ $STARTER_DIR/src/ui
  fi
  if [ -d terraform ]; then
    cp -R terraform/* $STARTER_DIR/src/terraform
  fi
  if [ -f terraform.tfvars ]; then
    rm $STARTER_DIR/terraform.tfvars
    ln -s ../terraform.tfvars $STARTER_DIR/terraform.tfvars
  fi
  if [ -f done.sh ]; then
    rm $STARTER_DIR/src/done.sh
    ln -s ../../done.sh $STARTER_DIR/src/done.sh
  fi
  # cp done.txt starter/.
  $STARTER_DIR/starter.sh $@
else
  echo "Error: $STARTER_DIR directory is missing"
fi  
exit ${PIPESTATUS[0]}

