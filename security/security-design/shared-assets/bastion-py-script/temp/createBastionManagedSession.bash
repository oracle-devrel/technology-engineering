#!/bin/bash
#
# Example script that creates a managed ssh session with the bastion service
#
PYENV=/home/doe/py38env
OCIPROFILE=oraemeasec
BASTIONOSID="ocid1.bastion.oc1.eu-frankfurt-1.amaaaaaaupxxxxxxxxxxxxxxxxxxxxxxxxx"
SSHKEYDIR="/home/doe/.ssh/"
SSHPUBFILE="bastion_pub"
SSHPRIVATEFILE="bastion.pem"
DISPLAYNAME="jumpv3-session"
RESOURCEID="ocid1.instance.oc1.eu-frankfurt-1.antheljsupfargixxxxxxxxxxxxxxxxxxxxx"
OSUSERNAME=oracle
RESOURCEPORT=22
RESOURCEIPADDRESS="10.3.4.86"
OCIREGION="eu-frankfurt-1"
TIMETOLIVE=1800
TEMPFILE=/home/doe/tempCreateSession.json
#
# Activate python env for OCI config
#
source py38env/bin/activate
#
# build inputfile for session creation
#
echo '{
  "bastionId": "'${BASTIONOSID}'",
  "displayName": "'${DISPLAYNAME}'",
  "keyType": "PUB",
  "maxWaitSeconds": 0,
  "sessionTtl": "string",
  "session-ttl-in-seconds": '${TIMETOLIVE}',
  "sshPublicKeyFile": "'${SSHKEYDIR}${SSHPUBFILE}'",
   "target-resource-details": {
        "session-type": "MANAGED_SSH",
        "target-resource-id": "'${RESOURCEID}'",
        "target-resource-operating-system-user-name": "'${OSUSERNAME}'",
        "target-resource-port": '${RESOURCEPORT}',
        "target-resource-private-ip-address": "'${RESOURCEIPADDRESS}'"
      },
  "waitForState": [
    "SUCCEEDED"
  ],
  "waitIntervalSeconds": 60
}'  >$TEMPFILE
#
# Create the session
#
#CSTATUS=`oci bastion session create --profile $OCIPROFILE --bastion-id --from-json "file://${TEMPFILE}"`
CSTATUS=`oci bastion session create --profile $OCIPROFILE --from-json "file://${TEMPFILE}"`
#echo $CSTATUS | jq '.data."lifecycle-state"' |  grep 'ACCEPTED\|CANCELED\|CANCELING\|IN_PROGRESS\|SUCCEEDED\|ACTIVE\|CREATING' >/dev/null
echo $CSTATUS | jq '.data."lifecycle-state"' |  grep 'ACCEPTED\|CANCELED\|CANCELING\|IN_PROGRESS\|SUCCEEDED\|ACTIVE\|CREATING'
if [ $? -ne  0 ]
then
  echo $CSTATUS
  echo ""
  echo "Creation of session failed"
  exit 1
fi
#
# check if creation failed
#
ASTATUS=`echo $CSTATUS | jq '.data."lifecycle-state"' | sed 's/"//g'`
if [ "$ASTATUS" = "FAILED" ]
then
  echo $CSTATUS
  echo "Creation of session failed"
  exit 2
fi
#
# grab the ID of the session, and check if it is active
#
ID=`echo $CSTATUS | jq '.data.id' | sed 's/"//g'`
echo "ID: "$ID
if [  "$ASTATUS" != "ACTIVE" ]
then
    echo "waiting for session creation (approx 60 sec.)"
    for I in 1 2 3 4 5 6
    do
      sleep 10
      ASTATUS=`oci --profile $OCIPROFILE bastion session get --session-id $ID | jq '.data."lifecycle-state"' | sed 's/"//g' `
      if [ "$ASTATUS" = "ACTIVE" ]
      then
        echo "bastion service is ready"
        break
      fi
      echo "Creation status: "${ASTATUS}
    done
     if [ "$ASTATUS" != "ACTIVE" ]
      then
        echo "bastion service is not yet available "
        echo "Please verify with command: "
        echo "oci --profile $OCIPROFILE bastion session get --session-id $ID"
        exit 1
      fi
fi
#
#  Connect to the session
#
ssh -i ${SSHKEYDIR}${SSHPRIVATEFILE} -o ProxyCommand="ssh -i  ${SSHKEYDIR}${SSHPRIVATEFILE} -W %h:%p -p '${RESOURCEPORT}' ${ID}@host.bastion.${OCIREGION}.oci.oraclecloud.com" \
 -p ${RESOURCEPORT} ${OSUSERNAME}@${RESOURCEIPADDRESS}


