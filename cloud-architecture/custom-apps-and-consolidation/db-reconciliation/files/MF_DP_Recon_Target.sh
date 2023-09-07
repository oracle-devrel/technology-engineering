#!/bin/bash
# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: Script to capture Target Object count,table row count and invalid objects and generate reconcile report.
# The purpose of this script is to verify the migrated data against the original source.
# @author: Ananda Ghosh Dastidar.

if [ "$#" -lt 2 ]; then
   echo Usage: $0 "<username>/<passowrd>@service_name" "spool_dir"
   exit 1
fi

clear screen
conn_string=`echo "$1"`
spool_dir=`echo "$2"`
Recon_conn_string="'${conn_string}'";
target_db_user="SYS"
gv_dp_version="3.0"
timestamp=$(date +%d-%m-%Y_%H-%M-%S)


if [ -z "$target_db_user" ] || [ "$target_db_user" == "SYSTEM" ] || [ "$target_db_user" == "system" ] ; then
    echo connect string $conn_string not valid. sys or system user not allowed. 
    exit 1
fi

#Default schema to be ignored for the reconciliation report
blacklisted_schema="('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA\$ORB\$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS\$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS\$ORACLE')"

echo
echo "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO"
echo "O                                                 ORACLE CLOUD LIFT SERVICES                                                O"
echo "O                                         RECONCILIATION REPORT - TARGET STEPS ${gv_dp_version}                                          O"
echo "O                                                 ( Oracle 11g onwards )                                                    O"
echo "O                                                    ${timestamp}                                                    O"
echo "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO"
echo
sqlplus -s "${conn_string}" << EOF
set feed off
set echo off;
set verify off;
SET linesize 32767;
SET LONG 999999;
SET SHOW OFF;
SET TRIMS ON;
SET TERM OFF;
select i.INSTANCE_NAME,i.HOST_NAME,i.VERSION,to_char(i.STARTUP_TIME,'YYYY/MM/DD HH:MI:SS') open_TIME 
from sys.v_\$INSTANCE i;
PROMPT
EOF

read -p "Please press Enter to continue : " v_run_option 
echo $'\n'

echo Start Date/Time : $timestamp  |tee ${spool_dir}/Target_Steps_Execution.log
echo Usage: $0 "$conn_string" "${spool_dir}" |tee -a ${spool_dir}/Target_Steps_Execution.log

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET TERM OFF;
DECLARE
c INT;
BEGIN
	SELECT COUNT(1) INTO c FROM dba_tables WHERE table_name = 'USER_TEMP' AND owner =upper('${target_db_user}');
	IF c = 1 THEN
		EXECUTE immediate 'DROP TABLE ${target_db_user}.USER_TEMP PURGE';
	END IF;
	EXECUTE immediate 'CREATE TABLE ${target_db_user}.USER_TEMP (SCHEMA_LIST VARCHAR2(100))';
END;
/
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while creating USER_TEMP in ${target_db_user}.USER_TEMP"  |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi
sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET TERM OFF;
BEGIN
	insert into USER_TEMP select username from dba_users where username not in ${blacklisted_schema};
    commit;
END;
/
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading data in ${target_db_user}.USER_TEMP"  |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


cat << EOF >  $spool_dir/source_data.ctl
LOAD DATA
INFILE '${spool_dir}/source_data.csv'
BADFILE '${spool_dir}/source_data.BAD'
DISCARDFILE '${spool_dir}/source_data.DIS'
APPEND INTO TABLE ${target_db_user}.RECON_TABLE
FIELDS TERMINATED BY "," 
(runid,recon_type,owner,object_name,object_type,subobject_name,index_type,index_name,tablespace_name,partition_name,subpartition_name,constraint_type,constraint_name,table_name,column_name,r_owner,r_constraint_name,grantee,priv_type,grantor,privilege,grantable,hierarchy,admin_option,granted_role,default_role,status,counts 
)
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while creating RECON_TABLE control file." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

#Added the section to recompile using utlprp
echo "Info - Step MF_DP_Recon_Target is in-progress for recompiling using utlprp" |tee -a ${spool_dir}/Target_Steps_Execution.log
sqlplus -s "${conn_string}" << EOF
@?/rdbms/admin/utlprp 8
EOF
if [ $? != 0 ]; then
   echo "Failure - Step OMF_Recon_Target Failed while recompiling using utlprp" |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET linesize 300;
SET feedback OFF;
SET heading OFF;
SET echo OFF;
SET pages 0;
col COUNT FOR 99
set serveroutput on
DECLARE
  c INT;
BEGIN
  SELECT COUNT(1)
  INTO c
  FROM dba_tables
  WHERE table_name = 'RECON_TABLE'
  AND owner        =upper('${target_db_user}');
  IF c             = 1 THEN
    EXECUTE immediate 'drop table ${target_db_user}.RECON_TABLE purge';
  END IF;
  EXECUTE immediate 'create table ${target_db_user}.RECON_TABLE (
runid number(1),
recon_type varchar2(30),
owner varchar2(30),
object_name varchar2(200),
object_type varchar2(200),
subobject_name varchar2(200),
index_type varchar2(200),
index_name varchar2(200),
tablespace_name varchar2(200),
partition_name varchar2(200),
subpartition_name varchar2(200),
constraint_type varchar2(1),
constraint_name varchar2(200),
table_name varchar2(200),
column_name varchar2(4000),
r_owner varchar2(30),
r_constraint_name varchar2(200),
grantee varchar2(30),
priv_type varchar2(10),
grantor varchar2(30),
privilege varchar2(40),
grantable varchar2(3),
hierarchy varchar2(3),
admin_option varchar2(3),
granted_role varchar2(30),
default_role varchar2(3),
status varchar2(10),
counts number(10)
)';
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while creating RECON_TABLE in ${target_db_user}.RECON_TABLE" |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlldr userid=${Recon_conn_string} control=$spool_dir/source_data.ctl log=$spool_dir/source_data_sqlldr.log

if [ $? = 1 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading source data csv file using sqlloader." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectCount
  IS
    select '2' runid,'OBJ_COUNTS' recon_type,owner,object_type,count(1) counts from dba_objects
    where object_type = 'TABLE'
    and owner in (SELECT SCHEMA_LIST FROM USER_TEMP) 
    and object_name in (select table_name from dba_tables where owner in (SELECT SCHEMA_LIST FROM USER_TEMP) and (IOT_TYPE is null or IOT_TYPE='IOT')) 
    and object_name not in (select table_name FROM dba_external_tables WHERE OWNER IN (SELECT SCHEMA_LIST FROM USER_TEMP) )
    group by owner,object_type
    union
    select '2' runid,'OBJ_COUNTS' recon_type,owner,'INDEX',count(1) counts from dba_indexes
    where owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
    group by owner
    union
    select '2' runid,'OBJ_COUNTS' recon_type,owner,object_type,count(1) counts from dba_objects
    where object_type not in ('TABLE','INDEX')
    and owner in (SELECT SCHEMA_LIST FROM USER_TEMP) 
    group by owner,object_type
    order by 1;

BEGIN
  FOR i IN MyObjectCount
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        object_type,
        counts
      )
      VALUES
      (
        i.runid,
        i.recon_type,
        i.owner,
        i.object_type,
        i.counts
      );
  END LOOP;
  COMMIT;
END;
/
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading object counts into ${target_db_user}.RECON_TABLE" |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
set serverout on
DECLARE
  val NUMBER;
  Mowner varchar2(128);
  Mtable varchar2(128);
BEGIN
  FOR I IN
  (SELECT OWNER,TABLE_NAME FROM DBA_TABLES WHERE OWNER IN (SELECT SCHEMA_LIST FROM USER_TEMP) AND (IOT_TYPE='IOT' OR IOT_TYPE is NULL)
  and TABLE_NAME NOT IN (SELECT table_name FROM dba_external_tables WHERE OWNER IN (SELECT SCHEMA_LIST FROM USER_TEMP) )
  ORDER BY owner,table_name
  )
  LOOP
    Mowner:=i.owner;
    Mtable:=i.table_name;
    EXECUTE IMMEDIATE 'SELECT count(1) FROM "' || i.owner||'"."'||i.table_name||'"' INTO val;
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        table_name,
        counts
      )
      VALUES
      (
        '2',
        'TABLE_COUNTS',
        i.owner,
        i.table_name,
        val
      );
  END LOOP;
  COMMIT;
EXCEPTION
 WHEN OTHERS THEN
 DBMS_OUTPUT.PUT_LINE ('Error while taking count of below table.');
 DBMS_OUTPUT.PUT_LINE (SQLERRM);
 DBMS_OUTPUT.PUT_LINE (SQLCODE);
 DBMS_OUTPUT.PUT_LINE (Mowner||'.'||Mtable);
END;
/
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading table counts into ${target_db_user}.RECON_TABLE" |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    SELECT owner,
      object_name,
      subobject_name,
      object_type,
      status,
      COUNT(1) COUNT
    FROM dba_objects
    WHERE owner IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    AND (object_name NOT LIKE 'SYS_%' AND object_name NOT LIKE 'BIN$%')
    group by owner,object_name,object_type,subobject_name,status;

BEGIN
  FOR i IN MyObjectInvalids
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        object_name,
        subobject_name,
        object_type,
        status,
        counts
      )
      VALUES
      (
        '2',
        'OBJECT_NAME',
        i.owner,
        i.object_name,
        i.subobject_name,
        i.object_type,
        i.status,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target object names into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    SELECT owner,
      object_name,
      subobject_name,
      object_type,
      status,
      COUNT(1) COUNT
    FROM dba_objects
    WHERE status <> 'VALID'
    AND owner    IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    GROUP BY owner,
      object_name,
      subobject_name,
      object_type,
      status;
BEGIN
  FOR i IN MyObjectInvalids
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        object_name,
        subobject_name,
        object_type,
        status,
        counts
      )
      VALUES
      (
        '2',
        'OBJ_INVALIDS',
        i.owner,
        i.object_name,
        i.subobject_name,
        i.object_type,
        i.status,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target invalid objects into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR Myuserdetails
  IS
    SELECT username,Account_status,COUNT(1) COUNT
    from dba_users 
    where username in (SELECT SCHEMA_LIST FROM USER_TEMP)
    group by username,Account_status
    order by username,Account_status;
BEGIN
  FOR i IN Myuserdetails
  LOOP
    INSERT
    INTO RECON_TABLE(runid,recon_type,owner,object_name,counts)
    VALUES
      (
        '2',
        'USER_DETAILS',
        i.username,
        i.Account_status,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target user account status into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    (SELECT 'UNUSABLE_INDEX_TABLE' INDEX_TYPE,
      owner,
      index_name,
      tablespace_name,
      STATUS ,
      'ZZ' PARTITION_NAME,
      'ZZ' SUBPARTITION_NAME
    FROM dba_indexes
    WHERE status = 'UNUSABLE'
    AND owner   IN (SELECT SCHEMA_LIST FROM USER_TEMP)
  UNION ALL
  SELECT 'UNUSABLE_INDEX_PARTITION' INDEX_TYPE,
    index_owner,
    index_name,
    tablespace_name,
    STATUS,
    PARTITION_NAME,
    'ZZ' SUBPARTITION_NAME
  FROM dba_ind_PARTITIONS
  WHERE status     = 'UNUSABLE'
  AND index_owner IN (SELECT SCHEMA_LIST FROM USER_TEMP)
  UNION ALL
  SELECT 'UNUSABLE_INDEX_SUB_PARTITION' INDEX_TYPE,
    index_owner,
    index_name,
    tablespace_name,
    STATUS,
    partition_name,
    subpartition_name
  FROM dba_ind_SUBPARTITIONS
  WHERE status     ='UNUSABLE'
  AND index_owner IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    ) ORDER BY 1;
  BEGIN
    FOR i IN MyObjectInvalids
    LOOP
      INSERT
      INTO ${target_db_user}.RECON_TABLE
        (
          runid,
          recon_type,
          owner,
          index_name,
          tablespace_name,
          status,
          partition_name,
          subpartition_name,
          counts
        )
        VALUES
        (
          '2',
          i.index_type,
          i.owner,
          i.index_name,
          i.tablespace_name,
          i.status,
          i.partition_name,
          i.subpartition_name,
          1
        );
    END LOOP;
    COMMIT;
  END;
  /
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target unusable indexes into ${target_db_user}.RECON_UNUSABLE_INDEX_${system_name} " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectCount
  IS
    SELECT owner,
      constraint_type,
      COUNT(1) COUNT
    FROM dba_constraints
    WHERE owner IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    GROUP BY owner,
      constraint_type;
BEGIN
  FOR i IN MyObjectCount
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        constraint_type,
        counts
      )
      VALUES
      (
        '2',
        'CONSTRAINT_TYPE_COUNTS',
        i.owner,
        i.constraint_type,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target constraints counts into ${target_db_user}.RECON_CONSTRAINTS_COUNT_${system_name} " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectCount
  IS
    SELECT cn.OWNER,
      cn.constraint_name,
      cn.table_name,
      cc.column_name,
      cn.r_owner,
      cn.r_constraint_name,
      COUNT(1) COUNT
    FROM dba_constraints cn,
      dba_cons_columns cc
    WHERE cn.CONSTRAINT_TYPE='R'
    AND cn.STATUS           =  'DISABLED'
    AND cn.owner           IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    AND cn.owner            =cc.owner
    AND cn.constraint_name  =cc.constraint_name
    AND cn.table_name       =cc.table_name
    GROUP BY cn.OWNER,
      cn.constraint_name,
      cn.table_name,
      cc.column_name,
      cn.r_owner,
      cn.r_constraint_name;
BEGIN
  FOR i IN MyObjectCount
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        constraint_name,
        table_name,
        column_name,
        r_owner,
        r_constraint_name,
        counts
      )
      VALUES
      (
        '2',
        'R_CONSTRAINTS_DISABLED',
        i.owner,
        i.constraint_name,
        i.table_name,
        i.column_name,
        i.r_owner,
        i.r_constraint_name,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectCount
  IS
    SELECT grantee,
      'ROLE_PRIVS' priv,
      COUNT(1) COUNT
    FROM dba_role_privs
    WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    GROUP BY grantee
  UNION
  SELECT grantee,
    'SYS_PRIVS' priv,
    COUNT(1) COUNT
  FROM dba_sys_privs
  WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
  GROUP BY grantee
  UNION
  SELECT grantee,
    'TAB_PRIVS' priv,
    COUNT(1) COUNT
  FROM dba_tab_privs
  WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
  GROUP BY grantee
  ORDER BY 1;
BEGIN
  FOR i IN MyObjectCount
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        grantee,
        priv_type,
        counts
      )
      VALUES
      (
        '2',
        'ROLE_SYS_TAB_PRIVS_COUNTS',
        i.grantee,
        i.priv,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target grantee privs counts into ${target_db_user}.RECON_PRIVS_COUNT_${system_name} " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    SELECT grantee,
      granted_role,
      admin_option,
      default_role,
      COUNT(1) COUNT
    FROM dba_role_privs
    WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    group by grantee,granted_role,admin_option,default_role;

BEGIN
  FOR i IN MyObjectInvalids
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        grantee,
        granted_role,
        admin_option,
        default_role,
        counts
      )
      VALUES
      (
        '2',
        'ROLE_PRIVS_MISSING',
        i.grantee,
        i.granted_role,
        i.admin_option,
        i.default_role,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target Role Privs into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    SELECT grantee,
      privilege,
      admin_option,      
      COUNT(1) COUNT
    FROM dba_sys_privs
    WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    group by grantee,privilege,admin_option;

BEGIN
  FOR i IN MyObjectInvalids
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        grantee,
        privilege,
        admin_option,        
        counts
      )
      VALUES
      (
        '2',
        'SYS_PRIVS_MISSING',
        i.grantee,
        i.privilege,
        i.admin_option,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target Sys Privs into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
DECLARE
  CURSOR MyObjectInvalids
  IS
    SELECT owner,
           table_name,
           grantee,
           grantor,
           privilege,
           grantable,
           hierarchy,      
           COUNT(1) COUNT
    FROM dba_tab_privs
    WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
    group by owner,table_name,grantee,grantor,privilege,grantable,hierarchy;

BEGIN
  FOR i IN MyObjectInvalids
  LOOP
    INSERT
    INTO ${target_db_user}.RECON_TABLE
      (
        runid,
        recon_type,
        owner,
        table_name,
        grantee,
        grantor,
        privilege,
        grantable,
        hierarchy,       
        counts
      )
      VALUES
      (
        '2',
        'TAB_PRIVS_MISSING',
        i.owner,
        i.table_name,
        i.grantee,
        i.grantor,
        i.privilege,
        i.grantable,
        i.hierarchy,
        i.count
      );
  END LOOP;
  COMMIT;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while loading target Tab Privs into ${target_db_user}.RECON_TABLE " |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


####################################################################################################################################################################
sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0
col owner FOR a30 
col object_type FOR a25
col comments for a60
SET lines 150
BREAK ON owner SKIP 1 ON REPORT
compute SUM OF src_cnt ON owner
compute SUM OF src_cnt ON report
compute SUM OF trg_cnt ON owner
compute SUM OF trg_cnt ON report
spool ${spool_dir}/Reconciliation_Object_Count_Report.log
TTITLE CENTER "SCHEMAWISE OBJECTS COUNT RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.object_type,trgt.object_type) object_type,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN (NVL(src.counts,0) > NVL(trgt.counts,0))
       THEN '*-*-*-* '||(NVL(src.counts,0) - NVL(trgt.counts,0))||' '||src.object_type||' missing in target db.'
    WHEN (NVL(src.counts,0) < NVL(trgt.counts,0))
       THEN '*-*-*-* '||(NVL(trgt.counts,0) - NVL(src.counts,0))||' '||trgt.object_type||' increased in target db.'
  END comments
FROM
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='OBJ_COUNTS'
  and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
  ) src
FULL OUTER JOIN
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='OBJ_COUNTS'
  and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
  ) trgt
ON (src.owner       = trgt.owner
AND src.object_type = trgt.object_type
)
ORDER BY 1,2;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating objects count reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 72 NEWPAGE 0 LINESIZE 100 
col owner FOR a30 
col table_name FOR a30
col comments for a60
SET lines 150
BREAK ON owner SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Table_Counts_Report.log
TTITLE CENTER "SCHEMAWISE TABLES COUNT RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.table_name,trgt.table_name) table_name,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  CASE
    WHEN (NVL(src.counts,-1) < 0)
       THEN '*-*-*-* Table Mising in Source.'
    WHEN (NVL(trgt.counts,-1) < 0)
       THEN '*-*-*-* Table Missing in Target.'
    WHEN (NVL(src.counts,0) <> NVL(trgt.counts,0))
       THEN '*-*-*-* Row Counts Mismatch.'
  END comments
FROM
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='TABLE_COUNTS'
  and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
  ) src
FULL OUTER JOIN
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='TABLE_COUNTS'
  and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
  ) trgt
ON (src.owner      = trgt.owner
AND src.table_name = trgt.table_name
)
ORDER BY 1,2;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating table rows count reconciliation report."
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100
col owner FOR a30
col object_name FOR a45
col subobject_name FOR a25
col object_type FOR a23
col src_status FOR a7
col trg_status FOR a7
col comments FOR a70
SET lines 400
BREAK ON owner SKIP 1 ON REPORT
compute SUM OF src_cnt ON owner
compute SUM OF src_cnt ON report
compute SUM OF trg_cnt ON owner
compute SUM OF trg_cnt ON report
spool ${spool_dir}/Reconciliation_Objects_Missing_Report.log
TTITLE CENTER "SCHEMAWISE OBJECTS MISSING/INCREASED RECONCILIATION REPORT" SKIP 3 CENTER
SELECT nvl(src.owner,trgt.owner) owner,
  nvl(src.object_name,trgt.object_name) object_name,
  nvl(src.object_type,trgt.object_type) object_type,
  nvl(src.subobject_name,trgt.subobject_name) subobject_name,  
  src.status src_status,
  trgt.status trg_status,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  CASE
    WHEN (NVL(src.counts,-1) = -1 )
        THEN '*-*-*-* Action Required object increased in Target'
    WHEN (NVL(trgt.counts,-1) = -1 )
        THEN '*-*-*-* Action Required object Missing in Target'
    WHEN (NVL(src.counts,-1) = NVL(trgt.counts,-1) AND src.status <> trgt.status)
        THEN '*-*-*-* Action Required Check object status changed in Target'
    END comments
FROM
  (SELECT runid,
    owner,
    object_name,
    object_type,
    subobject_name,
    status,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='OBJECT_NAME'
  AND (object_name NOT LIKE 'SYS_%' AND object_name NOT LIKE 'BIN$%')
  ) src
FULL OUTER JOIN
  (SELECT runid,
    owner,
    object_name,
    object_type,
    subobject_name,
    status,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='OBJECT_NAME'
  AND (object_name NOT LIKE 'SYS_%' AND object_name NOT LIKE 'BIN$%' )
  ) trgt
ON (src.owner       = trgt.owner
AND src.object_name = trgt.object_name
AND nvl(src.subobject_name,'ZZ') = nvl(trgt.subobject_name,'ZZ')
AND src.object_type = trgt.object_type
)
where (NVL(src.counts,0) + NVL(trgt.counts,0)) < 2 OR (src.status <> trgt.status and src.status is not null and trgt.status is not null)
ORDER BY 1,2,3,4;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating missing object reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100 
col owner FOR a30
col object_name FOR a45
col subobject_name FOR a25
col object_type FOR a23
col status FOR a7
col comments FOR a80
SET lines 300
BREAK ON owner SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Objects_Invalids_Report.log
TTITLE CENTER "SCHEMAWISE OBJECTS INVALIDS RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.object_name,trgt.object_name) object_name,
  NVL(src.object_type,trgt.object_type) object_type,
  src.status status,
  trgt.status status,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN NVL(src.counts,-1) < 0
       THEN '*-*-*-* Action Required object become INVALID in Target OR Increased in target'
    WHEN NVL(trgt.counts,-1)< 0 
       THEN 'Action Required Check object become VALID in Target OR Missing in Target'
  END comments
FROM
  (SELECT runid,
    owner,
    object_name,
    object_type,
    status,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='OBJ_INVALIDS'
  ) src
FULL OUTER JOIN
  (SELECT runid,
    owner,
    object_name,
    object_type,
    status,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='OBJ_INVALIDS'
  ) trgt
ON (src.owner       = trgt.owner
AND src.object_name = trgt.object_name
AND src.object_type = trgt.object_type)
ORDER BY 1,2,3,4;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating invalid objects reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100 
col owner FOR a30
col Account_status FOR a40
col status FOR a7
col comments FOR a85
SET lines 200
BREAK ON owner SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_User_Accounts_Status_Report.log
TTITLE CENTER "USERWISE ACCOUNTS STATUS RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.object_name,trgt.object_name) Account_status,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN NVL(src.counts,-1) < 0
       THEN '*-*-*-* Action Required as Account status changed in Target OR Increased in target'
    WHEN NVL(trgt.counts,-1)< 0 
       THEN 'Action Required Check Account status changed in Target OR Missing in Target'
  END comments
FROM
  (SELECT runid,
    owner,
    object_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='USER_DETAILS'
  ) src
FULL OUTER JOIN
  (SELECT runid,
    owner,
    object_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='USER_DETAILS'
  ) trgt
ON (src.owner       = trgt.owner
AND src.object_name = trgt.object_name)
ORDER BY 1,2;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating Userwise Account status reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100
col index_type FOR a13
col owner FOR a15
col index_name FOR a25
col tablespace_name FOR a25
col status FOR a10
col partition_name FOR a23
col subpartition_name FOR a25
col comments FOR a80
SET lines 200
BREAK ON index_type ON owner SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Unusable_Indexes_Report.log
TTITLE CENTER "SCHEMAWISE UNUSABLE INDEXES RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.index_type,trgt.index_type) index_type,
  NVL(src.owner,trgt.owner) owner,
  NVL(src.index_name,trgt.index_name) index_name,
  NVL(src.tablespace_name,trgt.tablespace_name) tablespace_name,
  NVL(src.status,trgt.status) status,
  NVL(DECODE(src.partition_name,'ZZ',' ',src.partition_name),DECODE(trgt.partition_name,'ZZ','  ',trgt.partition_name)) partition_name,
  NVL(DECODE(src.subpartition_name,'ZZ',' ',src.subpartition_name),DECODE(trgt.subpartition_name,'ZZ','  ',trgt.subpartition_name)) subpartition_name,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  CASE
    WHEN (NVL(trgt.counts,-1) < 0 )
       THEN '*-*-*-* Action Required Unusable Index become Usable/Missing in Target'
    WHEN (NVL(src.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Valid Index become Unusable/Increased in Target'
    END comments
FROM
  (SELECT runid,
    index_type,
    owner,
    index_name,
    tablespace_name,
    status,
    partition_name,
    subpartition_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and RECON_TYPE in ('UNUSABLE_INDEX_TABLE','UNUSABLE_INDEX_PARTITION','UNUSABLE_INDEX_SUB_PARTITION')
  ) src
FULL OUTER JOIN
  (SELECT runid,
    index_type,
    owner,
    index_name,
    tablespace_name,
    status,
    partition_name,
    subpartition_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and RECON_TYPE in ('UNUSABLE_INDEX_TABLE','UNUSABLE_INDEX_PARTITION','UNUSABLE_INDEX_SUB_PARTITION')
  ) trgt
ON ( src.index_type       = trgt.index_type
AND src.owner             = trgt.owner
AND src.index_name        = trgt.index_name
AND src.tablespace_name   = trgt.tablespace_name
AND src.status            = trgt.status
AND src.partition_name    = trgt.partition_name
AND src.subpartition_name = trgt.subpartition_name )
ORDER BY 1,2,3,4,5,6,7;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating Unusable Indexes reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100
col owner FOR a30
col constraint_type FOR a25
SET lines 100
BREAK ON owner SKIP 1 ON REPORT
compute SUM OF src_cnt ON owner
compute SUM OF src_cnt ON report
compute SUM OF trg_cnt ON owner
compute SUM OF trg_cnt ON report
spool ${spool_dir}/Reconciliation_Constraints_Count_Report.log
TTITLE CENTER "SCHEMAWISE CONSTRAINTS COUNT RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.constraint_type,trgt.constraint_type) constraint_type,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN (NVL(src.counts,0) <> NVL(trgt.counts,0))
    THEN '*-*-*-*'
  END comments
FROM
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type = 'CONSTRAINT_TYPE_COUNTS'
  ) src
FULL OUTER JOIN
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type = 'CONSTRAINT_TYPE_COUNTS'
  ) trgt
ON (src.owner           = trgt.owner
AND src.constraint_type = trgt.constraint_type)
ORDER BY 1,2;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating constraints count reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100
col owner FOR a15
col r_owner FOR a15
col constraint_name FOR a25
col r_constraint_name FOR a25
col table_name FOR a25
col column_name FOR a25
col comments FOR a60
SET lines 200
BREAK ON owner SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Ref_Constraints_Disabled_Report.log
TTITLE CENTER "SCHEMAWISE DISABLED REF CONSTRAINTS RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.owner,trgt.owner) owner,
  NVL(src.r_owner,trgt.r_owner) r_owner,
  NVL(src.constraint_name,trgt.constraint_name) constraint_name,
  NVL(src.r_constraint_name,trgt.r_constraint_name) r_constraint_name,
  NVL(src.table_name,trgt.table_name) table_name,
  NVL(src.column_name,trgt.column_name) column_name,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN (NVL(src.counts,-1)   < 0 )
       THEN '*-*-*-* Action Required Constraint become Enabled/Increased in Target'
    WHEN (NVL(trgt.counts,-1)  < 0 )
       THEN '*-*-*-* Action Required Constraint become Enabled/Missing in Target'
   END comments
FROM
  (SELECT runid,
    owner,
    constraint_name,
    table_name,
    column_name,
    r_owner,
    r_constraint_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='R_CONSTRAINTS_DISABLED'
  ) src
FULL OUTER JOIN
  (SELECT runid,
    owner,
    constraint_name,
    table_name,
    column_name,
    r_owner,
    r_constraint_name,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='R_CONSTRAINTS_DISABLED'
  ) trgt
ON (src.owner             = trgt.owner
AND src.r_owner           = trgt.r_owner
AND src.constraint_name   = trgt.constraint_name
AND src.r_constraint_name = trgt.r_constraint_name
AND src.table_name        = trgt.table_name
AND src.column_name       = trgt.column_name )
ORDER BY 1,2,3,4,5,6,7;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating Disbaled Ref Constraints reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET pagesize 999 NEWPAGE 0 LINESIZE 100
col grantee FOR a23
col priv_type FOR a25
col comments FOR a65
SET lines 200
BREAK ON grantee SKIP 1 ON REPORT
compute SUM OF src_cnt ON grantee
compute SUM OF src_cnt ON report
compute SUM OF trg_cnt ON grantee
compute SUM OF trg_cnt ON report
spool ${spool_dir}/Reconciliation_Grantee_Privs_Report.log
TTITLE CENTER "SCHEMAWISE PRIVS COUNT RECONCILIATION REPORT" SKIP 3 CENTER
SELECT NVL(src.grantee,trgt.grantee) grantee,
  NVL(src.priv_type,trgt.priv_type) priv_type,
  NVL(src.counts,0) src_cnt,
  NVL(trgt.counts,0) trg_cnt,
  CASE
    WHEN (NVL(src.counts,0) <> NVL(trgt.counts,0))
    THEN '*-*-*-*'
  END comments
FROM
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type in ('ROLE_SYS_TAB_PRIVS_COUNTS','ROLE_SYS_TAB_PRIVS_COUNTS','ROLE_SYS_TAB_PRIVS_COUNTS')
  ) src
FULL OUTER JOIN
  (SELECT *
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type in ('ROLE_SYS_TAB_PRIVS_COUNTS','ROLE_SYS_TAB_PRIVS_COUNTS','ROLE_SYS_TAB_PRIVS_COUNTS')
  ) trgt
ON (src.grantee   = trgt.grantee
AND src.priv_type = trgt.priv_type)
ORDER BY 1,2;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating Privs count reconciliation report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET linesize 300 pagesize 1000
col grantee format a30
col granted_role format a30
col admin_option format a13
col default_role format a13
BREAK ON grantee SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Missing_Roles_Report.log
TTITLE CENTER "SCHEMAWISE MISSING ROLE_PRIVS RECONCILIATION REPORT" SKIP 3 CENTER
SELECT nvl(src.grantee,trgt.grantee) grantee,
  nvl(src.granted_role,trgt.granted_role) granted_role,
  nvl(src.admin_option,trgt.admin_option) admin_option,
  nvl(src.default_role,trgt.default_role) default_role,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  CASE
    WHEN (NVL(trgt.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Role Privilege missing in Target'
    WHEN (NVL(src.counts,0) = NVL(trgt.counts,0) AND src.admin_option <> trgt.admin_option)
        THEN '*-*-*-* Action Required Check admin_option changed in Target'
    WHEN (NVL(src.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Role Privilege Increased in Target'
    END comments
FROM
  (SELECT runid,
    grantee,
    granted_role,
    admin_option,
    default_role,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='ROLE_PRIVS_MISSING'
  ) src
FULL OUTER JOIN
  (SELECT runid,
    grantee,
    granted_role,
    admin_option,
    default_role,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='ROLE_PRIVS_MISSING'
  ) trgt
ON (src.grantee       = trgt.grantee
AND src.granted_role = trgt.granted_role
AND src.default_role = trgt.default_role
)
where (NVL(src.counts,0) + NVL(trgt.counts,0)) < 2 OR (src.admin_option <> trgt.admin_option)
ORDER BY 1,2,3,4;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating missing role privileges report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi


sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET linesize 200 pagesize 1000
col grantee format a30
col privilege format a40
col admin_option format a13
BREAK ON grantee SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Missing_Sys_Privs_Report.log
TTITLE CENTER "SCHEMAWISE MISSING SYS_PRIVS NAME RECONCILIATION REPORT" SKIP 3 CENTER
SELECT nvl(src.grantee,trgt.grantee) grantee,
  nvl(src.privilege,trgt.privilege) privilege,
  nvl(src.admin_option,trgt.admin_option) admin_option,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  CASE
    WHEN (NVL(trgt.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Sys Privs is missing in Target'
    WHEN (NVL(src.counts,0) = NVL(trgt.counts,0) AND src.admin_option <> trgt.admin_option)
        THEN '*-*-*-* Action Required Check admin_option changed in Target'
    WHEN (NVL(src.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Sys Privs is Increased in Target'
    END comments
FROM
  (SELECT runid,
    grantee,
    privilege,
    admin_option,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='SYS_PRIVS_MISSING'
  ) src
FULL OUTER JOIN
  (SELECT runid,
    grantee,
    privilege,
    admin_option,
    counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='SYS_PRIVS_MISSING'
  ) trgt
ON (src.grantee       = trgt.grantee
AND src.privilege = trgt.privilege
)
where (NVL(src.counts,0) + NVL(trgt.counts,0)) < 2 OR (src.admin_option <> trgt.admin_option)
ORDER BY 1,2,3,4;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating missing sys privileges report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi



sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET linesize 500 pagesize 1000
col src_grantee format a18
col tgt_grantee format a18
col src_owner format a18
col tgt_owner format a18
col src_table_name format a30
col tgt_table_name format a30
col src_grantor format a18
col tgt_grantor format a18
col src_priv format a8
col tgt_priv format a8
col src_grant format a9
col tgt_grant format a9
col src_HIERARCHY format a10
col tgt_HIERARCHY format a10
col comments format a65

BREAK ON grantee SKIP 1 ON REPORT
spool ${spool_dir}/Reconciliation_Missing_Tab_Privs_Report.log
TTITLE CENTER "SCHEMAWISE MISSING TAB_PRIVS NAME RECONCILIATION REPORT" SKIP 3 CENTER


SELECT nvl(src.grantee,trgt.grantee) grantee,
  nvl(src.owner,trgt.owner) owner,
  nvl(src.table_name,trgt.table_name) table_name,
  nvl(src.grantor,trgt.grantor) grantor,
  nvl(src.privilege,trgt.privilege) privilege,
  nvl(src.grantable,trgt.grantable) grantable,
  nvl(src.hierarchy,trgt.hierarchy) hierarchy,
  NVL(src.counts,-1) src_cnt,
  NVL(trgt.counts,-1) trg_cnt,
  trgt.grantee grantee,
  trgt.owner owner,
  trgt.table_name table_name,
  trgt.grantor grantor,
  trgt.privilege privilege,
  trgt.grantable grantable,
  trgt.hierarchy hierarchy,
  CASE
    WHEN (NVL(trgt.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Tab Privs is Missing in Target'
    WHEN (NVL(src.counts,0) = NVL(trgt.counts,0) AND src.grantable <> trgt.grantable)
        THEN '*-*-*-* Action Required Check grantable option changed in Target'
    WHEN (NVL(src.counts,-1) < 0 )
        THEN '*-*-*-* Action Required Tab Privs is Increased in Target'
    END comments
FROM
  (SELECT runid,
  grantee,
  owner,
  table_name,
  grantor,
  privilege,
  grantable,
  hierarchy,
  counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 1
  and recon_type='TAB_PRIVS_MISSING'
  ) src
FULL OUTER JOIN
  (SELECT runid,
  grantee,
  owner,
  table_name,
  grantor,
  privilege,
  grantable,
  hierarchy,
  counts
  FROM ${target_db_user}.RECON_TABLE
  WHERE runid = 2
  and recon_type='TAB_PRIVS_MISSING'
  ) trgt
ON  (src.grantee   = trgt.grantee
AND  src.owner = trgt.owner
AND  src.table_name = trgt.table_name
AND  src.grantor = trgt.grantor
AND  src.privilege = trgt.privilege
AND  src.grantable = trgt.grantable
AND  src.hierarchy = trgt.hierarchy
)
where (NVL(src.counts,0) + NVL(trgt.counts,0)) < 2 OR (src.grantable <> trgt.grantable)
ORDER BY 1,2,3,4;
spool OFF
EOF
if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while generating missing Tab privileges report." |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

errorcount=`grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_*.log | wc -l`

if [ $errorcount -ne 0 ]; then
   echo
   echo "Passed...Target Steps compleated Successfully. There are Errors reported in Reconciliation logs for your attention." |tee -a ${spool_dir}/Target_Steps_Execution.log
fi
timestamp=$(date +%d-%m-%Y_%H-%M-%S)
echo End Date/Time : $timestamp |tee -a ${spool_dir}/Target_Steps_Execution.log

sqlplus -s "${conn_string}" << EOF
whenever sqlerror EXIT 1;
whenever oserror EXIT 1;
SET linesize 300;
SET feedback OFF;
SET heading OFF;
SET echo OFF;
SET pages 0;
col COUNT FOR 99
set serveroutput on
DECLARE
  c INT;
BEGIN
  SELECT COUNT(1) INTO c FROM dba_tables  WHERE table_name = 'RECON_TABLE' AND owner =upper('${target_db_user}');
  IF c = 1 THEN
    EXECUTE immediate 'drop table ${target_db_user}.RECON_TABLE purge';
  END IF;
END;
/
EOF

if [ $? != 0 ]; then
   echo "Failure - Step MF_DP_Recon_Target Failed while dropping RECON_TABLE in ${target_db_user}.RECON_TABLE" |tee -a ${spool_dir}/Target_Steps_Execution.log
   exit 1
fi

echo "Mismatch from Reconciliation_Object_Count_Report.log" > ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Object_Count_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Table_Counts_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------"|>> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Table_Counts_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Objects_Missing_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Objects_Missing_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Objects_Invalids_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Objects_Invalids_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_User_Accounts_Status_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_User_Accounts_Status_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Unusable_Indexes_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Unusable_Indexes_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Constraints_Count_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Constraints_Count_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Ref_Constraints_Disabled_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Ref_Constraints_Disabled_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Mismatch from Reconciliation_Grantee_Privs_Report.log" >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "--------------------------------------------------------------------------------------------------------------------">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
grep "\*-\*-\*-\*"  ${spool_dir}/Reconciliation_Grantee_Privs_Report.log >> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "====================================================================================================================">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "Also look at the below missing reports:- ">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "1) Reconciliation_Missing_Roles_Report.log">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "2) Reconciliation_Missing_Sys_Privs_Report.log">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "3) Reconciliation_Missing_Tab_Privs_Report.log">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
echo "====================================================================================================================">> ${spool_dir}/Reconciliation_Mismatch_Smmary_Report.log
