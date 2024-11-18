#!/bin/bash
PYENV=/home/doe/py38env
OCIPROFILE=oraemeasec
BASTIONOSID="ocid1.bastion.oc1.eu-frankfurt-1.amaaaaaaupfxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SSHKEYDIR="/home/doe/.ssh/"
SSHPUBFILE="from3.pub"
SSHPRIVATEFILE="fromios3"
DISPLAYNAME="jumpv3-session"
OSUSERNAME=oracle
RESOURCEPORT=22
LOCALPORT=8222
RESOURCEIPADDRESS="10.3.4.182"
OCIREGION="eu-frankfurt-1"
TIMETOLIVE=1800
TEMPFILE=/home/doe/cloud_scripts/tempCreateSession.json
#
# Activate python env for OCI config
#
source $PYENV/bin/activate
#
# build inputfile for session creation
#
echo ' {
  "bastionId": "'${BASTIONOSID}'",
  "displayName": "'${DISPLAYNAME}'",
  "keyType": "PUB",
  "maxWaitSeconds": 0,
  "sessionTtl": "'${TIMETOLIVE}'",
  "sshPublicKeyFile": "'${SSHKEYDIR}${SSHPUBFILE}'",
  "targetPort": "'${RESOURCEPORT}'",
  "targetPrivateIp": "'${RESOURCEIPADDRESS}'",
  "waitForState": [
     "SUCCEEDED"
   ],
  "waitIntervalSeconds": 30
}' >$TEMPFILE
#
# Create the session
#
#CSTATUS=`oci bastion session create --profile $OCIPROFILE --bastion-id --from-json "file://${TEMPFILE}"`
CSTATUS=`oci bastion session create-port-forwarding --profile $OCIPROFILE --from-json "file://${TEMPFILE}"`
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
SESSID=`echo $CSTATUS | jq '.data.id' | sed 's/"//g'`
echo "Session ID: "$SESSID
if [  "$ASTATUS" != "ACTIVE" ]
then
    echo "waiting for session creation (approx 60 sec.)"
    for I in 1 2 3 4 5 6
    do
      sleep 10
      ASTATUS=`oci --profile $OCIPROFILE bastion session get --session-id $SESSID | jq '.data."lifecycle-state"' | sed 's/"//g' `
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
        echo "oci --profile $OCIPROFILE bastion session get --session-id $SESSID"
        exit 1
      fi
fi
#
#  Create the localhost tunnel
#
echo "Please make sure all ssh keys are addedd with ssh-add"
ssh-add -l
echo "creating the localhost tunnel"
echo "open new session and ssh to the local tunnel with the command"
echo 'ssh -4 -N -L '${LOCALPORT}':'${RESOURCEIPADDRESS}':'${RESOURCEPORT}' -p '${RESOURCEPORT} ${SESSID}'@host.bastion.'${OCIREGION}'.oci.oraclecloud.com'
echo "Connect from a 2. ssh session with the command"
echo 'ssh '${OSUSER}'@localhost -p '${LOCALPORT}

