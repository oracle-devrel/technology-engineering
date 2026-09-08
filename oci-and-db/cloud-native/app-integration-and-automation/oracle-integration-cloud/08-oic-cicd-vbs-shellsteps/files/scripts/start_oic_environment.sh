#!/bin/bash
# ****************************************************************************************
# Script: start_oic_environment.sh
#
# This script is implementing comand to start OIC environment as part of CICD Implementation for OCI/OIC - uses OCI Signature
#
# Oracle 
# Created by:   Peter Obert
# Created date: 11/2024
# Updated date: 24/04/2025
# VBS adaptation: 24/04/2025
# Last updated by: Peter Obert
# Last updated date: 24/04/2025
# Last updated comments: OCI Digital signature script is preparing preparing privatekey in path - adaptation based on https://www.ateam-oracle.com/post/oracle-cloud-infrastructure-oci-rest-call-walkthrough-with-curl. 
#                        After this build step it is expected to have running OIC environment(eg DR site)
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


tenancy_ocid="ocid1.tenancy.oc1..<<my_tenancy_id>>"

# OCID of the user making the rest call
user_ocid="ocid1.user.oc1..<<my_cicd_user_id>>"

# path to the private PEM format key for this user
privateKeyPath="./<<my_priv_key_filename>>.pem"

# fingerprint of the private key for this user
fingerprint="<<my_cicd_user_finger_print>>"

# The REST api you want to call, with any required paramters.
rest_api="/20190131/integrationInstances/<<oic_ocid>>/actions/start"

# The host you want to make the call against
host="integration.eu-amsterdam-1.ocp.oraclecloud.com"

# the json file containing the data you want to POST to the rest endpoint
body="./empty-request.json"
####################################################################################
touch ./empty-request.json

# extra headers required for a POST/PUT request
body_arg=(--data-binary @${body})
content_sha256="$(openssl dgst -binary -sha256 < $body | openssl enc -e -base64)";
content_sha256_header="x-content-sha256: $content_sha256"
content_length="$(wc -c < $body | xargs)";
content_length_header="content-length: $content_length"
headers="(request-target) date host"
# add on the extra fields required for a POST/PUT
headers=$headers" x-content-sha256 content-type content-length"
content_type_header="content-type: application/json";

date=`date -u "+%a, %d %h %Y %H:%M:%S GMT"`
date_header="date: $date"
host_header="host: $host"
request_target="(request-target): post $rest_api"

# note the order of items. The order in the signing_string matches the order in the headers, including the extra POST fields
signing_string="$request_target\n$date_header\n$host_header"
# add on the extra fields required for a POST/PUT
signing_string="$signing_string\n$content_sha256_header\n$content_type_header\n$content_length_header"




echo "====================================================================================================="
printf '%b' "signing string is $signing_string \n"
signature=`printf '%b' "$signing_string" | openssl dgst -sha256 -sign $privateKeyPath | openssl enc -e -base64 | tr -d '\n'`
printf '%b' "Signed Request is  \n$signature\n"

echo "====================================================================================================="
set -x
curl -v -X POST --data-binary "@request.json" -sS https://$host$rest_api -H "date: $date" -H "x-content-sha256: $content_sha256" -H "content-type: application/json" -H "content-length: $content_length" -H "Authorization: Signature version=\"1\",keyId=\"$tenancy_ocid/$user_ocid/$fingerprint\",algorithm=\"rsa-sha256\",headers=\"$headers\",signature=\"$signature\"" 