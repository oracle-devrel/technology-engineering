#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
. ./env.sh

source myenv/bin/activate
# litellm --port 8080 --detailed_debug 2>&1 | tee app.log
litellm --port 8080 --config config.yaml --detailed_debug 2>&1 | tee app.log
