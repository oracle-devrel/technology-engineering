#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

. ./env.sh

cd OCI_GenAI_access_gateway
source myenv/bin/activate
cd app
# python app.py
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 600 --bind 0.0.0.0:8080 2>&1 | tee ../../app_openai_gtw.log


