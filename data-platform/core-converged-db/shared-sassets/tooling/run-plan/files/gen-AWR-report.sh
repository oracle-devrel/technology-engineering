#!/bin/sh

ORACLE_HOME=/home/opc/instantclient_19_6
LD_LIBRARY_PATH=/home/opc/instantclient_19_6
PATH=$ORACLE_HOME/bin:$PATH
ROOTPATH=/home/opc/PPL
DIRLOG=${ROOTPATH}/log

planlogfile=$1
IDPLAN=$2
THEDATE=$3
runlabel=$4

SNAPPREFIX=${IDPLAN}_${THEDATE}_${runlabel}
reportfile=${DIRLOG}/${SNAPPREFIX}_awr.html

beginsnap=$(grep -A2 ${SNAPPREFIX} ${planlogfile} | grep [0-9] | grep -v [A-Z] | awk '{ print $1 }' | head -1)
endsnap=$(grep -A2 ${SNAPPREFIX} ${planlogfile} | grep [0-9] | grep -v [A-Z] | awk '{ print $1 }' | tail -1)

fecha=$(date +%Y%m%d%H%M%S)
stringconnect=admin/AaZZ0r_cle#1@adwhpcdb_low
echo "Generating AWR report at "${fecha} | tee -a ${planlogfile}
sqlplus -s ${stringconnect} << EOF > ${reportfile}
set serveroutput on size 1000000
DECLARE
  db_id NUMBER;
  inst_id NUMBER;
  start_id NUMBER;
  end_id NUMBER;
 
 BEGIN
   dbms_output.enable(1000000);
   SELECT dbid INTO db_id FROM v\$pdbs;
   start_id := ${beginsnap};
   end_id := ${endsnap};
 
   FOR v_awr IN (SELECT output
              FROM   TABLE(DBMS_WORKLOAD_REPOSITORY.awr_global_report_html(db_id,'',start_id,end_id))) LOOP
 
   dbms_output.put_line(v_awr.output);
   END LOOP;
END;
/

exit

EOF

exit 0
