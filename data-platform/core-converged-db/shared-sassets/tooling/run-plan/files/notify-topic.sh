#!/bin/sh

### Script to notify a topic !!!
### Usage: notify-topic.sh ${IDPLAN} ${LOGFILE}

DATE=`date +%Y%m%d%H%M%S`
PRETTYDATE=`date +%d/%m/%Y-%Hh%Mmn%Ss`
ROOTPATH=/home/opc/PPL
DIRLOG=${ROOTPATH}/log
IDPLAN=$1
LOGFILE=$2
PLANSTARTDATE=$3
topicocid="YOUR OCI TOPIC OCID HERE"

bodyfile=${DIRLOG}/${DATE}.notify-topic.bodyfile.txt
msgtitle="Plan "${IDPLAN}"."${PLANSTARTDATE}" completed at "${PRETTYDATE}
export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True
### Generate body file !!!
echo " " > ${bodyfile}
echo "As of "${PRETTYDATE}", plan with ID "${IDPLAN}"."${PLANSTARTDATE}" completed with the following results:" >> ${bodyfile}
echo " " >> ${bodyfile}
head -2 ${LOGFILE} >> ${bodyfile}
echo " " >> ${bodyfile}
sed '1,/Plan results/d' ${LOGFILE} >> ${bodyfile}
echo " " >> ${bodyfile}
echo "Please review file "${LOGFILE}" for detailed information." >> ${bodyfile}
echo " " >> ${bodyfile}
echo "Kind regards," >> ${bodyfile}
/home/opc/bin/oci ons message publish --topic-id ${topicocid} --title "${msgtitle}" --body "$(cat ${bodyfile})" --defaults-file /home/opc/.oci/mydefaults.txt 1>>${LOGFILE} 2>&1

exit 0

