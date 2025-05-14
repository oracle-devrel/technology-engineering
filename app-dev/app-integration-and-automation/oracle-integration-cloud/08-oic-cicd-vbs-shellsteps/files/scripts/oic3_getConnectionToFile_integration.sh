#!/bin/bash
# ****************************************************************************************
# Script: oic3_getConnectionToFile_integration.sh
#
# This script is implementing comand to get connection details and store it to the file where the payload properties can be modified and adjusted according environment. The same payload can be used to import/update the connection the OIC environment as part of CICD Implementation for OCI/OIC 
#
# Oracle 
# Created by:   Peter Obert
# Created date: 11/2024
# Updated date: 25/04/2025
# VBS adaptation: 25/04/2025
# Last updated by: Peter Obert
# Last updated date: 25/04/2025
# Last updated comments:The script is exporting connection payload to file - adaptation based on https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/rest-endpoints.html 
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

export_connectionSetUp_api=$(curl -X GET -H "Authorization: Bearer $access_token" -o '<<my_connection_name>>.json' https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/connections/<<my_connection_id>>?integrationInstance=<<your_oic_instance_name>>)


# Send the GET request and capture the response headers in a separate file
response_headers=$(mktemp)
curl -X GET -o '<<my_connection_name>>.json' -H "Authorization: Bearer $access_token" -D "$response_headers" https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/connections/<<my_connection_id>>?integrationInstance=<<your_oic_instance_name>>

# Extract the HTTP status code from the response headers
http_status=$(awk 'NR==1{print $2}' "$response_headers")

# Check if the HTTP status code is 200 (OK)
if [ "$http_status" != "200" ]; then
    echo "Error: Export connection failed with HTTP status code: $http_status" >&2
    exit 1
fi

# Clean up the temporary response headers file
rm "$response_headers"