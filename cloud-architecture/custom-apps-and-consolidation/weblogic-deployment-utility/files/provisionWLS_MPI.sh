#!/bin/bash
# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: Creates Resource manager stack to provision WLS MPI Image . Scripts call custom python utility to convert XLS file to JSON. 
# Validates JSON and use it to create Weblogic MPI Stack in OCI.

# @author: Vasudeva Manikandan


echo "Converting EXCEL to JSON"
python3 xls_to_json.py

# Validate JSON

echo "Validating JSON\n"

./valiJSON.sh

# Get Compartment ID
comp_ocid=`cat input.json | jq .compartment_ocid | tr -d \"`

echo -n "Enter Stack Name: "
read displayname

echo -n "Enter Stack Description: "
read description

# Create Stack 

oci resource-manager stack create --config-source TF_BaseTemplate.zip --compartment-id ${comp_ocid} --display-name "${displayname}" --description "${description}" --terraform-version "1.1.x" | tee data.json

stack_id=`cat data.json | jq '.data.id' | tr -d \"`

echo "Updating Job with input.json"

oci resource-manager stack update --stack-id ${stack_id} --variables file://input.json 

echo "Plan Your Job ..."

oci resource-manager job create-plan-job --stack-id ${stack_id} --config-file /home/opc/.oci/config 


