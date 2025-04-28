#!/bin/bash
# ****************************************************************************************
# Script: oic3_stopSchedule_project_integration.sh
#
# This script is implementing comand to stop a schedule for the project integration - OIC environment as part of CICD Implementation for OCI/OIC or example of trigger integration on system event
#
# Oracle 
# Created by:   Peter Obert
# Created date: 04/2025
# Updated date: 25/04/2025
# VBS adaptation: 25/04/2025
# Last updated by: Peter Obert
# Last updated date: 28/04/2025
# Last updated comments:The script is stopping a schedule for the project integration - adaptation based on https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/rest-endpoints.html 
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
response=$(curl -i  -H 'Authorization: Basic MzQ5M2QwOTAyNjg2NDc0M2E3MGRlYTVkZjMwZTljNDU6aWRjc2NzLTExMGNhNGI5LWZkZjAtNGJkNC04ZTQyLTZlNTNjODQ0NDIxMg==' --request POST 'https://idcs-5ba32fa3496f48289532f8fc10f47032.identity.oraclecloud.com:443/oauth2/v1/token' -H 'Content-Type:application/x-www-form-urlencoded' -d 'grant_type=client_credentials&scope=https://BA3849F019F9468B9470A19274B91010.integration.eu-frankfurt-1.ocp.oraclecloud.com:443/ic/api/')

access_token=$(echo "$response" | grep -o '"access_token":[^,}]*' | awk -F '"' '{print $4}')

# Check if access_token is empty or null
if [ -z "$access_token" ]; then
    echo "Failed to retrieve access token from the first API."
    exit 1
fi

echo '{}' > ./stopschedule.json
cat ./stopschedule.json

StopSchedule_Integration_api=$(curl -X POST -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" -d @stopschedule.json https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/projects/POB_SIMPLERPA_SITETOLIST/integrations/SCHEDULED_RATES_CBUAE%7C01.00.0000/schedule/stop?integrationInstance=teamoic3-frrnyzlwrqhn-fr)



# Error handling
echo "Stop Schedule for Integration response: $StopSchedule_Integration_api"
# Error handling
http_links=$(echo "$StopSchedule_Integration_api" | jq -r '.links')
http_status=$(echo "$StopSchedule_Integration_api" | jq -r '.Schedule')

# Check if the StopSchedule_Integration_api response is with no content
if [[ -n "$http_status" || -n "$http_links" ]] 
then
    echo "Integration schedule stop succeeded/or schedule is not active with with reply: $StopSchedule_Integration_api" >&2
else 
    echo "Error: Integration schedule stop failed with Response: $StopSchedule_Integration_api" >&2
    exit 1
fi
exit 0