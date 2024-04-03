#!/bin/sh

runlabel=$1
runocpu=$2
runstorage=$3
THEDATE=$4
IDPLAN=$5
numstepSH=$6
planlogfile=$7

logtemplate=/home/opc/PPL/log/${IDPLAN}.${THEDATE}.${runlabel}.*.${runocpu}.${runstorage}

echo "Checking for completion on files "${logtemplate}."* ..." | tee -a ${planlogfile}
echo "Waiting for "${numstepSH}" steps to complete ... " | tee -a ${planlogfile}
sleep 5

while true
do
  numcompleted=$(grep "Elapsed:" ${logtemplate}.*.log | wc -l)
  if [ ${numcompleted} -eq ${numstepSH} ]
  then
     break
  else
     echo " ... waiting for "$(echo ${numstepSH}"-"${numcompleted} | bc -l)" SH steps to complete ..." | tee -a ${planlogfile} 
     sleep 15
  fi
done

echo ${numcompleted}" out of "${numstepSH}" steps completed. Resuming plan." | tee -a ${planlogfile}
exit 0
