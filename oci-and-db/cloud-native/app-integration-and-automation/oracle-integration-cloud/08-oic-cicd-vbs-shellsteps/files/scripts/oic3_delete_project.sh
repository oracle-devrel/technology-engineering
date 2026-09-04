#!/bin/bash
# ****************************************************************************************
# Script: oic3_delete_project.sh
#
# This script is implementing comand to delete project from OIC environment - to be able later e.g. import .car file which can be used in the OIC environments as part of CICD Implementation for OCI/OIC 
#
# Oracle 
# Created by:   Peter Obert
# Created date: 11/2024
# Updated date: 25/04/2025
# VBS adaptation: 25/04/2025
# Last updated by: Peter Obert
# Last updated date: 25/04/2025
# Last updated comments:The script is deleting project from OIC - adaptation based on https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/rest-endpoints.html 
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


#delete_project_api=$(curl -X DELETE -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/projects/ORCL-R-ERP_MSEMAIL_ORDERFULFILL/archive?integrationInstance=<<your_oic_instance_name>> )

delete_project_api=$(curl -s -w "%{http_code}" -X DELETE -H "Authorization: Bearer $access_token" -H "Content-Type: application/json" https://design.integration.eu-frankfurt-1.ocp.oraclecloud.com/ic/api/integration/v1/projects/<<my_integrationproject_id>>?integrationInstance=<<your_oic_instance_name>> )


http_code=$(tail -n1 <<< "$delete_project_api")  # get the last line

# Check if the delete_project_api response is with no content
if [[ $http_code == 200  ]] 
then
    echo "Integration project delete succeeded" >&2
else 
    echo "Error: Integration schedule delete failed with Response: $delete_project_api" >&2
    exit 1
fi
exit 0