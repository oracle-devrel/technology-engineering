#!/usr/bin/env bash
#
# starter.sh proxy. Run the real starter.sh 
# - in $PROJECT_DIR/bin
# - or in $PATH
#
export PROJECT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ -f $PROJECT_DIR/bin/starter.sh ]; then
  export PATH=$PROJECT_DIR/bin:$PATH
fi  

(return 0 2>/dev/null) && SOURCED=1 || SOURCED=0
if [ "$SOURCED" == "1" ]; then
  . starter.sh $@
else
  starter.sh $@
  exit ${PIPESTATUS[0]}
fi
