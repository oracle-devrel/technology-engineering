#!/bin/bash
#
# Version: @(#).secure.storage.sh 1.0.0 
# License
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License (UPL), Version 1.0.
# See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
#
#@  secure.storage.sh
#@
#
# Update history:
#
# V 1.0.0 28.06.2023 initial version
#

# ---------------------------------------------------------------------------------------------------------------------------------------------
# prepare environement (load functions)
# ---------------------------------------------------------------------------------------------------------------------------------------------
: ' ---------------------------------------------------------------------------------------------------------------------------------------
To run this script, please have functions0.sh and parameter1.sh handy.
Make sure parameter1.sh is set up proper with your individual variable settings.
-------------------------------------------------------------------------------------------------------------------------------------------'
source functions0.sh

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Oracle Cloud Infrastructure CLI Command Reference - https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/
# ---------------------------------------------------------------------------------------------------------------------------------------------

MYOUTPUT="Secure Storage by Example - Preperation" && MYCOUNT=$((1)) 
if [ 1 -eq 1 ] ; then
color_print "${IGreen}" "($MYCOUNT) $(date "+%d.%m.%Y %H:%M:%S") : $MYOUTPUT"

echo "Secure Storage by example - Preperation" > "${LOG_FILE}"
echo "=====================================================================" >> "${LOG_FILE}"
echo "${PF1} $(date "+%d.%m.%Y %H:%M:%S") " >> "${LOG_FILE}"
echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"

color_print "${MYcolor}" "${PF1} create BLOCK volume"
if [ 1 -eq 1 ] ; then # create BLOCK volume

if [ ${CREATE_BLOCK_VOLUME} -eq 1 ] ; then # create block volume 
  oci --profile "${REGION_PROFILE}" bv volume create --availability-domain "${FRANKFURT_AVAILABILITY_DOMAIN}" \
  --compartment-id "${COMPARTMENT_OCID}" \
  --display-name "${FRANKFURT_BLOCK_VOLUME_NAME}" \
  --size-in-gbs 50 \
  --wait-for-state "AVAILABLE" 
fi
 
  tempfile myTEMPFILE
  oci --profile "${REGION_PROFILE}" bv volume list --compartment-id "${COMPARTMENT_OCID}" --availability-domain "${FRANKFURT_AVAILABILITY_DOMAIN}" > "${myTEMPFILE}"
  for ii in $(cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(."lifecycle-state"!="TERMINATED")] | .[]."id" ')
  do
    myOCID=$ii
    myNAME=$( cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(.'\"id\"'=='\"$ii\"')] | .[].'\"display-name\"' ' )
    if [ 0 -lt $(echo "${myNAME}" | grep "${FRANKFURT_BLOCK_VOLUME_NAME}" | wc -l)  ] ; then 
      BLOCK_VOLUME_OCID=${myOCID}
      echo "${PF1} Block Volume name.........: ${myNAME}" >> "${LOG_FILE}"
      echo "${PF1} Block Volume OCID.........: ${myOCID}" >> "${LOG_FILE}"
    fi  
  done 
fi

color_print "${MYcolor}" "${PF1} get VAULT details"
if [ 1 -eq 1 ] ; then # get VAULT details
  tempfile myTEMPFILE
  oci --profile "${REGION_PROFILE}" kms management vault get --vault-id "${VAULT_OCID}" > "${myTEMPFILE}"
  myNAME=$( cat "${myTEMPFILE}" | grep "display-name" | awk '{print $2}' |  sed 's/\"//g' | sed 's/,//g' )
  ManagementEndpoint=$( cat "${myTEMPFILE}" | grep "management-endpoint" | awk '{print $2}' |  sed 's/\"//g' | sed 's/,//g' )
  echo "${PF1} Vault name................: ${myNAME}" >> "${LOG_FILE}"
  echo "${PF1} Vault Management Endpoint.: ${ManagementEndpoint}" >> "${LOG_FILE}"

  tempfile myTEMPFILE
  oci --profile "${REGION_PROFILE}" kms management key get --key-id "${MasterEncryptionKey_OCID}" --endpoint "${ManagementEndpoint}" > "${myTEMPFILE}"
  myNAME=$( cat "${myTEMPFILE}" | grep "display-name" | awk '{print $2}' |  sed 's/\"//g' | sed 's/,//g' )
  echo "${PF1} Master Encryption Key name: ${myNAME}" >> "${LOG_FILE}"
fi

color_print "${MYcolor}" "${PF1} create BLOCK volume backup"
if [ 1 -eq 1 ] ; then # create BLOCK volume backup

if [ ${CREATE_BLOCK_VOLUME_BACKUP} -eq 1 ] ; then # create block volume backup
  oci --profile "${REGION_PROFILE}" bv backup create --volume-id "${BLOCK_VOLUME_OCID}" --display-name "${FRANKFURT_BLOCK_VOLUME_NAME}Backup" --wait-for-state "AVAILABLE"
fi
 
  tempfile myTEMPFILE
  oci --profile "${REGION_PROFILE}" bv backup list --compartment-id "${COMPARTMENT_OCID}" > "${myTEMPFILE}"
  for ii in $(cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(."lifecycle-state"!="TERMINATED")] | .[]."id" ')
  do
    myOCID=$ii
    myNAME=$( cat "${myTEMPFILE}"|jq --raw-output '.[] | [.[] | select(.'\"id\"'=='\"$ii\"')] | .[].'\"display-name\"' ' )
    if [ 0 -lt $(echo "${myNAME}" | grep "${FRANKFURT_BLOCK_VOLUME_NAME}Backup" | wc -l)  ] ; then 
      BLOCK_VOLUME_BACKUP_OCID=${myOCID}
      echo "${PF1} Block Volume Backup name..: ${myNAME}" >> "${LOG_FILE}"
      echo "${PF1} Block Volume Backup OCID..: ${myOCID}" >> "${LOG_FILE}"
    fi  
  done 
fi

echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"
echo " " >> "${LOG_FILE}"
fi


MYOUTPUT="Secure Storage with Customer-managed Key" && MYCOUNT=$(($MYCOUNT + 1))
if [ 1 -eq 1 ] ; then
color_print "${IGreen}" "($MYCOUNT) $(date "+%d.%m.%Y %H:%M:%S") : $MYOUTPUT"

: ' ---------------------------------------------------------------------------------------------------------------------------------------
Encrypt Data in Block Volumes       https://docs.oracle.com/en/solutions/oci-best-practices/protect-data-rest1.html
oci bv volume-kms-key update        https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/bv/volume-kms-key/update.html
-------------------------------------------------------------------------------------------------------------------------------------------'

echo "Secure Storage with Customer managed Key" >> "${LOG_FILE}"
echo "=====================================================================" >> "${LOG_FILE}"
echo "${PF1} $(date "+%d.%m.%Y %H:%M:%S")" >> "${LOG_FILE}"
echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"

color_print "${MYcolor}" "${PF1} BLOCK volume change from Oracle-managed Key to Customer-managed Key"
if [ 1 -eq 1 ] ; then # BLOCK volume change from Oracle-managed Key to Customer-managed Key
  oci --profile "${REGION_PROFILE}" bv volume-kms-key update --volume-id "${BLOCK_VOLUME_OCID}" --kms-key-id "${MasterEncryptionKey_OCID}"
  echo "${PF1} BLOCK volume change from Oracle-managed Key to Customer-managed Key" >> "${LOG_FILE}"
fi

color_print "${MYcolor}" "${PF1} BLOCK volume backup change from Oracle-managed Key to Customer-managed Key (coming soon)"
if [ 1 -eq 0 ] ; then # BLOCK volume backup change from Oracle-managed Key to Customer-managed Key (coming soon)
: ' ---------------------------------------------------------------------------------------------------------------------------------------
Backup Data in Storage Services     https://docs.oracle.com/en/solutions/oci-best-practices/back-your-data1.html
-------------------------------------------------------------------------------------------------------------------------------------------'
  oci --profile "${REGION_PROFILE}" bv backup-kms-key update --volume-id "${BLOCK_VOLUME_BACKUP_OCID}" --kms-key-id "${MasterEncryptionKey_OCID}"
  
  oci --profile "${REGION_PROFILE}" bv backup update --volume-backup-id "${BLOCK_VOLUME_BACKUP_OCID}" --kms-key-id "${MasterEncryptionKey_OCID}"
  echo "${PF1} BLOCK volume backup change from Oracle-managed Key to Customer-managed Key" >> "${LOG_FILE}"
fi

color_print "${MYcolor}" "${PF1} Rotation of Customer-managed Key"
if [ 1 -eq 1 ] ; then # Rotation of Customer-managed Key

: ' ---------------------------------------------------------------------------------------------------------------------------------------
Periodically rotating keys limits the amount of data 
encrypted or signed by one key version. If a key is 
ever compromised, key rotation thus reduces the risk.   https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm#concepts
kms management key-version create                       https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/kms/management/key-version/create.html
-------------------------------------------------------------------------------------------------------------------------------------------'

  oci --profile "${REGION_PROFILE}" kms management key-version create --key-id "${MasterEncryptionKey_OCID}" --endpoint "${ManagementEndpoint}" --wait-for-state "ENABLED"
  echo "${PF1} Rotation of Customer-managed Key" >> "${LOG_FILE}"
fi

echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"
echo " " >> "${LOG_FILE}"
fi

MYOUTPUT="Secure Storage with Oracle-managed Key" && MYCOUNT=$(($MYCOUNT + 1))
if [ 1 -eq 1 ] ; then
color_print "${IGreen}" "($MYCOUNT) $(date "+%d.%m.%Y %H:%M:%S") : $MYOUTPUT"

echo "Secure Storage with Oracle-managed Key" >> "${LOG_FILE}"
echo "=====================================================================" >> "${LOG_FILE}"
echo "${PF1} $(date "+%d.%m.%Y %H:%M:%S")" >> "${LOG_FILE}"
echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"

color_print "${MYcolor}" "${PF1} BLOCK volume change from Customer-managed Key to Oracle-managed Key"
if [ 1 -eq 1 ] ; then # BLOCK volume change from Customer managed Key to Oracle managed Key
  oci --profile "${REGION_PROFILE}" bv volume-kms-key update --volume-id "${BLOCK_VOLUME_OCID}" --kms-key-id "${MasterEncryptionKey_OCID}"
  echo "${PF1} BLOCK volume change from Customer-managed Key to Oracle-managed Key" >> "${LOG_FILE}"
fi

color_print "${MYcolor}" "${PF1} BLOCK volume backup change from Customer-managed Key to Oracle-managed Key (coming soon)"
if [ 1 -eq 0 ] ; then # BLOCK volume backup change from Customer-managed Key to Oracle-managed Key (coming soon)
  #oci --profile "${REGION_PROFILE}" bv backup-kms-key update --volume-id "${BLOCK_VOLUME_BACKUP_OCID}" --kms-key-id "${MasterEncryptionKey_OCID}" 
  echo "${PF1} BLOCK volume backup change from Customer-managed Key to Oracle-managed Key" >> "${LOG_FILE}"
fi

echo "${PF1} --------------------------------------------------------------" >> "${LOG_FILE}"
echo " " >> "${LOG_FILE}"
fi


MYOUTPUT="End of Programm" && MYCOUNT=$(($MYCOUNT + 1)) 
color_print "${IGreen}" "($MYCOUNT) $(date "+%d.%m.%Y %H:%M:%S") : $MYOUTPUT"
# ---------------------------------------------------------------------------------------------------------------------------------------------
# end of file
# ---------------------------------------------------------------------------------------------------------------------------------------------
