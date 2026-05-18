. $SCRIPT_DIR/../../starter.sh env -no-auto

# Build_common.sh
#!/usr/bin/env bash
if [ "$BIN_DIR" == "" ]; then
  echo "Error: BIN_DIR not set"
  exit 1
fi
if [ "$PROJECT_DIR" == "" ]; then
  echo "Error: PROJECT_DIR not set"
  exit 1
fi

APP_DIR=`echo ${SCRIPT_DIR} |sed -E "s#(.*)/(.*)#\2#"`
cd $SCRIPT_DIR

if [ "$TF_VAR_deploy_type" == "" ]; then
  . $PROJECT_DIR/starter.sh env
else 
  . $BIN_DIR/shared_bash_function.sh
fi 

if [ -f $PROJECT_DIR/before_build.sh ]; then
  . $PROJECT_DIR/before_build.sh
fi 
