#!/bin/bash
# ****************************************************************************************
# Script: prepare_pem_for_builds.sh
#
# This script is used as prerequisite/part of CI Implementation for OCI/OIC to get and store private PEM key necessary to compose OCI Signature. content can be replaced by e.g. retrieval of the key from the git or key vault or so.
#
# Oracle 
# Created by:   Peter Obert
# Created date: 11/2024
# Updated date: 24/04/2025
# VBS adaptation: 24/04/2025
# Last updated by: Peter Obert
# Last updated date: 24/04/2025
# Last updated comments: OCI Digital signature script preparing privatekey in path - adaptation based on https://www.ateam-oracle.com/post/oracle-cloud-infrastructure-oci-rest-call-walkthrough-with-curl. 
#                        After this build step is expected to archive *.pem to be available for the follow-up build steps
# No mandatory parameters:
#  this can be custom iplementation that will deliver the private key which can be used in follow-up steps with OCI cURL commands with OCI Signature
# 
#
# Disclaimer:
#
# You expressly understand and agree that your use of the utilities is at your sole risk and that 
# the utilities are provided on an "as is" and "as available" basis. Oracle expressly disclaims 
# all warranties of any kind, whether express or implied, including, but not limited to, the implied 
# warranties of merchantability, fitness for a particular purpose and non-infringement. 
# Any material downloaded or otherwise obtained through this deliver is done at your own discretion 
# and risk and you will be solely responsible for any damage to your computer system or loss of data 
# that results from the download of any such material.
#
# ****************************************************************************************


echo "-----BEGIN RSA PRIVATE KEY-----
yourkeyContent
-----END RSA PRIVATE KEY-----" > ./oci_cicduser@oracle.com_api_key_priv.pem
