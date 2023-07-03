#!/bin/sh

export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True
ocid=$1
newocpu=$2
ficlog=/tmp/$$.log
planlogfile=$3

### Gets current ocpu count !!!
/home/opc/bin/oci db autonomous-database get --autonomous-database-id ${ocid} --defaults-file /home/opc/.oci/mydefaults.txt 1>${ficlog} 2>&1

currentocpu=$(grep "cpu-core-count" ${ficlog} | awk '{ print $NF }' | sed '1,$ s/"//g' | sed '1,$ s/,//' | head -1)
echo "Current ocpu="${currentocpu}

if ! [ ${currentocpu} -eq ${newocpu} ]
then
   ### Scale ADW to newcpu !!!
   echo "Now scaling to "${newocpu}" ..." | tee -a ${planlogfile}
   /home/opc/bin/oci db autonomous-database update --autonomous-database-id ${ocid} --cpu-core-count ${newocpu} --defaults-file /home/opc/.oci/mydefaults.txt 1>${ficlog} 2>&1
## Wait until status is AVAILABLE !!!
while true
do
  /home/opc/bin/oci db autonomous-database get --autonomous-database-id ${ocid} --defaults-file /home/opc/.oci/mydefaults.txt 1>${ficlog} 2>&1
  status=$(grep "lifecycle-state" ${ficlog} | awk '{ print $NF }' | sed '1,$ s/"//g' | sed '1,$ s/,//')
  if [ ${status} == "AVAILABLE" ]
  then
     break
  else
     ### Sleep 15s before re-checking status !!!
     echo "... Waiting for status to become AVAILABLE, current status is "${status}" ..." | tee -a ${planlogfile}
     sleep 15
  fi
done
else
   echo "No need to scale ..." | tee -a ${planlogfile}
fi

exit 0
