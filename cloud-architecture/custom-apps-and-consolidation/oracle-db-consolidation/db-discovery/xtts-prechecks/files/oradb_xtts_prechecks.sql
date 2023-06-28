--# Copyright (c) 2023, Oracle and/or its affiliates.
--# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
--# Purpose: This script does self content check on database tablespaces.
--# This script is to be executed at the discovery phase if we identify the oracle database is to be migrated using XTTS method.
--# @author: Ananda Ghosh Dastidar


clear screen;
connect / as sysdba
define disversion = 'v1.4';

col open_mode for a15
col host_name for a45
col name for a15
COL NAME HEADING 'Name'
col pdbconid new_value v_pdbconid;
variable gv_multi NUMBER;
variable gv_dbinfosql REFCURSOR;
set truncate off
set numwidth 15
set heading off
set feedback off
set verify off
set lines 200
set pages 9999
set numf 9999999999999999
set serveroutput on

set heading on timing off
col version heading 'Version'
col startup_time heading 'STARTUP|TIME'
col FORCE_LOGGING format a30 wrap
col OBJECT_NAME for A30
column username for a45
column tablespace_name for a45

PROMPT ****************************************************************************************************************************************
PROMPT |                                               XTTS PRE-CHECK FOR ORACLE DATABASE &disversion                                                 |
PROMPT |                                                         ( Oracle 11g onwards )                                                        |
PROMPT ****************************************************************************************************************************************
PROMPT
--# Validation Block 2: Checking multitenant database
PROMPT
DECLARE
v_cdb_count number :=0;
BEGIN
EXECUTE IMMEDIATE 'select case when CDB =''YES'' then 1 else 0 END as CDB from sys.v_$database' into v_cdb_count;

If v_cdb_count = 0 THEN
DBMS_OUTPUT.put_line('INFO: This Oracle database is not multitenant!! Please check the details below');
:gv_multi := v_cdb_count;
END IF;

If v_cdb_count = 1 THEN
DBMS_OUTPUT.put_line('INFO: This Oracle database is a multitenant!! Please check the details below');
:gv_multi := v_cdb_count;
END IF;

EXCEPTION WHEN OTHERS THEN
DBMS_OUTPUT.put_line('INFO: This Oracle database is not multitenant!! Please check the details below');
:gv_multi := 0;
END;
/

DECLARE
v_sql varchar2(2000);
BEGIN
IF :gv_multi = 0 THEN
v_sql := 'select d.DBID,d.NAME,i.INSTANCE_NUMBER inst_id,d.OPEN_MODE,i.HOST_NAME,i.INSTANCE_NAME,to_char(i.STARTUP_TIME,''YYYY/MM/DD HH:MI:SS'') open_TIME from sys.v_$database d,sys.v_$INSTANCE i WHERE upper(d.NAME)=substr(upper(i.INSTANCE_NAME),0,length(upper(d.NAME)))';
OPEN :gv_dbinfosql FOR v_sql;
END IF;
IF :gv_multi = 1 THEN
v_sql := 'select p.con_id,p.name, p.inst_id, p.OPEN_MODE,i.host_name,i.instance_name,to_char(p.open_TIME,''YYYY/MM/DD HH:MI:SS'') open_TIME from gv$pdbs p, gv$instance i where i.inst_id=p.inst_id order by 1,2';
OPEN :gv_dbinfosql FOR v_sql;
END IF;
END;
/
print :gv_dbinfosql
BEGIN 
IF :gv_multi = 0 THEN DBMS_OUTPUT.put_line('Please verify the instance and press Enter to continue : '); END IF;
IF :gv_multi = 1 THEN DBMS_OUTPUT.put_line('Please verify CDB/PDB instance and Press Enter to continue : '); END IF;
END;
/
ACCEPT v_pdbconid CHAR FORMAT 'A20' PROMPT '>>>>>>' default 2
PROMPT

set markup HTML ON entmap off spool on
alter session set nls_date_format='YYYY-MM-DD HH24:Mi:SS';
alter session set nls_language=american;

REM
REM spool file name AUTOMATICALLY GENERATED
REM

REM Collection name SRDC_ or MOS_
define PREFIXHTM='MF_XTTS_DA'
column ORAGGSPOOLNAME new_val ORAGGSPOOLNAME
column SYSTEMDATE new_val SYSTEMDATE

select sysdate SYSTEMDATE from dual;
select '&&PREFIXHTM'||'_'||upper(instance_name)||'_'||to_char(sysdate,'YYYYMMDD_HH24MISS')||'.htm' ORAGGSPOOLNAME from v$instance, v$database;

spool &ORAGGSPOOLNAME
prompt <p style="text-align: center;"><strong><span style="text-shadow: rgb(136, 136, 136) -2px 0px 7px;"><span style="font-size: 30px; color: rgb(51, 102, 153);">xTTS Pre-check For ORACLE Database &disversion</span></span><span style="text-shadow: 3px 3px 2px rgba(136, 136, 136, 0.8);"> </span></strong>
prompt <span style="font-size: 14px; color: rgb(51, 102, 153); text-shadow: rgb(136, 136, 136) 1px -1px 5px;">( Oracle 11g onwards ) Report Date : &SYSTEMDATE</span></p>
prompt <table border='0' width='90%' align='center'><tr><td colspan=2 style="width:30%"><a name="top"><span style="font-size: 20px; color: rgb(51, 102, 153);"><strong> Main Menu </strong></span></a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Configuration Info </strong></li></td><td><a href="#Database">Database Information</a> | <a href="#Additional">Additional Information</a> </td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>xTTS Info </strong></li></td><td> <a href="#excludedTBS">Tablespaces excluded for XTTS Migration</a> | <a href="#eligibleTBS">Eligible Tablespace list for XTTS Migration</a> | <a href="#invalidTBS">Invalid userwise DEFAULT tablespace list</a> | <a href="#violation">Self-contained tablespace violations</a></td></tr></table>

PROMPT
prompt  <a name="Database"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Database Information : </strong></span></a><a href="#top">Go To Main Menu</a>
SELECT (select DBid from v$database) DB_ID,
(select name from v$database) DB_NAME,
(select instance_number from v$instance) INSTANCE,
(select version from v$instance) DB_VERSION,
(select decode(count(*),3,'1/8th OR Quarter RAC',7,'Half RAC',14,'Full RAC','Non-Exadata') from (select distinct cell_name from gv$cell_state)) Exadata_Option,
(select HOST_NAME from v$instance) HOST_NAME,
(select PLATFORM_ID from v$database) PLATFORM_ID,
(select Platform_name from v$database) OS,
(select VERSION from V$TIMEZONE_FILE) TIMEZ_VER,
(select DECODE(regexp_substr(banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(banner, '[^ ]+', 1, 4)) from v$version where banner like 'Oracle%') DB_EDITION,
(select CREATED from v$database) CREATED,
(Select to_char(startup_time, 'DD-MON-YY HH24:MI') from v_$instance) STARTUP_TIME,
(select round(((select sum(bytes) from dba_data_files))/1024/1024/1024,4) ||' GB' from dual) DB_SIZE from dual;

prompt  <a name="Additional"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Database Additional Information : </strong></span></a><a href="#top">Go To Main Menu</a>
SELECT a.DB_UNIQUE_NAME,b.LOGINS,a.LOG_MODE,a.OPEN_MODE,FORCE_LOGGING,a.current_scn CURRENT_SCN,a.DATABASE_ROLE from sys.v_$database a,sys.v_$instance b;
SELECT INSTANCE_NUMBER, INSTANCE_NAME, STATUS  FROM  GV$INSTANCE;

prompt  <a name="excludedTBS"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Tablespaces Excluded For XTTS Migration : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Defualt tablespaces are excluded from xTTS migration. Below is the list
select 'SYSTEM,SYSAUX,TEMP,UNDOTBS1,UNDOTBS2' Tablespace_Name from dual;

prompt  <a name="eligibleTBS"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Eligible Tablespace List For XTTS Migration : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Below is the list of eligible Tablespaces
select LISTAGG(tablespace_name, ',') WITHIN GROUP (ORDER BY tablespace_name) VALID_TABLESPACE_LIST_FOR_XTTS
from (
select d.tablespace_name tablespace_name
from dba_tablespaces d
where (d.CONTENTS not in ('TEMPORARY','UNDO') and d.TABLESPACE_NAME NOT IN ('SYSTEM','SYSAUX','TEMP','UNDOTBS1','UNDOTBS2'))
union
select default_tablespace tablespace_name
from dba_users where default_tablespace in (select tablespace_name from dba_tablespaces where TABLESPACE_NAME NOT IN ('SYSTEM','SYSAUX','TEMP','UNDOTBS1','UNDOTBS2'))
order by 1
);

prompt  <a name="invalidTBS"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Invalid Userwise DEFAULT tablespace List(IF ANY) : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Below is the list of invalid userwise DEFUALT tablespace 
select username,default_tablespace tablespace_name,'<span style="font-size: 14px; color: rgb(255,0,0);">This Tablespace does not exists/dropped.. Remap this user at Target</span>' TBS_Remarks
from dba_users where default_tablespace not in (select tablespace_name from dba_tablespaces)
order by 1;

prompt  <a name="violation"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Self-contained Tablespace Violations Status(IF ANY) : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Status of self-contained tablespace violations 
prompt
DECLARE
tbs_list clob;
v_count number :=0;
BEGIN

select LISTAGG(tablespace_name, ',') WITHIN GROUP (ORDER BY tablespace_name) tablespace_name into tbs_list
from (
select d.tablespace_name tablespace_name
from dba_tablespaces d
where (d.CONTENTS not in ('TEMPORARY','UNDO') and d.TABLESPACE_NAME NOT IN ('SYSTEM','SYSAUX','TEMP','UNDOTBS1','UNDOTBS2'))
union
select default_tablespace tablespace_name
from dba_users where default_tablespace in (select tablespace_name from dba_tablespaces where TABLESPACE_NAME NOT IN ('SYSTEM','SYSAUX','TEMP','UNDOTBS1','UNDOTBS2'))
order by 1
);

sys.DBMS_TTS.TRANSPORT_SET_CHECK(TS_LIST => tbs_list ,INCL_CONSTRAINTS => TRUE,FULL_CHECK => TRUE);
FOR cur_err_desc IN (SELECT VIOLATIONS FROM sys.TRANSPORT_SET_VIOLATIONS)
LOOP
   v_count:= v_count + 1;
   	dbms_output.put_line('<span style="font-size: 14px; color: rgb(255,0,0);">#'||v_count||' Violations found: '||cur_err_desc.VIOLATIONS||'</span>');
END LOOP;

SELECT count(*) into v_count FROM sys.TRANSPORT_SET_VIOLATIONS;
If v_count=0 THEN
	dbms_output.put_line('<span style="font-size: 14px; color: rgb(34,139,34);">Success... No violations found based on self-contained tablespace</span>');
END IF;
END;
/

prompt  
prompt  <a name="eor"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> End Of Report: </strong></span></a><a href="#top">Go To Main Menu</a>
set timing off
set markup html off
spool off
prompt
exit