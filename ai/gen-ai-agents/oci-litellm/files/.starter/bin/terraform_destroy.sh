#!/usr/bin/env bash
if [ "$PROJECT_DIR" == "" ]; then
  echo "ERROR: PROJECT_DIR undefined. Please use starter.sh terraform destroy"
  exit 1
fi  
cd $PROJECT_DIR

. starter.sh env -silent
. $BIN_DIR/shared_infra_as_code.sh
infra_as_code_destroy $@
exit_on_error "infra_as_code_destroy"
