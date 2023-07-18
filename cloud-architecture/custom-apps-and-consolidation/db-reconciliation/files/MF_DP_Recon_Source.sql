--# Copyright (c) 2023, Oracle and/or its affiliates.
--# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
--# Purpose: Script to capture Source Objects counts & Metadata for Reconciliation after Migration/Upgrade Database.
--# The purpose of this script is to verify the migrated data where the target data is compared against original source data.
--# @author: Ananda Ghosh Dastidar

clear screen
set serveroutput on
set feed off
set echo off;
set verify off;
SET linesize 32767;
SET LONG 999999;
SET SHOW OFF;
SET TRIMS ON;
SET TERM OFF;

define gv_dp_version=3.0
col cur_timestamp new_value cur_timestamp
SET TERMOUT OFF;
SELECT CURRENT_TIMESTAMP cur_timestamp FROM DUAL;
SET TERMOUT ON;
PROMPT
PROMPT OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
PROMPT O                                                 ORACLE CLOUD LIFT SERVICES                                                O
PROMPT O                                         RECONCILIATION REPORT - SOURCE STEPS v&gv_dp_version                                         O
PROMPT O                                                 ( Oracle 11g onwards )                                                    O
PROMPT O                                              &cur_timestamp                                          O
PROMPT OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
PROMPT
select i.INSTANCE_NAME,i.HOST_NAME,i.VERSION,to_char(i.STARTUP_TIME,'YYYY/MM/DD HH:MI:SS') open_TIME 
from sys.v_$INSTANCE i;
PROMPT
PROMPT
SET PAGESIZE 0;
SET HEADING OFF;
SET VERIFY OFF;
SET ECHO OFF;
SET PAGES 0;

ACCEPT user_response PROMPT 'Please press Enter to continue : '

--Source check and validation
SET TERM OFF;
SPOOL raise_exit.sql;
DECLARE
	v_mode varchar2(20);
	c INT;
BEGIN
	select ltrim(open_mode) into v_mode from v$database;
	IF (v_mode<>'READ WRITE') THEN
		dbms_output.put_line('PROMPT Failed...Source Database is in '||v_mode||' Mode.');
		dbms_output.put_line('exit;');	
	ELSE
	    dbms_output.put_line('PROMPT Passed...Source Database is in '||v_mode||' Mode.');
		dbms_output.put_line('PROMPT Passed...Source Checks Passed...');
	END IF;
	SELECT COUNT(1) INTO c FROM USER_TABLES WHERE table_name = 'USER_TEMP';
	IF c = 1 THEN
		EXECUTE immediate 'DROP TABLE USER_TEMP PURGE';
	END IF;
	EXECUTE immediate 'CREATE TABLE USER_TEMP (SCHEMA_LIST VARCHAR2(100))';
	BEGIN
	EXECUTE IMMEDIATE 'insert into USER_TEMP select username from dba_users where username not in (''ANONYMOUS'',''CTXSYS'',''DBSNMP'',''EXFSYS'',''LBACSYS'',''MDSYS'',''MGMT_VIEW'',''OLAPSYS'',''ORDDATA'',''OWBSYS'',''ORDPLUGINS'',''ORDSYS'',''OUTLN'',''SI_INFORMTN_SCHEMA'',''SYS'',''SYSTEM'',''SYSMAN'',''SYSMAN_OPSS'',''SYSMAN_APM'',''SYSMAN_RO'',''MGMT_VIEW'',''WK_TEST'',''WKSYS'',''WKPROXY'',''WMSYS'',''XDB'',''PERFSTAT'',''TRACESVR'',''TSMSYS'',''DSSYS'',''DMSYS'',''SYSMAN_MDS'',''DIP'',''CSMIG'',''AWR_STAGE'',''AURORA$ORB$UNAUTHENTICATED'',''SCOTT'',''HR'',''SH'',''OE'',''PM'',''IX'',''BI'',''XS$NULL'',''ORACLE_OCM'',''SPATIAL_CSW_ADMIN_USR'',''SPATIAL_WFS_ADMIN_USR'',''MDDATA'',''FLOWS_FILES'',''FLOWS_30000'',''APEX_030200'',''APEX_PUBLIC_USER'',''APPQOSSYS'',''DBATOOLS_ADMIN'',''SQLTXPLAIN'',''PUBLIC'',''OPS$ORACLE'',''OWBSYS_AUDIT'',''OWBSYS'',''SYSTEM'',''XS$NULL'',''LBACSYS'',''OUTLN'',''DBSNMP'',''APPQOSSYS'',''DBSFWUSER'',''GGSYS'',''ANONYMOUS'',''CTXSYS'',''DVSYS'',''DVF'',''GSMADMIN_INTERNAL'',''MDSYS'',''OLAPSYS'',''XDB'',''WMSYS'',''GSMCATUSER'',''MDDATA'',''SYSBACKUP'',''REMOTE_SCHEDULER_AGENT'',''PDBADMIN'',''GSMUSER'',''SYSRAC'',''OJVMSYS'',''SI_INFORMTN_SCHEMA'',''PDBUSER'',''AUDSYS'',''DIP'',''ORDPLUGINS'',''SYSKM'',''ORDDATA'',''ORACLE_OCM'',''SYS$UMF'',''APEX_INSTANCE_ADMIN_USER'',''SYSDG'',''ORDSYS'',''APEX_LISTENER'',''FLOWS_FILES'',''APEX_PUBLIC_USER'',''APEX_REST_PUBLIC_USER'',''ORDS_PUBLIC_USER'',''ORDS_METADATA'',''UNIFIER'',''C##GGADMIN'',''GGADMIN'',''APEX_200200'',''APEX_040200'',''APEX_030200'',''AUD_OWNER'',''AUDTASK'')';
    commit;	
	END;
	dbms_output.put_line('PROMPT Passed...Temporary user list generated...');
	
END;
/
SPOOL OFF
SET TERMOUT ON;
SPOOL Source_Steps_Execution.log append
@raise_exit.sql
PROMPT
SET TERM ON;
spool off

PROMPT
PROMPT OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
PROMPT

whenever sqlerror exit 1;
whenever oserror exit 1;
set serveroutput on
col owner for a30
col object_type for a25
col counts for 99999

spool source_data.csv

REM Objects Counts

select '1'||','||'OBJ_COUNTS'||','||owner||',,'||object_type||',,,,,,,,,,,,,,,,,,,,,,,'||count(1) counts from dba_objects 
where object_type = 'TABLE' 
and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
and object_name in (select table_name from dba_tables where owner in (SELECT SCHEMA_LIST FROM USER_TEMP) and (IOT_TYPE is null or IOT_TYPE='IOT'))
and object_name not in (select table_name FROM dba_external_tables WHERE OWNER IN (SELECT SCHEMA_LIST FROM USER_TEMP) )
group by owner,object_type
union
select '1'||','||'OBJ_COUNTS'||','||owner||',,'||'INDEX'||',,,,,,,,,,,,,,,,,,,,,,,'||count(1) counts from dba_indexes
where owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by owner
union
select '1'||','||'OBJ_COUNTS'||','||owner||',,'||object_type||',,,,,,,,,,,,,,,,,,,,,,,'||count(1) counts from dba_objects
where object_type not in ('TABLE','INDEX')
and owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by owner,object_type
order by 1;

REM Tables Counts

DECLARE
val NUMBER;
BEGIN
FOR I IN (SELECT OWNER,TABLE_NAME FROM DBA_TABLES WHERE OWNER in (SELECT SCHEMA_LIST FROM USER_TEMP) and (IOT_TYPE is null or IOT_TYPE='IOT')
and TABLE_NAME NOT IN (SELECT table_name FROM dba_external_tables WHERE OWNER IN (SELECT SCHEMA_LIST FROM USER_TEMP)) order by owner,table_name) 
LOOP
EXECUTE IMMEDIATE 'SELECT count(1) FROM "' || i.owner||'"."'||i.table_name||'"' INTO val;
DBMS_OUTPUT.PUT_LINE('1'||','||'TABLE_COUNTS'||','||i.owner||',,,,,,,,,,,'||i.table_name || ',,,,,,,,,,,,,,' || val );
END LOOP;
END;
/

REM Missing Object Names
select '1'||','||'OBJECT_NAME'||','||OWNER||','||OBJECT_NAME||','||OBJECT_TYPE||','||SUBOBJECT_NAME||',,,,,,,,,,,,,,,,,,,,,'||STATUS||','||count(1) 
from dba_objects WHERE owner in (SELECT SCHEMA_LIST FROM USER_TEMP) 
AND (object_name NOT LIKE 'SYS_%' AND object_name NOT LIKE 'BIN$%' )
group by owner,object_name,object_type,subobject_name,status
order by OWNER, OBJECT_TYPE, STATUS, OBJECT_NAME, SUBOBJECT_NAME;


REM INVALID Objects

select '1'||','||'OBJ_INVALIDS'||','||OWNER||','||OBJECT_NAME||','||OBJECT_TYPE||','||SUBOBJECT_NAME||',,,,,,,,,,,,,,,,,,,,,'||STATUS||','||count(1) from dba_objects 
where owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
and STATUS <> 'VALID' 
group by owner,object_name,object_type,subobject_name,status
order by OWNER, OBJECT_TYPE, STATUS, OBJECT_NAME, SUBOBJECT_NAME;

REM USER ACCOUNT STATUS

select '1'||','||'USER_DETAILS'||','||username||','||Account_status||',,,,,,,,,,,,,,,,,,,,,,,,'||count(1) from dba_users 
where username in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by username,Account_status
order by username,Account_status;

REM source_unusable_index.csv;
SELECT '1'||','||'UNUSABLE_INDEX_TABLE'||','||owner||',,,,,'||index_name||','||tablespace_name||','||'ZZ'||','||'ZZ'||',,,,,,,,,,,,,,,,'||STATUS||','||count(1) FROM dba_indexes WHERE status = 'UNUSABLE'
and owner in (SELECT SCHEMA_LIST FROM USER_TEMP) group by owner,index_name,tablespace_name,STATUS
order by OWNER, index_name;

SELECT '1'||','||'UNUSABLE_INDEX_PARTITION'||','||index_owner||',,,,,'||index_name||','||tablespace_name||','||PARTITION_NAME||','||'ZZ'||',,,,,,,,,,,,,,,,'||STATUS||','||count(1) FROM dba_ind_PARTITIONS
WHERE status = 'UNUSABLE'
and index_owner in (SELECT SCHEMA_LIST FROM USER_TEMP) group by index_owner,index_name,tablespace_name,STATUS,PARTITION_NAME
order by index_owner, index_name;

SELECT '1'||','||'UNUSABLE_INDEX_SUB_PARTITION'||','||index_owner||',,,,,'||index_name||','||tablespace_name||','||partition_name||','||subpartition_name||',,,,,,,,,,,,,,,,'||STATUS||','||count(1)
FROM dba_ind_SUBPARTITIONS WHERE status='UNUSABLE'
and index_owner in (SELECT SCHEMA_LIST FROM USER_TEMP) group by index_owner,index_name,tablespace_name,STATUS,partition_name,subpartition_name
order by index_owner, index_name;

REM source_constraints_count.csv;

select '1'||','||'CONSTRAINT_TYPE_COUNTS'||','||owner||',,,,,,,,,'||constraint_type||',,,,,,,,,,,,,,,,'||count(1) counts from dba_constraints
where owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by 1,owner,constraint_type
order by 1;


REM source_r_constraints_dis.csv;

select '1'||','||'R_CONSTRAINTS_DISABLED'||','||cn.OWNER||',,,,,,,,,,'||cn.constraint_name||','||cn.table_name||','||cc.column_name||','||cn.r_owner||','||cn.r_constraint_name||',,,,,,,,,,,'||count(1)
from dba_constraints cn, dba_cons_columns cc
where cn.CONSTRAINT_TYPE='R' and cn.STATUS = 'DISABLED' and cn.owner in (SELECT SCHEMA_LIST FROM USER_TEMP)
and cn.owner=cc.owner
and cn.constraint_name=cc.constraint_name
and cn.table_name=cc.table_name
group by 1,cn.owner,cn.constraint_name,cn.table_name,cc.column_name,cn.r_owner,cn.r_constraint_name
ORDER BY 1;


REM source_privs_count.csv;

select '1'||','||'ROLE_SYS_TAB_PRIVS_COUNTS'||',,,,,,,,,,,,,,,,'||grantee||','||'ROLE_PRIVS'||',,,,,,,,,'||count(1) counts from dba_role_privs
where grantee in (SELECT SCHEMA_LIST FROM USER_TEMP) 
group by grantee
union
select '1'||','||'ROLE_SYS_TAB_PRIVS_COUNTS'||',,,,,,,,,,,,,,,,'||grantee||','||'SYS_PRIVS'||',,,,,,,,,'||count(1) counts from dba_sys_privs
where grantee in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by grantee
union
select '1'||','||'ROLE_SYS_TAB_PRIVS_COUNTS'||',,,,,,,,,,,,,,,,'||grantee||','||'TAB_PRIVS'||',,,,,,,,,'||count(1) counts from dba_tab_privs
where grantee in (SELECT SCHEMA_LIST FROM USER_TEMP)
group by grantee
order by 1;

REM source_role_privs
select '1'||','||'ROLE_PRIVS_MISSING'||',,,,,,,,,,,,,,,,'||GRANTEE||',,,,,,'||ADMIN_OPTION||','||GRANTED_ROLE||','||DEFAULT_ROLE||',,'||count(1) 
FROM dba_role_privs
WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
group by grantee,admin_option,granted_role,default_role;

REM source_sys_privs
select '1'||','||'SYS_PRIVS_MISSING'||',,,,,,,,,,,,,,,,'||GRANTEE||',,,'||PRIVILEGE||',,,'||ADMIN_OPTION||',,,,'||count(1)
FROM dba_sys_privs
WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
group by grantee,privilege,admin_option;

REM source_tab_privs
select '1'||','||'TAB_PRIVS_MISSING'||','||OWNER||',,,,,,,,,,,'||TABLE_NAME||',,,,'||GRANTEE||',,'||GRANTOR||','||PRIVILEGE||','||GRANTABLE||','||HIERARCHY||',,,,,'||count(1)
FROM dba_tab_privs
WHERE grantee IN (SELECT SCHEMA_LIST FROM USER_TEMP)
group by owner,table_name,grantee,grantor,privilege,grantable,hierarchy;

spool off
PROMPT
PROMPT OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
PROMPT
DECLARE	
c INT;
BEGIN
	SELECT COUNT(1) INTO c FROM USER_TABLES WHERE table_name = 'USER_TEMP';
	IF c = 1 THEN
		EXECUTE immediate 'DROP TABLE USER_TEMP PURGE';
		dbms_output.put_line('Passed...Source Steps compleated Successfully!!!');
	END IF;
END;
/
PROMPT
SET TERM ON;
SPOOL Source_Steps_Execution.log append;
PROMPT Passed...Source Steps compleated Successfully!!!
prompt
SPOOL OFF
exit;