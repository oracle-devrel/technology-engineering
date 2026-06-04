#!/usr/bin/env bash
export SRC_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export ROOT_DIR=${SRC_DIR%/*}
cd $ROOT_DIR

. ./starter.sh env

title "INSTALLATION DONE"
echo
# echo "(experimental) Cohere with Tools and GenAI Agent:"
# echo "http://${BASTION_IP}:8081/"
# echo "-----------------------------------------------------------------------"

echo "URLs" > $FILE_DONE
append_done "-----------------------------------------------------------------------"
append_done "OpenAI Gateway URLs:"
append_done "- http://${BASTION_IP}/app/v1"
append_done "- https://${APIGW_HOSTNAME}/${TF_VAR_prefix}/app/v1"
append_done
append_done "APIKEY: $TF_VAR_default_api_keys"
append_done "MODEL: dac or cohere.command-latest (see models.yaml)"
append_done
append_done "Endpoint OCID: $TF_VAR_dac_endpoint_ocid"
append_done 
append_done "curl https://${APIGW_HOSTNAME}/${TF_VAR_prefix}/app/v1/completions \\"
append_done "-H \"Content-Type: application/json\" \\"
append_done "-H \"Authorization: Bearer $TF_VAR_db_password\" \\"
append_done "-d '{\"model\": \"xxx_model_name_xxx\", \"prompt\": \"Who are you\", \"max_tokens\": 200}'"


