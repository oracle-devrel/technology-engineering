#!/bin/bash

#### Run a test plan from JSON !!!

ROOTPATH=/home/opc/PPL
DIRLOG=${ROOTPATH}/log
PLANFILE=${ROOTPATH}/$1
THEDATE=$(date +%Y%m%d%H%M%S)
ADWOCID="YOUR ADB OCID HERE"

### Get basic information of the plan !!!
##
IDPLAN=$(jq -r '.IDPLAN' ${PLANFILE})
LOGFILE=${DIRLOG}/${IDPLAN}.${THEDATE}.log
numrun=$(jq -r '.runs[].name' ${PLANFILE} | wc -l) ### This is the number of runs defined in the plan !!!
lastrunidx=$(echo ${numrun}"-1" | bc -l)
plandesc=$(jq -r '.PlanDesc' ${PLANFILE})

### Starting to run the plan !!!
echo "Now starting plan "${IDPLAN}" at "${THEDATE} | tee -a ${LOGFILE}
echo "Plan description: "${plandesc} | tee -a ${LOGFILE}
echo " " | tee -a ${LOGFILE}
echo "Number of runs is "${numrun} | tee -a ${LOGFILE}

for i in `seq 0 ${lastrunidx}`
do
   runname=$(jq -r '.runs['${i}'].name' ${PLANFILE})
   runlabel=$(jq -r '.runs['${i}'].Label' ${PLANFILE})
   runocpu=$(jq -r '.runs['${i}'].ocpu' ${PLANFILE})
   runstorage=$(jq -r '.runs['${i}'].storageTB' ${PLANFILE})
   runparallel=$(jq -r '.runs['${i}'].parallel' ${PLANFILE})
   numsteps=$(jq -r '.runs['${i}'].steps[].name' ${PLANFILE}| wc -l)
   numstepSH=$(jq -r '.runs['${i}'].steps[].type' ${PLANFILE} | grep SH | wc -l)
   laststepidx=$(echo ${numsteps}"-1" | bc -l)
   echo " " | tee -a ${LOGFILE}
   echo "Now entering run "${runname}" with "${numsteps}" steps ..."  | tee -a ${LOGFILE}
   echo "... Label: "${runlabel} | tee -a ${LOGFILE}
   echo "... OCPU: "${runocpu} | tee -a ${LOGFILE}
   echo "... Storage (TB): "${runstorage} | tee -a ${LOGFILE}
   echo "... Parallel (Y/N): "${runparallel} | tee -a ${LOGFILE}
   echo "... Number of SH steps: "${numstepSH} | tee -a ${LOGFILE}

   for j in `seq 0 ${laststepidx}`
   do
      stepname=$(jq -r '.runs['${i}'].steps['${j}'].name' ${PLANFILE})
      steptype=$(jq -r '.runs['${i}'].steps['${j}'].type' ${PLANFILE})
      stepcommand=$(jq -r '.runs['${i}'].steps['${j}'].command' ${PLANFILE})
      ##
      echo "Now running step "${stepname}" of type "${steptype}" ..." | tee -a ${LOGFILE}
      if [ ${steptype} == "SH" ]
      then
         ### Run the command with nohup if runparallel="Y", as is otherwise !!!
         if [ ${runparallel} == "Y" ]
         then
              nohup ${stepcommand} ${runlabel} ${stepname} ${runocpu} ${runstorage} ${THEDATE} ${IDPLAN} &
         else
              ${stepcommand} ${runlabel} ${stepname} ${runocpu} ${runstorage} ${THEDATE} ${IDPLAN}
         fi
      elif [ ${steptype} == "AWR" ]
      then
              ${stepcommand} ${LOGFILE} ${runlabel} ${THEDATE} ${IDPLAN}
      elif [ ${steptype} == "SCALE" ]
      then
         ${stepcommand} ${ADWOCID} ${runocpu} ${LOGFILE}
      elif [ ${steptype} == "WAIT" ]
      then
            ${stepcommand} ${runlabel} ${runocpu} ${runstorage} ${THEDATE} ${IDPLAN} ${numstepSH} ${LOGFILE}
      elif [ ${steptype} == "AWRREPORT" ]
      then
            ${stepcommand} ${LOGFILE} ${IDPLAN} ${THEDATE} ${runlabel}
      fi
   done
done

### Spool the results into plan logfile !!!
echo "Plan results ****************" | tee -a ${LOGFILE}
for fic in `ls -1tr /home/opc/PPL/log/${IDPLAN}.${THEDATE}.*.*.*.*.*.log`
do
   echo $fic":"$(grep "Elapsed:" $fic)
done | tee -a ${LOGFILE}

echo "Now scaling down to 4 ocpu." | tee -a ${LOGFILE}
${ROOTPATH}/scale-ADW.sh ${ADWOCID} 4 ${LOGFILE}
echo "Plan "${IDPLAN}" completed." | tee -a ${LOGFILE}
### 
### Notify by topic email !!!
###
${ROOTPATH}/notify-topic.sh ${IDPLAN} ${LOGFILE} ${THEDATE}
###
exit 0
