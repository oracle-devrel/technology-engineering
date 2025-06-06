#!/bin/bash
# ****************************************************************************************
# Script: oic3_runNow_integration.sh
#
# This script is implementing comand to run scheduled integration on demand now() - OIC environment as part of CICD Implementation for OCI/OIC or example of trigger integration on system event
#
# Oracle 
# Created by:   Peter Obert
# Created date: 04/2025
# Updated date: 25/04/2025
# VBS adaptation: 25/04/2025
# Last updated by: Peter Obert
# Last updated date: 28/04/2025
# Last updated comments:The script is triggering run of the scheduled integration - adaptation based on https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/rest-endpoints.html 
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


# get the token to access OIC REST API# get the token to access OIC REST API
response=$(curl -i  -H 'Authorization: Basic <<client_id_client_secret_basictoken>>' --request POST 'https://<<your_IDom_service>>.identity.oraclecloud.com:443/oauth2/v1/token' -H 'Content-Type:application/x-www-form-urlencoded' -d 'grant_type=client_credentials&scope=https://<<your_oic_mgmt_scope>>.integration.eu-frankfurt-1.ocp.oraclecloud.com:443/ic/api/')

access_token=$(echo "$response" | grep -o '"access_token":[^,}]*' | awk -F '"' '{print $4}')


# Check if access_token is empty or null
if [ -z "$access_token" ]; then
    echo "Failed to retrieve access token from the first API."
    exit 1
fi

RunNowSchedulable_Integration_api=$(curl -X POST -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" -d "{\"status\": \"ACTIVATED\"}" https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/integrations/<<my_integration_id>>%7C<<version>>/schedule/jobs?integrationInstance=<<your_oic_instance_name>>)



# Error handling
#http_response=$(echo "$RunNowSchedulable_Integration_api" | jq -r '.status')
echo "Integration run Now response: $RunNowSchedulable_Integration_api"


# Check if the RunNowSchedulable_Integration_api response is with no content
if [ -z "$RunNowSchedulable_Integration_api" ]; then
    echo "Integration run Now succeeded with with no content reply" >&2
else 
    echo "Error: Integration run Now failed with Response: $RunNowSchedulable_Integration_api" >&2
    exit 1
fi
