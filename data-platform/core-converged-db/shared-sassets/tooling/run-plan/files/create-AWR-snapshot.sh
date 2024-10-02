#!/bin/sh

ORACLE_HOME=/home/opc/instantclient_19_6
LD_LIBRARY_PATH=/home/opc/instantclient_19_6
PATH=$ORACLE_HOME/bin:$PATH
planlogfile=$1
runlabel=$2
THEDATE=$3
IDPLAN=$4

SNAPPREFIX=${IDPLAN}_${THEDATE}_${runlabel}

fecha=$(date +%Y%m%d%H%M%S)
stringconnect=admin/AaZZ0r_cle#1@adwhpcdb_low
echo "Creating AWR snapshot at "${fecha} | tee -a ${planlogfile}
sqlplus -s ${stringconnect} << EOF | tee -a ${planlogfile}
select  dbms_workload_repository.create_snapshot() as "${SNAPPREFIX}_SNAPID" from dual;
exit

EOF

exit 0
