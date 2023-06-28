--# Copyright (c) 2023, Oracle and/or its affiliates.
--# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
--# Purpose: To capture database details (Oracle database 11g onwards) for ZDM online based migration.
--# This should be executed at discovery phase if we identify the Oracle database is to be migrated online using ZDM Tool.
--# @author: Ananda Ghosh Dastidar

clear screen;
connect / as sysdba
define disversion = 'v1.2';
set markup HTML ON entmap off spool on

set truncate off
set numwidth 15
set heading off
set feedback off
set verify off
set lines 200
set pages 9999
set numf 9999999999999999
alter session set nls_date_format='YYYY-MM-DD HH24:Mi:SS';
alter session set nls_language=american;

REM
REM spool file name AUTOMATICALLY GENERATED
REM

REM Collection name SRDC_ or MOS_
define PREFIXHTM='MF_ZDM_DA'
column ORAGGSPOOLNAME new_val ORAGGSPOOLNAME
column SYSTEMDATE new_val SYSTEMDATE

select sysdate SYSTEMDATE from dual;
select '&&PREFIXHTM'||'_'||upper(instance_name)||'_'||to_char(sysdate,'YYYYMMDD_HH24MISS')||'.htm' ORAGGSPOOLNAME from v$instance, v$database;

spool &ORAGGSPOOLNAME
prompt <p style="text-align: center;"><strong><span style="text-shadow: rgb(136, 136, 136) -2px 0px 7px;"><span style="font-size: 30px; color: rgb(51, 102, 153);">ZDM Discovery Utility For ORACLE Database &disversion</span></span><span style="text-shadow: 3px 3px 2px rgba(136, 136, 136, 0.8);"> </span></strong>
prompt <span style="font-size: 14px; color: rgb(51, 102, 153); text-shadow: rgb(136, 136, 136) 1px -1px 5px;">( For Oracle Database 11g onwards ) Report Date : &SYSTEMDATE</span></p>
prompt <table border='0' width='90%' align='center'><tr><td colspan=2 style="width:30%"><a name="top"><span style="font-size: 20px; color: rgb(51, 102, 153);"><strong> Main Menu </strong></span></a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Genral Info </strong></li></td><td><a href="#objsize">Segment Details of Tables and Indexes</a> | <a href="#seqlist">Schema-wise Sequence List</a> | <a href="#invobjlist">Schema-wise Invalid Object List</a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Configuration Info </strong></li></td><td><a href="#Database">Database Information</a> | <a href="#Additional">Additional Information</a> | <a href="#Parameters">Parameters</a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Redo Log Info </strong></li></td><td> <a href="#Redo">Redo Log Information</a> | <a href="#Archivelog">Archivelog Volume per Day</a> | <a href="#redohist">Redo Switch History</a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Undo Info </strong></li></td><td> <a href="#undo">UNDO usage per Day</a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>Unsupported Info </strong></li></td><td> <a href="#unsupportedtype">Unsupported Table Type</a> | <a href="#supportmodenone">Support Mode = NONE</a> | <a href="#mviews">Materialized View List</a> | <a href="#nopk">Missing Primary Key/Unique Key Table</a> | <a href="#supplemental">Tables having Supplemental log Disabled</a> | <a href="#fnindx">Tables with function based index</a> | <a href="#external">External Table List</a></td></tr><tr><td> <li style="font-size: 12px; color: rgb(51, 102, 153);"><strong>ZDM Specific Info </strong></li></td><td> <a href="#Prereq">ZDM Pre-Requisite Status Summary</a> | <a href="#admusrroles">ZDM Specific Mandatory User Roles and privileges</a></td></tr></table>

PROMPT
set heading on timing off
col open_mode for a15
col host_name for a45
col name for a15

COL NAME HEADING 'Name'
col OS_PLATFORM format a30 wrap
col current_scn format 99999999999999999
col MAX_VALUE format 999999999999999999999999999999
col host Heading 'Host'
col version heading 'Version'
col startup_time heading 'STARTUP|TIME'
col database_role Heading 'DATABASE|ROLE'
col SUPPORT_MODE heading 'SUPPORT_MODE'
col VALUE for a5
col DB_Edition heading 'DATABASE|EDITION' format a10
col FORCE_LOGGING format a30 wrap
col OBJECT_NAME for A30
col SEQUENCE_NAME for A30
col SEQUENCE_OWNER for A30
col CYCLE_FLAG for A10
col ORDER_FLAG for A10
col SUPPORT_MODE for A30
col SUPPLEMENTAL_LOG_DATA_MIN format a20 wrap
col REMOTE_ARCHIVE format a20 wrap

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
SELECT a.DB_UNIQUE_NAME,b.LOGINS,a.LOG_MODE,a.OPEN_MODE,a.REMOTE_ARCHIVE,FORCE_LOGGING,SUPPLEMENTAL_LOG_DATA_MIN,a.current_scn CURRENT_SCN,a.DATABASE_ROLE from sys.v_$database a,sys.v_$instance b;
SELECT INSTANCE_NUMBER, INSTANCE_NAME, STATUS  FROM  GV$INSTANCE;

prompt  <a name="Prereq"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> ZDM Pre-Requisite Status Summary : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Please validate below check list prior to proceed with migration using ZDM

WITH SERVER_INFO AS (
SELECT (select LOG_MODE  from v$database) LOG_MODE,
(select decode(count(1), 0, 'NO', 'YES') from (SELECT REMOTE_ARCHIVE from sys.v_$database WHERE upper(REMOTE_ARCHIVE)='ENABLED')) REMOTE_ARC_ENABLED,
(select decode(count(1), 0, 'NO', 'YES') from (SELECT FORCE_LOGGING from sys.v_$database WHERE upper(FORCE_LOGGING)='YES')) FORCE_LOGGING,
(select decode(count(1), 0, 'NO', 'YES') from (SELECT SUPPLEMENTAL_LOG_DATA_MIN from sys.v_$database WHERE upper(SUPPLEMENTAL_LOG_DATA_MIN)='YES')) SUPPLEMENTAL_LOG,
(select to_char(VERSION) from V$TIMEZONE_FILE) TIMEZ_VER,
(SELECT max(round(s.bytes/1024/1024/1024,2)) Lob_max_size FROM   dba_lobs l JOIN dba_segments s ON s.owner = l.owner AND s.segment_name = l.segment_name
where l.owner not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','DBSFWUSER','GGSYS','DVSYS','DVF','GSMADMIN_INTERNAL','GSMCATUSER','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','PDBUSER','AUDSYS','SYS$UMF','APEX_LISTENER','ORDS_METADATA','APEX_200200')) LOB_MAX,
(select count(1) from dba_objects where status<>'VALID' and owner not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','DBSFWUSER','GGSYS','DVSYS','DVF','GSMADMIN_INTERNAL','GSMCATUSER','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','PDBUSER','AUDSYS','SYS$UMF','APEX_LISTENER','ORDS_METADATA','APEX_200200')) INVALID_OBJ,
(select count(1) from dba_sequences where SEQUENCE_OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')) SEQ_TOT,
(select decode(count(1), 0, 'NO', 'YES') from (SELECT name, value FROM v$parameter WHERE upper(NAME)='ENABLE_GOLDENGATE_REPLICATION' and upper(value)='TRUE')) GG_ENABLED,
(select decode(count(1), 0, 'NO', 'YES') from (SELECT name, value FROM v$parameter WHERE upper(NAME)='STREAMS_POOL_SIZE' and value >= '2147483648')) STREAMS_POOL_SIZE,
(select decode(count(1), 0, 'NO', 'YES') from (select DIRECTORY_NAME from dba_directories where exists (select DIRECTORY_NAME from dba_directories where upper(DIRECTORY_NAME) = 'ZDM_DATA_PUMP_DIR'))) ZDM_DATA_PUMP_DIR,
(select decode(count(1), 0, 'NO', 'YES') from (select tablespace_name from dba_tablespaces where exists (select tablespace_name from dba_tablespaces where upper(tablespace_name) = 'ZDM_DATA01'))) ZDM_DATA01,
(select decode(count(1), 0, 'NO', 'YES') from (select username from dba_users where exists (select username from dba_users where upper(username) = 'ZDMDUMP'))) ZDMDUMP,
(select decode(count(1), 0, 'NO', 'YES') from (select username from dba_users where exists (select username from dba_users where upper(username) = 'GGADMIN'))) GGADMIN,
(select decode(count(1), 0, 'NO', 'YES') from (select role from dba_roles where exists (select role from dba_roles where upper(role) = 'DB_CONNECT'))) DB_CONNECT,
(select decode(count(1), 0, 'NO', 'YES') from (select role from dba_roles where exists (select role from dba_roles where upper(role) = 'GGADMIN_OWNER_ROLE'))) GGADMIN_OWNER_ROLE
from dual
)
SELECT 'Is Archive Log Mode Enabled' KEY_POINTS,case when LOG_MODE='ARCHIVELOG' THEN 'YES' ELSE 'NO' END KEY_VALUE, case when LOG_MODE='ARCHIVELOG' THEN 'No Action required' else 'Action Required : Enable ARCHIVELOG mode at source..' end ACTION_POINTS FROM  SERVER_INFO union all
SELECT 'Is REMOTE ARCHIVE Enabled' KEY_POINTS,REMOTE_ARC_ENABLED KEY_VALUE, case when REMOTE_ARC_ENABLED='YES' THEN 'No Action required' else 'Action Required : Enable REMOTE ARCHIVE at source..' end ACTION_POINTS FROM  SERVER_INFO union all
SELECT 'Is FORCE LOGGING Enabled' KEY_POINTS,FORCE_LOGGING KEY_VALUE, case when FORCE_LOGGING='YES' THEN 'No Action required' else 'Action Required : Enable FORCE LOGGING at source..' end ACTION_POINTS FROM  SERVER_INFO union all
SELECT 'Is SUPPLEMENTAL LOG DATA Enabled' KEY_POINTS,SUPPLEMENTAL_LOG KEY_VALUE, case when SUPPLEMENTAL_LOG='YES' THEN 'No Action required' else 'Action Required : Enable SUPPLEMENTAL LOG DATA at source..' end ACTION_POINTS FROM  SERVER_INFO union all
SELECT 'LOB Max Size' KEY_POINTS,to_char(nvl(LOB_MAX,0))||' GB' KEY_VALUE, case when nvl(LOB_MAX,0)>0 then 'Needs to be highlighted.Please refer main Discovery report..' else 'No Action required' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Invalid Object Count' KEY_POINTS,to_char(nvl(INVALID_OBJ,0)) KEY_VALUE, case when nvl(INVALID_OBJ,0)>0 then 'Needs to be highlighted.Please refer list below..' else 'No Action required' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Total Sequence Count' KEY_POINTS,to_char(nvl(SEQ_TOT,0)) KEY_VALUE, case when nvl(SEQ_TOT,0)>0 then 'Action Required : Needs to be re-created at target after migration.Please refer list below..' else 'No Action required' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'TIMEZONE_FILE version' KEY_POINTS,TIMEZ_VER KEY_VALUE, case when nvl(TIMEZ_VER,0)>0 THEN 'Action Required : Please verify the same at Target' end ACTION_POINTS FROM  SERVER_INFO union all
SELECT 'Is ENABLE_GOLDENGATE_REPLICATION parameter enabled' KEY_POINTS,GG_ENABLED KEY_VALUE, case when GG_ENABLED='YES' then 'No Action required' else 'Action Required : Enable this parameter at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is STREAMS_POOL_SIZE >= 2GB' KEY_POINTS,STREAMS_POOL_SIZE KEY_VALUE, case when STREAMS_POOL_SIZE='YES' then 'No Action required' else 'Action Required : Increase this value >= 2GB at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is ZDM_DATA_PUMP_DIR directory Exists' KEY_POINTS,ZDM_DATA_PUMP_DIR KEY_VALUE, case when ZDM_DATA_PUMP_DIR='YES' then 'No Action required' else 'Action Required : Create ZDM_DATA_PUMP_DIR directory as ''<NFS_SHARE"/ZDM/<SOURCE_TARGET>'' at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is DB_CONNECT Role Exists' KEY_POINTS,DB_CONNECT KEY_VALUE, case when DB_CONNECT='YES' then 'No Action required' else 'Action Required : Create DB_CONNECT Role at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is GGADMIN_OWNER_ROLE Role Exists' KEY_POINTS,GGADMIN_OWNER_ROLE KEY_VALUE, case when GGADMIN_OWNER_ROLE='YES' then 'No Action required' else 'Action Required : Create GGADMIN_OWNER_ROLE Role at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is ZDM_DATA01 Tablespace Exists' KEY_POINTS,ZDM_DATA01 KEY_VALUE, case when ZDM_DATA01='YES' then 'No Action required' else 'Action Required : Create ZDM_DATA01 tablespace at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is ZDMDUMP User Exists' KEY_POINTS,ZDMDUMP KEY_VALUE, case when ZDMDUMP='YES' then 'No Action required' else 'Action Required : Create ZDMDUMP User at source..' end REQUIRED_ACTION FROM SERVER_INFO union all
SELECT 'Is GGADMIN User Exists' KEY_POINTS,GGADMIN KEY_VALUE, case when GGADMIN='YES' then 'No Action required' else 'Action Required : Create GGADMIN User at source..' end REQUIRED_ACTION FROM SERVER_INFO;

prompt  <a name="admusrroles"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> ZDM Specific mandatory User Roles and privileges : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Please find the mandatory User Roles and privileges for GGADMIN and ZDMDUMP users

select 1 sl#,'Is CREATE SESSION granted to DB_CONNECT role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required' else 'Action Required : Please grant CREATE SESSION to DB_CONNECT role' end ACTION_POINTS from  dba_sys_privs  where grantee='DB_CONNECT' and privilege = 'CREATE SESSION' union
select 2,'Is CREATE SYNONYM granted to DB_CONNECT role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required' else 'Action Required : Please grant CREATE SYNONYM to DB_CONNECT role' end ACTION_POINTS from  dba_sys_privs  where grantee='DB_CONNECT' and privilege = 'CREATE SYNONYM' union
select 3,'Is CREATE CLUSTER granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE CLUSTER to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE CLUSTER' union
select 4,'Is CREATE INDEXTYPE granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE INDEXTYPE to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE INDEXTYPE' union
select 5,'Is CREATE JOB granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE JOB to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE JOB' union
select 6,'Is CREATE MATERIALIZED VIEW granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE MATERIALIZED VIEW to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE MATERIALIZED VIEW' union
select 7,'Is CREATE PROCEDURE granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE PROCEDURE to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE PROCEDURE' union
select 8,'Is CREATE PUBLIC SYNONYM granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE PUBLIC SYNONYM to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE PUBLIC SYNONYM' union
select 9,'Is CREATE SEQUENCE granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE SEQUENCE to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE SEQUENCE' union
select 10,'Is CREATE SESSION granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE SESSION to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE SESSION' union
select 11,'Is CREATE SYNONYM granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE SYNONYM to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE SYNONYM' union
select 12,'Is CREATE TABLE granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE TABLE to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE TABLE' union
select 13,'Is CREATE TRIGGER granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE TRIGGER to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE TRIGGER' union
select 14,'Is CREATE TYPE granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE TYPE to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE TYPE' union
select 15,'Is CREATE VIEW granted to GGADMIN_OWNER_ROLE role' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE VIEW to GGADMIN_OWNER_ROLE role' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN_OWNER_ROLE' and privilege = 'CREATE VIEW' union
select 16,'Is GGADMIN_OWNER_ROLE role granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant GGADMIN_OWNER_ROLE role to GGADMIN user' end ACTION_POINTS from  dba_role_privs where grantee='GGADMIN' and granted_role = 'GGADMIN_OWNER_ROLE' union
select 17,'Is DB_CONNECT role granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant DB_CONNECT role to GGADMIN user' end ACTION_POINTS from  dba_role_privs where grantee='GGADMIN' and granted_role = 'DB_CONNECT' union
select 18,'Is SELECT ANY TRANSACTION granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant SELECT ANY TRANSACTION to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'SELECT ANY TRANSACTION' union
select 19,'Is SELECT ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant SELECT ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'SELECT ANY TABLE' union
select 20,'Is FLASHBACK ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant FLASHBACK ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'FLASHBACK ANY TABLE' union
select 21,'Is ALTER ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant ALTER ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'ALTER ANY TABLE' union
select 22,'Is CREATE JOB granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE JOB to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'CREATE JOB' union
select 23,'Is SELECT ANY DICTIONARY granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant SELECT ANY DICTIONARY to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'SELECT ANY DICTIONARY' union
select 24,'Is DEQUEUE ANY QUEUE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant DEQUEUE ANY QUEUE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'DEQUEUE ANY QUEUE' union
select 25,'Is DELETE ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant DELETE ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'DELETE ANY TABLE' union
select 26,'Is UPDATE ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant UPDATE ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'UPDATE ANY TABLE' union
select 27,'Is CREATE RULE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE RULE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'CREATE RULE' union
select 28,'Is EXECUTE ANY RULE SET granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant EXECUTE ANY RULE SET to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'EXECUTE ANY RULE SET' union
select 29,'Is CREATE RULE SET granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE RULE SET to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'CREATE RULE SET' union
select 30,'Is CREATE VIEW granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE VIEW to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'CREATE VIEW' union
select 31,'Is INSERT ANY TABLE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant INSERT ANY TABLE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'INSERT ANY TABLE' union
select 32,'Is ALTER SESSION granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant ALTER SESSION to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'ALTER SESSION' union
select 33,'Is CREATE EVALUATION CONTEXT granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CREATE EVALUATION CONTEXT to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'CREATE EVALUATION CONTEXT' union
select 34,'Is UNLIMITED TABLESPACE granted to GGADMIN user' GGADMIN_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant UNLIMITED TABLESPACE to GGADMIN user' end ACTION_POINTS from  dba_sys_privs where grantee='GGADMIN' and privilege = 'UNLIMITED TABLESPACE';

select 1 Sl#,'Is SELECT_CATALOG_ROLE role granted to ZDMDUMP user' ZDMDUMP_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required' else 'Action Required : Please grant DATAPUMP_EXP_FULL_DATABASE role to ZDMDUMP user' end ACTION_POINTS from  dba_role_privs where grantee='ZDMDUMP' and granted_role = 'DATAPUMP_EXP_FULL_DATABASE' union
select 2,'Is CONNECT role granted to ZDMDUMP user' ZDMDUMP_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant CONNECT to ZDMDUMP user' end ACTION_POINTS from  dba_role_privs where grantee='ZDMDUMP' and granted_role = 'CONNECT' union
select 3,'Is DATAPUMP_IMP_FULL_DATABASE role granted to ZDMDUMP user' ZDMDUMP_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required'	else 'Action Required : Please grant DATAPUMP_IMP_FULL_DATABASE to ZDMDUMP user' end ACTION_POINTS from  dba_role_privs where grantee='ZDMDUMP' and granted_role = 'DATAPUMP_IMP_FULL_DATABASE' union
select 4,'Is EXEMPT ACCESS POLICY granted to ZDMDUMP user' ZDMDUMP_ROLES_AND_PRIVS, decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required' else 'Action Required : Please grant EXEMPT ACCESS POLICY to ZDMDUMP user' end ACTION_POINTS from  dba_sys_privs where grantee='ZDMDUMP' and privilege = 'EXEMPT ACCESS POLICY' union
select 5,'Is QUOTA UNLIMITED on ZDM_DATA01 Tbs granted to ZDMDUMP user' ZDMDUMP_ROLES_AND_PRIVS,decode(count(1), 0, 'NO', 'YES') KEY_VALUE,case when decode(count(1), 0, 'NO', 'YES')='YES' THEN 'No Action required' else 'Action Required : Please grant QUOTA UNLIMITED on ZDM_DATA01 Tbs to ZDMDUMP user' end ACTION_POINTS  from dba_ts_quotas WHERE greatest(max_bytes, -1)= -1 and username='ZDMDUMP' and tablespace_name='ZDM_DATA01';


prompt  <a name="Redo"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Redo Log Information : </strong></span></a><a href="#top">Go To Main Menu</a>
select group#, THREAD#, SEQUENCE#, BYTES/1024/1024 BYTES, MEMBERS, ARCHIVED, STATUS, FIRST_CHANGE#, to_char(FIRST_TIME,'DD-Mon-YYYY HH24:Mi:SS') First_time  from sys.v_$log order by group#;
select group#, status, member, type from sys.v_$logfile order by group#;

prompt  <a name="Archivelog"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong>Archivelog Volume per Day : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Summary of log volume processed by day for last 30 days:
select to_char(first_time, 'DD-MON-YYYY') ArchiveDate,round((sum(BLOCKS*BLOCK_SIZE/1024/1024)),2) LOG_in_MB
from sys.v_$archived_log
where first_time > sysdate - 30
group by to_char(first_time, 'DD-MON-YYYY')
order by to_char(first_time, 'DD-MON-YYYY');

prompt  <a name="undo"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> UNDO usage per Day  : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Summary of UNDO used and Tuned Undoretention by day for last 30 days:
select substr( time,1,8) Snap_Date ,sum(used_GB) USED_GB, sum(TUNED_UNDORETENTION) TUNED_UNDORETENTION from (
select to_char(begin_time,'yyyymmdd hh24') time ,
round(max(UNDOBLKS+ EXPIREDBLKS+UNEXPIREDBLKS+ACTIVEBLKS)*8192/(1024*1024*1024),2) USED_GB, 
TUNED_UNDORETENTION
from dba_hist_undostat
where begin_time > sysdate - 30
group by to_char(begin_time,'yyyymmdd hh24'), TUNED_UNDORETENTION
order by to_char(begin_time,'yyyymmdd hh24')) a
group by substr( time,1,8) order by 1 ;

prompt  <a name="unsupportedtype"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> All Unsupported Table Type (if any): </strong></span></a><a href="#top">Go To Main Menu</a>
SELECT OWNER, TABLE_NAME, CLUSTER_NAME, TABLE_TYPE FROM all_all_tables 
WHERE OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
AND (cluster_name is NOT NULL or TABLE_TYPE is NOT NULL)
union all
select null,null,null,null from dual;

Prompt
Prompt <a name="supportmodenone"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong>Schema-wise Objects List with Support Mode = NONE : </strong></span></a><a href="#top">Go To Main Menu</a>

Select OWNER, OBJECT_NAME, SUPPORT_MODE from DBA_GOLDENGATE_SUPPORT_MODE where support_mode ='NONE' 
and OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all select null,null,null from dual order by OWNER;

prompt  <a name="Parameters"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Required Parameters for Golden Gate : </strong></span></a><a href="#top">Go To Main Menu</a>
select name Parameter_name,value from v$parameter where name in ('streams_pool_size','enable_goldengate_replication','shared_pool_size','db_recovery_file_dest_size');

Prompt <a name="external"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong>External Table Details : </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Below external tables are not supported in GG. List will be used to Exclude the external tables from the Replication

select owner,table_name,DEFAULT_DIRECTORY_NAME from DBA_EXTERNAL_TABLES union all select ' ',' ',' ' from dual;

Prompt <a name="mviews"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong>Materialized View List </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Below Materialized Views are not supported in GG. List will be used to Exclude the MView from the Replication

select owner, object_name, object_type, status
from dba_objects where object_type='MATERIALIZED VIEW'
and OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all
select null,null,null,null from dual;

Prompt <a name="nopk"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Missing Primary Key/Unique Key Table List </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Replciated Tables should have primary key/Unique key if we do not go by all column replication

select t.owner as schema_name,t.table_name
from sys.dba_tables t left join sys.dba_constraints c
on t.owner = c.owner and t.table_name = c.table_name and c.constraint_type in ('P','U')
where c.constraint_type is null
and t.OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all select null,null from dual
order by 1, 2;

Prompt <a name="supplemental"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong>Tables having Supplemental log Disabled </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Supplemental log enabling must for all Tables involved in replication

select OWNER,TABLE_NAME,'Supplemental log Not Enabled' SUPPLEMENTAL_LOG_STATUS from dba_tables
where owner not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
minus
select OWNER,TABLE_NAME,NULL from dba_log_groups
where OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all select null,null,null from dual
order by 1;

Prompt <a name="fnindx"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Tables with function based index </strong></span></a><a href="#top">Go To Main Menu</a>
Prompt Note : Tables  with function based index might have issues while data replication
select owner, index_name, index_type from dba_indexes where index_type like 'FUNCTION-BASED%' and OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all select ' ', ' ', ' ' from dual
order by 1;

Prompt <a name="objsize"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Segment Details of Tables and Indexes: </strong></span></a><a href="#top">Go To Main Menu</a>
select owner,segment_name,segment_type,bytes/1024/1024 "MB" from dba_segments
 WHERE OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
and segment_type in ('TABLE','INDEX')
order by 1,3;

Prompt <a name="seqlist"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Schema-wise Sequence List: </strong></span></a><a href="#top">Go To Main Menu</a>
select * from dba_sequences
where SEQUENCE_OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK')
union all 
select null,null,null,null,null,null,null,null,null from dual
order by 1, 2;

Prompt <a name="invobjlist"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Schema-wise Invalid Object List: </strong></span></a><a href="#top">Go To Main Menu</a>
select OWNER, OBJECT_NAME, SUBOBJECT_NAME, OBJECT_TYPE, STATUS from dba_objects 
where OWNER not in ('ANONYMOUS','CTXSYS','DBSNMP','EXFSYS','LBACSYS','MDSYS','MGMT_VIEW','OLAPSYS','ORDDATA','OWBSYS','ORDPLUGINS','ORDSYS','OUTLN','SI_INFORMTN_SCHEMA','SYS','SYSTEM','SYSMAN','SYSMAN_OPSS','SYSMAN_APM','SYSMAN_RO','MGMT_VIEW','WK_TEST','WKSYS','WKPROXY','WMSYS','XDB','PERFSTAT','TRACESVR','TSMSYS','DSSYS','DMSYS','SYSMAN_MDS','DIP','CSMIG','AWR_STAGE','AURORA$ORB$UNAUTHENTICATED','SCOTT','HR','SH','OE','PM','IX','BI','XS$NULL','ORACLE_OCM','SPATIAL_CSW_ADMIN_USR','SPATIAL_WFS_ADMIN_USR','MDDATA','FLOWS_FILES','FLOWS_30000','APEX_030200','APEX_PUBLIC_USER','APPQOSSYS','DBATOOLS_ADMIN','SQLTXPLAIN','PUBLIC','OPS$ORACLE','OWBSYS_AUDIT','OWBSYS','SYSTEM','XS$NULL','LBACSYS','OUTLN','DBSNMP','APPQOSSYS','DBSFWUSER','GGSYS','ANONYMOUS','CTXSYS','DVSYS','DVF','GSMADMIN_INTERNAL','MDSYS','OLAPSYS','XDB','WMSYS','GSMCATUSER','MDDATA','SYSBACKUP','REMOTE_SCHEDULER_AGENT','PDBADMIN','GSMUSER','SYSRAC','OJVMSYS','SI_INFORMTN_SCHEMA','PDBUSER','AUDSYS','DIP','ORDPLUGINS','SYSKM','ORDDATA','ORACLE_OCM','SYS$UMF','APEX_INSTANCE_ADMIN_USER','SYSDG','ORDSYS','APEX_LISTENER','FLOWS_FILES','APEX_PUBLIC_USER','APEX_REST_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA','APEX_200200','APEX_040200','APEX_030200','RECON_USER','AUD_OWNER','AUDTASK') 
and STATUS <> 'VALID' order by OWNER, OBJECT_TYPE, STATUS, OBJECT_NAME, SUBOBJECT_NAME;

Prompt <a name="redohist"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> Redo Log Switch History </strong></span></a><a href="#top">Go To Main Menu</a>
SELECT  to_char(trunc(first_time),'DD-Mon-YY') "Date",to_char(first_time, 'Dy') "Day",count(1) Total,
SUM(decode(to_char(first_time, 'hh24'),'00',1,0)) "h0",SUM(decode(to_char(first_time, 'hh24'),'01',1,0)) "h1",
SUM(decode(to_char(first_time, 'hh24'),'02',1,0)) "h2",
SUM(decode(to_char(first_time, 'hh24'),'03',1,0)) "h3",
SUM(decode(to_char(first_time, 'hh24'),'04',1,0)) "h4",
SUM(decode(to_char(first_time, 'hh24'),'05',1,0)) "h5",
SUM(decode(to_char(first_time, 'hh24'),'06',1,0)) "h6",
SUM(decode(to_char(first_time, 'hh24'),'07',1,0)) "h7",
SUM(decode(to_char(first_time, 'hh24'),'08',1,0)) "h8",
SUM(decode(to_char(first_time, 'hh24'),'09',1,0)) "h9",
SUM(decode(to_char(first_time, 'hh24'),'10',1,0)) "h10",
SUM(decode(to_char(first_time, 'hh24'),'11',1,0)) "h11",
SUM(decode(to_char(first_time, 'hh24'),'12',1,0)) "h12",
SUM(decode(to_char(first_time, 'hh24'),'13',1,0)) "h13",
SUM(decode(to_char(first_time, 'hh24'),'14',1,0)) "h14",
SUM(decode(to_char(first_time, 'hh24'),'15',1,0)) "h15",
SUM(decode(to_char(first_time, 'hh24'),'16',1,0)) "h16",
SUM(decode(to_char(first_time, 'hh24'),'17',1,0)) "h17",
SUM(decode(to_char(first_time, 'hh24'),'18',1,0)) "h18",
SUM(decode(to_char(first_time, 'hh24'),'19',1,0)) "h19",
SUM(decode(to_char(first_time, 'hh24'),'20',1,0)) "h20",
SUM(decode(to_char(first_time, 'hh24'),'21',1,0)) "h21",
SUM(decode(to_char(first_time, 'hh24'),'22',1,0)) "h22",
SUM(decode(to_char(first_time, 'hh24'),'23',1,0)) "h23"
from v$log_history 
where first_time > sysdate - 30
group by trunc(first_time), to_char(first_time, 'Dy')
order by trunc(first_time);

prompt  <a name="eor"><span style="font-size: 16px; color: rgb(51, 102, 153);"><strong> End Of Report: </strong></span></a><a href="#top">Go To Main Menu</a>

set timing off
set markup html off
spool off
prompt
exit