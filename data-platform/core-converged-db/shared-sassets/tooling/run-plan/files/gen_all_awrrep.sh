#!/bin/sh

logfile=$1
logdir=/home/opc/PPL/log

PLANID=$(echo ${logfile} | cut -f1 -d".")
THEDATE=$(echo ${logfile} | cut -f2 -d".")
AWRLOGFILE=${logdir}/AWR.${PLANID}.${THEDATE}.log

for linea in $(grep -A2 SNAPID ${logdir}/${logfile} | grep [0-9] | grep -v [A-Z] | awk '{printf "%s%s",$0,NR%2?";":"\n" ; }' | sed '1,$ s/ //g' | awk '{ print "RUN"NR";"$0 }')
do
   idrun=$(echo $linea | cut -f1 -d";")
   beginsnap=$(echo $linea | cut -f2 -d";")
   endsnap=$(echo $linea | cut -f3 -d";")
   /home/opc/PPL/gen-AWR-report2.sh ${AWRLOGFILE} ${PLANID} ${THEDATE} ${idrun} ${beginsnap} ${endsnap}
done
