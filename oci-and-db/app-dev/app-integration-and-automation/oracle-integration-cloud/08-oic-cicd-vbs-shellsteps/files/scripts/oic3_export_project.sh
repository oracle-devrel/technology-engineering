#!/bin/bash
# ****************************************************************************************
# Script: oic3_export_project.sh
#
# This script is implementing comand to export project to .car file which can be used in the other OIC environment as part of CICD Implementation for OCI/OIC 
#
# Oracle 
# Created by:   Peter Obert
# Created date: 11/2024
# Updated date: 25/04/2025
# VBS adaptation: 25/04/2025
# Last updated by: Peter Obert
# Last updated date: 25/04/2025
# Last updated comments:The script is exporting project to file - adaptation based on https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/rest-endpoints.html 
#                        
# No mandatory parameters:
#  this is the script template and it is not bringing any external/run parameters to keep it as simple as possible. That can be added/modified by the user and concrete build/pipelining strategy
# 
#
# Disclaimer:
#
# You expressly understand and agree that your use of the utilities is at your sole risk and that 
# the utilities are provided on an "as is" and "as available" basis. Oracle expressly disclaims 
# all warranties of any kind, whether express or implied, including, but not limited to, the implied 
# warranties of merchantability, fitness for a particular purpose and non-infringement. 
# Any material downloaded or otherwise obtained through this delivery is done at your own discretion 
# and risk and you will be solely responsible for any damage to your computer system or loss of data 
# that results from the download of any such material.
#
# ****************************************************************************************


# get the token to access OIC REST API
response=$(curl -i  -H 'Authorization: Basic <<client_id_client_secret_basictoken>>' --request POST 'https://<<your_IDom_service>>.identity.oraclecloud.com:443/oauth2/v1/token' -H 'Content-Type:application/x-www-form-urlencoded' -d 'grant_type=client_credentials&scope=https://<<your_oic_mgmt_scope>>.integration.eu-frankfurt-1.ocp.oraclecloud.com:443/ic/api/')

access_token=$(echo "$response" | grep -o '"access_token":[^,}]*' | awk -F '"' '{print $4}')



# Check if access_token is empty or null
if [ -z "$access_token" ]; then
    echo "Failed to retrieve access token from the first API."
    exit 1
fi

echo '{"name":"my_project_name","code":"my_project_code","type":"DEVELOPED","builtBy":"","label":"01.00.0002"}' > Request_payload.json

export_project_api=$(curl -X POST -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" -d @Request_payload.json -o 'my_project_export_filename-01.00.0002.car' https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/projects/<<my_integrationproject_id>>/archive?integrationInstance=<<your_oic_instance_name>> )


# Send the GET request and capture the response headers in a separate file
response_headers=$(mktemp)
curl -X POST -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" -d @Request_payload.json -o 'my_project_export_filename-01.00.0002.car' https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/projects/<<my_integrationproject_id>>/archive?integrationInstance=<<your_oic_instance_name>> 

# Extract the HTTP status code from the response headers
http_status=$(awk 'NR==1{print $2}' "$response_headers")

# Check if the HTTP status code is 200 (OK)
if [ "$http_status" != "200" ]; then
    echo "Error: Export project failed with HTTP status code: $http_status" >&2
    exit 1
fi

echo .* *

# Clean up the temporary response headers file
rm "$response_headers"