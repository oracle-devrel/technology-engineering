#!/bin/sh

ROOTPATH=/home/opc/PPL
PLANFILE=${ROOTPATH}/$1
IDPLAN=$(jq -r '.IDPLAN' ${PLANFILE})
numrun=$(jq -r '.runs[].name' ${PLANFILE} | wc -l)
plandesc=$(jq -r '.PlanDesc' ${PLANFILE})
lastrunidx=$(echo ${numrun}"-1" | bc -l)

echo "Plan: "${IDPLAN}
echo "Plan description: "${plandesc}
echo "Number of runs in the plan is "${numrun}
echo " "
echo "Now parsing runs ..."
echo " "
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
   echo "...Run number "${i}" with name "${runname}" and label "${runlabel}
   echo "...Number of ocpu for this run: "${runocpu}
   echo "...Amount of storage (TB) for this run: "${runstorage}
   echo "...Will this run go parallel: "${runparallel}
   echo "...Number of steps into this run: "${numsteps}
   echo "...Number of paralelizable SH steps into this run: "${numstepSH}
   echo "...List of steps:"
   for j in `seq 0 ${laststepidx}`
   do
      stepname=$(jq -r '.runs['${i}'].steps['${j}'].name' ${PLANFILE})
      steptype=$(jq -r '.runs['${i}'].steps['${j}'].type' ${PLANFILE})
      echo "......Step "${stepname}" of type "${steptype}
   done
   echo " "
done

exit 0
