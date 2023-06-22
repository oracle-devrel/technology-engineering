--# Copyright (c) 2023, Oracle and/or its affiliates.
--# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
--# Purpose: To capture database details for Oracle database 11g onwards 
--# This script is to be executed at the discovery phase before planning for migration/upgrade
--# @author: Ananda Ghosh Dastidar


clear screen;
set echo off;
set feedback off;
set verify off;
set pagesize 10000;
SET linesize 32767;
set serveroutput on size 1000000;

variable gv_multi NUMBER;
variable gv_version NUMBER;
variable gv_dbinfosql REFCURSOR;
variable gv_dbname varchar2(30);
define gv_script_version='3.6';

--Added for centralized discovery
variable gv_pdbconid NUMBER;
col pdbconid new_value v_pdbconid;


--# Validation Block 1: Checking eligible DB version to run this script
PROMPT
DECLARE
v_version number;
BEGIN
EXECUTE IMMEDIATE 'select replace(version,''.'') dbversion from sys.v_$instance' INTO v_version;
IF v_version < 110000 THEN
DBMS_OUTPUT.put_line('PROMPT Error!! This script is intended to execute on oracle database 11g or higher version.');
:gv_version := 1;
END IF;
EXCEPTION WHEN OTHERS THEN
DBMS_OUTPUT.PUT_LINE ('PROMPT Error!! '||SQLCODE ||' : '||SUBSTR(SQLERRM,1,64));
:gv_version := 1;
END;
/
PROMPT
set termout off;
SPOOL version_not_matched.sql
define _editor=vi
DECLARE
	PROCEDURE delsqlfile IS
	v_os_platform varchar2(200);
	BEGIN
	EXECUTE IMMEDIATE 'SELECT lower(PLATFORM_NAME) FROM sys.v_$database' INTO v_os_platform;
	IF(v_os_platform LIKE  '%window%') THEN
	dbms_output.put_line('host del /Q '||'version_not_matched.sql');
	END IF;
	IF( (v_os_platform LIKE  '%solaris%') OR (v_os_platform like  '%linux%') OR (v_os_platform like  '%aix%') ) THEN
	dbms_output.put_line('host rm -rf '||'version_not_matched.sql');
	END IF;
	END;

BEGIN
IF :gv_version = 1 THEN
DBMS_OUTPUT.put_line('PROMPT Error!! This script is intended to execute on oracle database 11g or higher version.');
delsqlfile;
dbms_output.put_line('exit;');
ELSE
delsqlfile;
END IF;
END;
/
SPOOL OFF
@version_not_matched.sql
set termout on;

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
PROMPT
col open_mode for a15
col host_name for a45
col name for a15
PROMPT ****************************************************************************************************************************************
PROMPT |                                               ORACLE DATABASE DISCOVERY UTILITY v&gv_script_version                                                 |
PROMPT |                                                ( For Oracle database 11g onwards )                                                   |
PROMPT ****************************************************************************************************************************************
PROMPT

--Section for dedicated discovery

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
IF :gv_multi = 0 THEN DBMS_OUTPUT.put_line('Press Enter to continue : '); END IF;
IF :gv_multi = 1 THEN DBMS_OUTPUT.put_line('Please select from the list of PDBs given above and enter CON_ID [default 2]: '); END IF;
END;
/
ACCEPT v_pdbconid CHAR FORMAT 'A20' PROMPT '>>>>>>' default 2
PROMPT


--#################################################################
--#################################################################

define gv_project_prefix ='MF_DA';

column here_sql_file_name 	new_value here_sql_file_name;
column here_lst_file_name 	new_value here_lst_file_name;
column here_csv_file_name 	new_value here_csv_file_name;
column here_Script_Version 	new_value here_script_version;

BEGIN
IF :gv_multi = 0 THEN
EXECUTE IMMEDIATE 'select name from v$database' into :gv_dbname;
END IF;

IF :gv_multi = 1 THEN
EXECUTE IMMEDIATE 'select distinct p.name from gv$pdbs p, gv$instance i where i.inst_id=p.inst_id and p.CON_ID='||&v_pdbconid into :gv_dbname;
END IF;
END;
/

--- begin block make SQL, LST file names ----------
set echo off;
set feedback off;
set verify off;
set term off;
select '&gv_project_prefix'||'_'||UPPER(substr(host_name,0,10))||'_'||instance_name||'_'||:gv_dbname||'_'||&v_pdbconid||'_v'|| replace(version,'.')||to_char(sysdate,'_ddmmYYYY') ||'.SQL' here_sql_file_name from sys.v_$instance where rownum<2;
set termout on;
set heading off;
SPOOL &here_sql_file_name;

select 'spool '||'&gv_project_prefix'||'_'|| UPPER(substr(host_name,0,10))||'_'||instance_name||'_'||:gv_dbname||'_'||&v_pdbconid||'_v'|| replace(version,'.') ||to_char(sysdate,'_ddmmYYYY') ||'.LST;' here_lst_file_name from sys.v_$instance where rownum<2;
set heading on;
--- end block make SQL, LST file names ----------

--- end block ------------
SET term on;
SET serveroutput on size 1000000;
SET ECHO OFF;
SET pagesize 10000;
SET linesize 500;
SET trimspool on;
SET serveroutput on;
SET feedback off;
ALTER SESSION SET nls_date_format = 'DD-Mon-YYYY HH24:MI:SS';
SET termout off;

Prompt SET feedback off;;
Prompt SET pagesize 10000;;
Prompt SET serveroutput on size 1000000;;

DECLARE
   gv_version     varchar2(15);
   gv_version_chr varchar2(15);  /* it have processed version */
   gv_version_num number(10);    /* it have processed version */
   gv_slab        varchar2(10);
	PROCEDURE sp_get_slab(v_inp number:=0) IS
	BEGIN
      if ( (110000 < v_inp) and (v_inp < 111071) ) then gv_slab:='11g1'; end if;
      if ( (111071 < v_inp) and (v_inp < 120000) ) then gv_slab:='11g2'; end if;
      if ( (120001 < v_inp) and (v_inp < 130000) ) then gv_slab:='12c';  end if;
      if ( (130001 < v_inp) and (v_inp < 140000) ) then gv_slab:='13';  end if;
	  if ( (179999 < v_inp) and (v_inp < 190000) ) then gv_slab:='18';  end if;
      if ( (189999 < v_inp) and (v_inp < 200000) ) then gv_slab:='19';  end if;
	END;
	PROCEDURE sp_get_version IS
      cursor c1 is select version from sys.v_$instance;
      v_first_number varchar2(4);
	BEGIN
      for i in c1 loop
         gv_version_chr := i.version; gv_version     := i.version; exit;
      end loop;
      v_first_number:=substr(gv_version_chr,1,instr(gv_version_chr,'.',1,1)-1);
      if(length(v_first_number)=1) then
         gv_version_chr := '0'||gv_version_chr;
      end if;
      gv_version_chr := replace(gv_version_chr,'.');
      gv_version_num := gv_version_chr;
	END;
	PROCEDURE sp_process_slab is
	BEGIN
     sp_get_version;
     sp_get_slab(gv_version_num);
   END;
 ------------------------------------------      
	PROCEDURE sp_process_dbinfo is 
	BEGIN
		dbms_output.put_line('SET MARKUP HTML ON;');
		dbms_output.put_line('set linesize 200;');
		dbms_output.put_line('set trimspool on;');
		dbms_output.put_line('set termout on;');
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Information');
		dbms_output.put_line('SELECT (select name from v$database) DB_NAME,(select version from v$instance) DB_VERSION,(select HOST_NAME from v$instance) HOST_NAME,');
		dbms_output.put_line('(select decode(count(*),3,''1/8th OR Quarter RAC'',7,''Half RAC'',14,''Full RAC'',''Non-Exadata'') from (select distinct cell_name from gv$cell_state)) Exadata_Option,');
		dbms_output.put_line('(select Platform_name from v$database) OS_PLATFORM,');
		dbms_output.put_line('(select banner from v$version where banner like ''Oracle%'') EDITION,');
		dbms_output.put_line('(select upper(ENDIAN_FORMAT) ENDIANNESS from v$transportable_platform tp, v$database db where tp.platform_id=db.platform_id) ENDIANNESS,');
		dbms_output.put_line('(select round(((select sum(bytes) from dba_data_files))/1024/1024/1024,4) ||'' GB'' from dual) DB_SIZE from dual;');

	END;
---------------------------
	PROCEDURE sp_process_cdb_dbinfo IS
		v_pdbname varchar2(50);
	BEGIN
		
		EXECUTE IMMEDIATE 'SELECT name from v$pdbs where con_id ='||&v_pdbconid INTO v_pdbname;
		
		dbms_output.put_line('SET MARKUP HTML ON;');
		dbms_output.put_line('set linesize 200;');
		dbms_output.put_line('set trimspool on;');
		dbms_output.put_line('set termout on;');
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Information');		 
		dbms_output.put_line('SELECT (select name from v$database) DB_NAME,(select case when CDB =''YES'' then ''CDB - Multitenant enabled'' else ''Regular 12c Database'' END from v$database) Multitenant_Option,');
		dbms_output.put_line('(select decode(count(*),3,''1/8th OR Quarter RAC'',7,''Half RAC'',14,''Full RAC'',''Non-Exadata'') from (select distinct cell_name from gv$cell_state)) Exadata_Option,');
		dbms_output.put_line('(select version from v$instance) DB_VERSION,(SELECT SYS_CONTEXT(''USERENV'',''HOST'') FROM dual) HOST_NAME,(select Platform_name from v$database) OS_PLATFORM,(select banner from v$version where banner like ''Oracle%'') EDITION,');
		dbms_output.put_line('(select upper(ENDIAN_FORMAT) ENDIANNESS from v$transportable_platform tp, v$database db where tp.platform_id=db.platform_id) ENDIANNESS,');
		dbms_output.put_line('(select round(((select sum(bytes) from dba_data_files) + (select sum(bytes) from dba_temp_files))/1024/1024/1024,2) ||'' GB'' from dual) DB_SIZE from dual;');
		dbms_output.put_line('ALTER SESSION SET CONTAINER = '||v_pdbname||';');
		dbms_output.put_line('SELECT  (select PDB_NAME from DBA_PDBS where PDB_NAME='''||v_pdbname||''') PDB_NAME,(select listagg(name,'', '') within group (order by name) from v$services where PDB='''||v_pdbname||''') Service_Name,(select version from v$instance) DB_VERSION,');
		dbms_output.put_line('(SELECT SYS_CONTEXT(''USERENV'',''HOST'') FROM dual) HOST_NAME,(select Platform_name from v$database) OS_PLATFORM, (select banner from v$version where banner like ''Oracle%'') EDITION,(select open_mode from v$pdbs where name='''||v_pdbname||''') Open_Mode,');
		dbms_output.put_line('(select open_time from v$pdbs where name='''||v_pdbname||''') Open_time, (select round(((select sum(bytes) from dba_data_files) + (select sum(bytes) from dba_temp_files))/1024/1024/1024,2) ||'' GB'' from dual) DB_SIZE from dual;');
		--dbms_output.put_line('ALTER SESSION SET CONTAINER = cdb$root;');
	
	END;
BEGIN
	sp_process_slab; /* this will bring defined slab value */
	IF :gv_multi = 0 THEN
	IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) then
		sp_process_dbinfo;  /* call non-CDB DB info procedure */
	END IF;
	END IF;

	IF :gv_multi = 1 THEN
	IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) then
		sp_process_cdb_dbinfo;  /* call CDB DB info procedure */
	END IF;
	END IF;
	DECLARE
		v_sub_str varchar2(300);
	BEGIN
		dbms_output.put_line('PROMPT Heading U_I_GG DB:Reporting Date');
		v_sub_str:= 'select '||''''||'DATE_AND_TIME='||''''||'||'||'to_char(sysdate,'||''''||'DD-Mon-YYYY HH24:MI:SS';
		v_sub_str:= v_sub_str||''''||') date_N_time from dual;';
		dbms_output.put_line(v_sub_str);
	END;
	dbms_output.put_line('SET TERMOUT OFF;');
	dbms_output.put_line('CLEAR COLUMNS;');
END;
/

DECLARE
   --Heading Additional
   gv_recycle_bin_count varchar2(40);
   gv_version     varchar2(15);
   gv_version_chr varchar2(15);  /* it have processed version */
   gv_version_num number(10);    /* it have processed version */
   gv_slab        varchar2(10);
   procedure sp_get_slab(v_inp number:=0) is
   begin
      if ( (110000 < v_inp) and (v_inp < 111071) ) then gv_slab:='11g1'; end if;
      if ( (111071 < v_inp) and (v_inp < 120000) ) then gv_slab:='11g2'; end if;
      if ( (120001 < v_inp) and (v_inp < 130000) ) then gv_slab:='12c';  end if;
      if ( (130001 < v_inp) and (v_inp < 140000) ) then gv_slab:='13';  end if;
	  if ( (179999 < v_inp) and (v_inp < 190000) ) then gv_slab:='18';  end if;
      if ( (189999 < v_inp) and (v_inp < 200000) ) then gv_slab:='19';  end if;
   end;
   procedure sp_get_version is
      cursor c1 is select version from sys.v_$instance;
      v_first_number varchar2(4);
   begin
      for i in c1 loop
         gv_version_chr := i.version; gv_version     := i.version; exit;
      end loop;
      v_first_number:=substr(gv_version_chr,1,instr(gv_version_chr,'.',1,1)-1);
      if(length(v_first_number)=1) then
         gv_version_chr := '0'||gv_version_chr;
      end if;
      gv_version_chr := replace(gv_version_chr,'.');
      gv_version_num := gv_version_chr;
   end;
   procedure sp_process_slab is
   begin
     sp_get_version;
     sp_get_slab(gv_version_num);
   end;
 ------------------------------------------     
      
		PROCEDURE sp_process_dbinfo IS
     ------ Please change the following value as desired -------------------
      v_input_table_name varchar2(30):='block_01';
      V_identitity       varchar2(50):='PROMPT REM block_No_0002.sql Version V_1.0'; /* Change only versoin */
      v_to_debug         varchar2(3):='no';      /* 'yes' or 'no' only valid values */
      -----------------------------------------------------------------------
      ----------------------
      TYPE tab_col_des_dec IS RECORD (tab varchar2(30) :='' ,col varchar2(30) :=''
           ,des varchar2(30):='', choose varchar2(30):='ok',in_where varchar2(4000):='',out_value varchar2(1000) );
      TYPE tab_col_des_type IS TABLE OF tab_col_des_dec INDEX BY BINARY_INTEGER;
      tab_col_des tab_col_des_type;
      ----------------------
      v_number         number(20):=0;
      v_bytes          number(20);
      yes_no           varchar2(1);
      v_here_file_name varchar2(100);
      v_sub_str        varchar2(4000);
      v_os_bit_info    varchar2(100);
      v_endian         varchar2(100);
      cursor c1 (cv_table_name varchar2,cv_column_name varchar2) is
         select a.owner||'.'|| a.table_name table_name, a.column_name from all_tab_columns a
            where a.column_name = upper(cv_column_name) and a.table_name in (
                  select table_name from all_synonyms    where synonym_name = UPPER(cv_table_name)
                  union
                  select table_name from all_tab_columns where table_name   = UPPER(cv_table_name)
            ) and rownum<2;
		PROCEDURE sp_debug_out_values IS
		BEGIN
         for ii in tab_col_des.FIRST .. tab_col_des.LAST loop
            dbms_output.put_line(ii|| ' '||tab_col_des(ii).des ||' '|| tab_col_des(ii).out_value ||'('||nvl(tab_col_des(ii).choose,'OK')||')');
         end loop;
		END;
		PROCEDURE SP_STRIP_80_LENGH(v_str varchar2) is
         v_length   number :=70;
         v_sub_str  varchar2(1000);
         v_sub_str1 varchar2(4000);
         v_sub_str2 varchar2(4000);
         v_number number;
		BEGIN
         v_number   := instr(v_str,',',v_length,1)-1;
         v_sub_str1 := substr(v_str,1,v_number);
         v_sub_str2 := substr(v_str,(v_number+1));
         dbms_output.put_line(v_sub_str1);
         if ( length(v_sub_str2) >v_length) then
            SP_STRIP_80_LENGH(v_sub_str2);
         else
            dbms_output.put_line(v_sub_str2);  /* remvoe comment here */
            return;
         end if;
   
         null;
		END;
		PROCEDURE sp_generate_sql IS
         v_sub_str varchar2(4000);
         v_des_str varchar2(4000);
   
         v_create_tbl varchar2(4000);
         v_val_str varchar2(5000);
         v_col_format_str varchar2(4000);
         v_number integer;
		BEGIN
   ----
         for ii in 0 .. tab_col_des.LAST LOOP
            v_col_format_str :='';
            if (lower(nvl(tab_col_des(ii).choose,'ok')) not like '%delete%') then
               begin
                  -- column xx fromat a??; doing here ---
                  v_number := greatest( length(nvl(tab_col_des(ii).out_value,'5')), length(nvl(tab_col_des(ii).des,'5') )) ;
                  if( v_number <> length(nvl(tab_col_des(ii).out_value,'5')) ) then
                     v_col_format_str := 'COLUMN '||tab_col_des(ii).des||' FORMAT A' ||trim(to_char(v_number))||';';
                  end if;
               exception when others then
                     begin
                        dbms_output.put_line('EXCEPTION in sp_generate_sql for'||v_col_format_str);
                     end;
               end;
            end if;
            dbms_output.put_line(v_col_format_str);
         end loop;
   ----
         dbms_output.put_line('SET MARKUP HTML ON;');
         dbms_output.put_line('set linesize 200;');
         dbms_output.put_line('set trimspool on;');
         dbms_output.put_line('set termout on;');
         dbms_output.put_line('Prompt Heading U_I_GG DB:Additional');
         dbms_output.put_line('SELECT ''oracle'' DB');   
         for ii in 0 .. tab_col_des.LAST LOOP
            if (lower(nvl(tab_col_des(ii).choose,'ok')) not like '%delete%') then
               begin
                  v_sub_str :=' '||''''||trim(nvl(tab_col_des(ii).out_value,''))||''''||' '||tab_col_des(ii).des||' ';
               --if( ii = 0 ) then
                  --v_sub_str := 'SELECT '||v_sub_str;
               --els
               if( ii = tab_col_des.LAST ) then
                  v_sub_str := '  ,'||v_sub_str ||' from dual;';
               else
                    v_sub_str := ' ,'||v_sub_str;
               end if;
               exception when others then
                     begin
                        dbms_output.put_line('EXCEPTION in sp_generate_sql for'||v_sub_str);
                     end;
               end;
               dbms_output.put_line(v_sub_str);
            end if;
         end loop;
      END;
      PROCEDURE sp_fill_out_values IS
         v_str        varchar2(1000);
         v_sub_str    varchar2(1000);
         v_column_name varchar2(60);
      BEGIN
         for ii in 0 .. tab_col_des.LAST LOOP
            v_str := 'SELECT '||tab_col_des(ii).col ||' from ' || tab_col_des(ii).tab ||' '||tab_col_des(ii).in_where  ;
            v_column_name:= upper(tab_col_des(ii).col);
            v_column_name:= replace( v_column_name,',0)',null);
            v_column_name:= replace( v_column_name,'TO_CHAR(',null);
            v_column_name:= replace( v_column_name,'SUM(',null);
            v_column_name:= replace( v_column_name,'NVL(',null);
            v_column_name:= replace( v_column_name,'COUNT(',null);
            v_column_name:= replace( v_column_name,'))',null);
            v_column_name:= replace( v_column_name,'))',null);
            v_column_name:= replace( v_column_name,')',null);
            v_column_name:= replace( v_column_name,')',null);
            v_column_name:= replace( v_column_name,')',null);
            yes_no:='n';
---         dbms_output.put_line('REM -->table:'||tab_col_des(ii).tab||' column:'||v_column_name);
            for i in c1(tab_col_des(ii).tab,v_column_name) LOOP
               tab_col_des(ii).tab := i.table_name;   --this table have schema name with in   newly added
               v_str := 'SELECT '||tab_col_des(ii).col ||' from ' || tab_col_des(ii).tab ||' '||tab_col_des(ii).in_where  ; -- newly added
               v_sub_str:=tab_col_des(ii).out_value;
               yes_no:='y'; 
               begin
                  EXECUTE IMMEDIATE v_str into v_sub_str;
                  if v_sub_str is null then             
                     tab_col_des(ii).out_value := null;
                  else
                     tab_col_des(ii).out_value := v_sub_str;
                  end if;
               exception when others then null;
               end;
            end loop;
            --- debug line below --
            if( (yes_no='n') ) then
               if ( tab_col_des(ii).out_value is null ) then   /* if default value is there then keept it */
                  tab_col_des(ii).choose :='deleted';
               end if;
               dbms_output.put_line('REM '||ii||' '||v_str||' skipped ');
            else
               tab_col_des(ii).out_value := v_sub_str;
            end if;
         end loop;
      END;
      PROCEDURE sp_delete_dups IS
         prev_des varchar2(30):='kri';
      BEGIN
         for ii in tab_col_des.FIRST .. tab_col_des.LAST loop
            if ( ( prev_des = tab_col_des(ii).des ) and nvl(tab_col_des(ii).choose,'kri') <>'deleted') then
                --dbms_output.put_line(prev_des);
                if ( tab_col_des(ii-1).out_value is null) then
                   tab_col_des(ii-1).choose :='deleted';
                   tab_col_des(ii).choose :='';
                else
                   tab_col_des(ii).choose :='deleted';
                   tab_col_des(ii-1).choose :='';
                end if;
             else
                prev_des := tab_col_des(ii).des;
             end if;
             prev_des := tab_col_des(ii).des;
         end loop;
      END;
----
      FUNCTION sf_bytes_des ( i_number number := NULL) RETURN varchar2 IS
         v_number  number;
         v_sub_str varchar2(100);
      BEGIN
         v_number := i_number;
         if(v_number > 1024 ) then
            v_number:=v_number/(1024);             --kilo
            if(v_number >1024) then
               v_number:=v_number/(1024);          --mega
               if (v_number > 1024) then
                  v_number:=v_number/(1024);       --giga
                  if (v_number > 1024) then
                     v_number:=v_number/(1024);    --Terra
                     if (v_number > 1024) then
                        v_number:=v_number/(1024); --Peta
                        v_sub_str:=to_char(v_number,'99999999.9999')||' PB';                                                                 
                     else 
                        v_sub_str:=to_char(v_number,'99999.9999')||' TB';
                     end if;
                  else
                     v_sub_str:=to_char(v_number,'99999.9999')||' GB';
                  end if;
               else
                  v_sub_str:=to_char(v_number,'99999.9999')||' MB';
               end if;
            else
               v_sub_str:= rtrim(to_char(v_number,'99999.9999'),'0') ||' KB';
            end if;
         else
            v_sub_str:=to_char(v_number,'99999.9999')||' Bytes';
         end if;
         RETURN trim(v_sub_str);
      END;
----
   begin
   -------general block starts -------
   ---        dbms_output.put_line(V_identitity);
--      select value into v_bytes from sys.v_$parameter where name='db_block_size';
   --0
      tab_col_des(0).tab                     :='V_$PARAMETER';
      tab_col_des(tab_col_des.LAST).col      :='VALUE' ;
      tab_col_des(tab_col_des.LAST).des      :='DB_BLOCK_SIZE';
      tab_col_des(tab_col_des.LAST).in_where :=' where name='||''''||'db_block_size'||'''';

   --1
      tab_col_des(tab_col_des.LAST+1).tab   := 'V_$PROCESS';
      tab_col_des(tab_col_des.LAST).col     :='addr' ;
      tab_col_des(tab_col_des.LAST).des     :='DB_WORD_SIZE';
      tab_col_des(tab_col_des.LAST).in_where :=' where rownum < 2';

   --2
      tab_col_des(tab_col_des.LAST+1).tab   :='V_$DATABASE';
      tab_col_des(tab_col_des.LAST).col     :='LOG_MODE';
      tab_col_des(tab_col_des.LAST).des     :='LOG_MODE';

   --3
      tab_col_des(tab_col_des.LAST+1).tab   :='DBA_SEGMENTS';
      tab_col_des(tab_col_des.LAST).col     :='bytes' ;
      tab_col_des(tab_col_des.LAST).des     :='DB_SETMENT_SIZE';

   --4
      tab_col_des(tab_col_des.LAST+1).tab   :='V_$TIMEZONE_FILE';
      tab_col_des(tab_col_des.LAST).col     :='VERSION';
      tab_col_des(tab_col_des.LAST).des     :='TIME_ZONE';
      tab_col_des(tab_col_des.LAST).out_value :='_NA_';

   --5
      tab_col_des(tab_col_des.LAST+1).tab   :='DBA_RECYCLEBIN';
      tab_col_des(tab_col_des.LAST).col   :='TO_CHAR(COUNT(NVL(OWNER,0)))';
      tab_col_des(tab_col_des.LAST).des   :='RECYCLE_BIN_COUNT';
   --6
      tab_col_des(tab_col_des.LAST+1).tab   :='V_$DATABASE';
      tab_col_des(tab_col_des.LAST).col     :='FLASHBACK_ON';
      tab_col_des(tab_col_des.LAST).des     :='FLASHBACK';
      tab_col_des(tab_col_des.LAST).out_value :='_NA_';

   --7
      tab_col_des(tab_col_des.LAST+1).tab   :='V_$PARAMETER';
      tab_col_des(tab_col_des.LAST).col     :='VALUE';
      tab_col_des(tab_col_des.LAST).des     :='RECYCLE_BIN';
      tab_col_des(tab_col_des.LAST).in_where :=' where lower(name) like '||''''||'%recyclebin%'||'''';
      tab_col_des(tab_col_des.LAST).out_value :='_NA_';

      begin
         sp_fill_out_values;
         sp_delete_dups ;
         sp_delete_dups ;

         for i in 0 .. tab_col_des.LAST LOOP
            if ( tab_col_des(i).des  = 'DB_BLOCK_SIZE') then
               tab_col_des(i).out_value := sf_bytes_des(tab_col_des(i).out_value);
            end if;
            if ( tab_col_des(i).des  = 'RECYCLE_BIN_COUNT') then
               gv_recycle_bin_count := tab_col_des(i).out_value;
               tab_col_des(i).choose :='deleted';
            end if;
            if ( tab_col_des(i).des  = 'RECYCLE_BIN') then
               if(lower(trim(tab_col_des(i).out_value)) like '%on%') then
                  tab_col_des(i).out_value := tab_col_des(i).out_value || ' / in_bin:' || gv_recycle_bin_count ;
               end if;
            end if;
            if ( tab_col_des(i).des like '%DB_WORD_SIZE') then
               tab_col_des(i).out_value     := 'This is '|| length(tab_col_des(i).out_value)*4||' -bit database' ;
            end if;
            if ( tab_col_des(i).des like '%DB_SETMENT_SIZE') then
               tab_col_des(i).out_value     := sf_bytes_des(tab_col_des(i).out_value);
            end if;
            if ( tab_col_des(i).out_value like '%TNS for%' ) then
               tab_col_des(i).out_value :=replace(tab_col_des(i).out_value,'TNS for');
               tab_col_des(i).out_value := substr(tab_col_des(i).out_value,1,(instr(tab_col_des(i).out_value,':')-1) );
            end if;
         end loop;
      end;
      v_bytes:=0;
      for cv_bytes in ( select sum(bytes) bytes from sys.v_$datafile ) loop
         v_bytes := cv_bytes.bytes;
      end loop;

   --9
   v_endian := 'Error';
	for cv_endian in (select endianness from ( select upper(ENDIAN_FORMAT) ENDIANNESS from v$transportable_platform tp, v$database db where tp.platform_id=db.platform_id and rownum <2 )) 
	loop
	v_endian := cv_endian.endianness;
	end loop;
 
      if(upper(v_to_debug) like 'Y%') then
         sp_debug_out_values;
      end if;
      sp_generate_sql;
      dbms_output.put_line('CLEAR COLUMNS;');
end;
---------------------------      
	PROCEDURE sp_process_cdb_dbinfo IS
		v_pdbname varchar2(50);
	BEGIN
-------------------------------------------------------
--Prompt Heading U_I_GG DB:Additional Database Details|
-------------------------------------------------------	
		--dbms_output.put_line('ALTER SESSION SET CONTAINER = cdb$root;');
		dbms_output.put_line('SET MARKUP HTML ON;');
		dbms_output.put_line('set linesize 200;');
		dbms_output.put_line('set trimspool on;');
		dbms_output.put_line('set termout on;');
		dbms_output.put_line('Prompt Heading U_I_GG DB:Additional Database Details');
		dbms_output.put_line('SELECT a.DBID,NAME DBNAME,a.CREATED,to_char(b.startup_time, ''DD-MON-YY HH24:MI'') "Startup time",b.LOGINS,a.LOG_MODE,a.OPEN_MODE,a.REMOTE_ARCHIVE,a.DATABASE_ROLE,a.PLATFORM_ID,a.PLATFORM_NAME,a.DB_UNIQUE_NAME from sys.v_$database a,sys.v_$instance b;');
		dbms_output.put_line('SELECT a.DBID,a.name PDB_NAME,a.open_time "Startup time",a.open_mode Status,b.property_value CHARACTERSET,recovery_status,restricted,a.snapshot_parent_con_id Parent_Container_Id,a.con_id from v$pdbs a join CDB_PROPERTIES b on a.con_id=b.con_id where a.con_id='||&v_pdbconid||' and b.property_name = ''NLS_CHARACTERSET'' ;');
		dbms_output.put_line('SET TERMOUT OFF;');
	END;

BEGIN
IF :gv_multi = 0 THEN
   sp_process_slab; /* this will bring defined slab value */
   if ( gv_slab in ('11g1','11g2','12c','18','19') ) then
      sp_process_dbinfo;
   end if;
END IF;

IF :gv_multi = 1 THEN
	sp_process_cdb_dbinfo;
END IF;

END;
/

set serveroutput on size 1000000;
SET linesize 32767;
set pagesize 0;
SET TRIMSPOOL ON;
set termout off;
set feedback off;
DECLARE
   gv_version     varchar2(15);
   gv_version_chr varchar2(15);  /* it have processed version */
   gv_version_num number(10);    /* it have processed version */
   gv_slab        varchar2(10);
   owner_blacklist varchar2(4000);
   procedure sp_get_slab(v_inp number:=0) is
   begin
      if ( (110000 < v_inp) and (v_inp < 111071) ) then gv_slab:='11g1'; end if;
      if ( (111071 < v_inp) and (v_inp < 120000) ) then gv_slab:='11g2'; end if;
      if ( (120001 < v_inp) and (v_inp < 130000) ) then gv_slab:='12c';  end if;
      if ( (130001 < v_inp) and (v_inp < 140000) ) then gv_slab:='13';  end if;
	  if ( (179999 < v_inp) and (v_inp < 190000) ) then gv_slab:='18';  end if;
      if ( (189999 < v_inp) and (v_inp < 200000) ) then gv_slab:='19';  end if;
   end;
   procedure sp_get_version is
      cursor c1 is select version from sys.v_$instance;
      v_first_number varchar2(4);
   begin
      for i in c1 loop
         gv_version_chr := i.version; gv_version     := i.version; exit;
      end loop;
      v_first_number:=substr(gv_version_chr,1,instr(gv_version_chr,'.',1,1)-1);
      if(length(v_first_number)=1) then
         gv_version_chr := '0'||gv_version_chr;
      end if;
      gv_version_chr := replace(gv_version_chr,'.');
      gv_version_num := gv_version_chr;
   end;
   procedure sp_process_slab is
   begin
     sp_get_version;
     sp_get_slab(gv_version_num);
   end;
BEGIN
   sp_process_slab; /* this will bring defined slab value */
   owner_blacklist:='(''ANONYMOUS'',''CTXSYS'',''DBSNMP'',''EXFSYS'',''LBACSYS'',''MDSYS'',''MGMT_VIEW'',''OLAPSYS'',''ORDDATA'',''OWBSYS'',''ORDPLUGINS'',''ORDSYS'',''OUTLN'',''SI_INFORMTN_SCHEMA'',''SYS'',''SYSTEM'',''SYSMAN'',''SYSMAN_OPSS'',''SYSMAN_APM'',''SYSMAN_RO'',''MGMT_VIEW'',''WK_TEST'',''WKSYS'',''WKPROXY'',''WMSYS'',''XDB'',''PERFSTAT'',''TRACESVR'',''TSMSYS'',''DSSYS'',''DMSYS'',''SYSMAN_MDS'',''DIP'',''CSMIG'',''AWR_STAGE'',''AURORA$ORB$UNAUTHENTICATED'',''SCOTT'',''HR'',''SH'',''OE'',''PM'',''IX'',''BI'',''XS$NULL'',''ORACLE_OCM'',''SPATIAL_CSW_ADMIN_USR'',''SPATIAL_WFS_ADMIN_USR'',''MDDATA'',''FLOWS_FILES'',''FLOWS_30000'',''APEX_030200'',''APEX_PUBLIC_USER'',''APPQOSSYS'',''DBATOOLS_ADMIN'',''SQLTXPLAIN'',''PUBLIC'',''OPS$ORACLE'',''OWBSYS_AUDIT'',''DBSFWUSER'',''GGSYS'',''DVSYS'',''DVF'',''GSMADMIN_INTERNAL'',''GSMCATUSER'',''SYSBACKUP'',''REMOTE_SCHEDULER_AGENT'',''PDBADMIN'',''GSMUSER'',''SYSRAC'',''OJVMSYS'',''PDBUSER'',''AUDSYS'',''SYS$UMF'',''APEX_LISTENER'',''ORDS_METADATA'',''APEX_200200'')';

IF :gv_multi = 0 THEN
   dbms_output.put_line('SET MARKUP HTML ON;'); dbms_output.put_line('set termout on;');

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Additional Database Details');
      dbms_output.put_line('select a.DBID,NAME,a.CREATED,to_char(b.startup_time, '||''''||'DD-MON-YY HH24:MI'||''''||') "Startup time",b.LOGINS,a.LOG_MODE,a.OPEN_MODE,a.REMOTE_ARCHIVE,a.DATABASE_ROLE,a.PLATFORM_ID,a.PLATFORM_NAME,');
      dbms_output.put_line('a.DB_UNIQUE_NAME from sys.v_$database a,sys.v_$instance b;');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Supplemental Logging ');
      dbms_output.put_line('Prompt Footnote Supplemental Logging Information ');
      dbms_output.put_line('select name, log_mode "LogMode", ');
      dbms_output.put_line('supplemental_log_data_min "SupLog: Min", supplemental_log_data_pk "PK",');
      dbms_output.put_line('supplemental_log_data_ui "UI", force_logging "Forced",');
      dbms_output.put_line('supplemental_log_data_fk "FK", supplemental_log_data_all "All",');
      dbms_output.put_line('to_char(created, '||''''||'MM-DD-YYYY HH24:MI:SS'||''''||') "Created"');
      dbms_output.put_line('from sys.v_$database;');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Compressed Objects');
      dbms_output.put_line('Prompt Footnote Objects stored in Tablespaces with Compression are not supported in the current release of OGG');
      dbms_output.put_line('select');
      dbms_output.put_line('	TABLESPACE_NAME,');
      dbms_output.put_line('	DEF_TAB_COMPRESSION ');
      dbms_output.put_line('from DBA_TABLESPACES ');
      dbms_output.put_line('where ');
      dbms_output.put_line('DEF_TAB_COMPRESSION <> '||''''||'DISABLED'||''''||';');
   END IF; 
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Standby availibility');
      dbms_output.put_line('select * from (');
      dbms_output.put_line('select name standby_parameter_name,value from sys.v_$parameter where');
      dbms_output.put_line('(name like '||''''||'log_archive_dest_%'||''''||' or name in ('||''''||'fal_server'||''''||','||''''||'db_file_name_convert'||''''||','||''''||'log_file_name_convert'||''''||'))');
      dbms_output.put_line('and name not like '||''''||'%state%'||''''||' and value is not null');
      dbms_output.put_line('union');
      dbms_output.put_line('select '||''''||'SWITCHOVER_STATUS'||''''||' standby_parameter_name, SWITCHOVER_STATUS value from sys.v_$database);');
   END IF;   
 
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Schema Wise Object Count from dba_objects');
      dbms_output.put_line('select owner,object_type, count(1) object_count from sys.dba_objects');
      dbms_output.put_line(' where owner not in '||owner_blacklist);
      dbms_output.put_line('group by owner,object_type');
      dbms_output.put_line('order by owner,object_type;');
   END IF; 
 
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Distinct Column Data Type ');
      dbms_output.put_line('Prompt Footnote Distinct Column Data Types and their Count in the Schema:'||''''||' ');
      dbms_output.put_line('SELECT data_type, count(*) total');
      dbms_output.put_line('FROM all_tab_columns');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist); 
      dbms_output.put_line('GROUP BY data_type;');
   END IF; 
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables having more than 32 Columns ');
      dbms_output.put_line('Prompt Footnote Tables that will Fail Add Trandata (Only an issue for Oracle versions below Oracle 10G) in the Database');
      dbms_output.put_line('SELECT distinct(table_name)');
      dbms_output.put_line('FROM dba_tab_columns');
      dbms_output.put_line('WHERE owner not in '||owner_blacklist); 
      dbms_output.put_line('AND column_id > 32;');

   END IF;  
 
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables Without Primary or Unique Key');
      dbms_output.put_line('Prompt Footnote Tables With No Primary Key or Unique Index by Schema:');
      dbms_output.put_line('SELECT owner, table_name');
      dbms_output.put_line('  FROM dba_tables');
      dbms_output.put_line(' WHERE owner not in '||owner_blacklist); 
      dbms_output.put_line('MINUS');
	  dbms_output.put_line('(');
      dbms_output.put_line('SELECT distinct(owner), idx.table_name');
      dbms_output.put_line('  FROM dba_indexes idx');
      dbms_output.put_line(' WHERE idx.owner not in '||owner_blacklist); 
      dbms_output.put_line('   AND idx.uniqueness = '||''''||'UNIQUE'||''''||');');
   END IF; 
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Nologging setting');
      dbms_output.put_line('Prompt Footnote This may cause problems with missing data down stream.');
      dbms_output.put_line('');
      dbms_output.put_line('select owner, table_name, '||''''||' '||''''||', logging from DBA_TABLES');
      dbms_output.put_line('where logging <> '||''''||'YES'||''''||'');
      dbms_output.put_line('and owner not in '||owner_blacklist); 
	  dbms_output.put_line('UNION');
      dbms_output.put_line('select owner, table_name, partitioning_type, DEF_LOGGING "LOGGING" from DBA_part_tables');
      dbms_output.put_line('where DEF_LOGGING != '||''''||'YES'||''''||' ');
      dbms_output.put_line('and owner not in '||owner_blacklist); 
	  dbms_output.put_line('UNION');
      dbms_output.put_line('select table_owner, table_name, PARTITION_NAME, logging from DBA_TAB_PARTITIONS');
      dbms_output.put_line('where logging <> '||''''||'YES'||''''||' ');
      dbms_output.put_line('and table_owner not in '||owner_blacklist); 
	  dbms_output.put_line('UNION');
      dbms_output.put_line('select table_owner, table_name, PARTITION_NAME, logging from DBA_TAB_SUBPARTITIONS');
      dbms_output.put_line('where logging <> '||''''||'YES'||''''||' ');
      dbms_output.put_line('and table_owner not in '||owner_blacklist); 
	  dbms_output.put_line(';');
   END IF;  
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Deferred Indexes');
      dbms_output.put_line('Prompt Footnote Tables with Deferred constraints. Deferred constraints may cause TRANDATA to chose an incorrect Key');
      dbms_output.put_line('Prompt Footnote Tables with Deferred constraints should be added using KEYCOLS in the trandata statement.');
      dbms_output.put_line('SELECT c.TABLE_NAME,');
      dbms_output.put_line('  c.CONSTRAINT_NAME,');
      dbms_output.put_line('  c.CONSTRAINT_TYPE,');
      dbms_output.put_line('  c.DEFERRABLE,');
      dbms_output.put_line('  c.DEFERRED,');
      dbms_output.put_line('  c.VALIDATED,');
      dbms_output.put_line('  c.STATUS,');
      dbms_output.put_line('  i.INDEX_TYPE,');
      dbms_output.put_line('  c.INDEX_NAME,');
      dbms_output.put_line('  c.INDEX_OWNER');
--    dbms_output.put_line('  c.OWNER');
      dbms_output.put_line('FROM dba_constraints c,');
      dbms_output.put_line('  dba_indexes i');
      dbms_output.put_line('WHERE');
      dbms_output.put_line('    i.TABLE_NAME   = c.TABLE_NAME');
      dbms_output.put_line('AND i.OWNER        = c.OWNER');
      dbms_output.put_line('AND  c.DEFERRED = '||''''||'DEFERRED'||''''||'');
      dbms_output.put_line('And i.owner not in '||owner_blacklist); 
	  dbms_output.put_line(';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Big RowSize Tables');
      dbms_output.put_line('Prompt Footnote Tables Defined with Rowsize greater than 2MB in all Schemas');
      dbms_output.put_line('SELECT table_name, sum(data_length) row_length_over_2MB');
      dbms_output.put_line('FROM all_tab_columns');
      dbms_output.put_line('WHERE owner not in '||owner_blacklist); 
	  dbms_output.put_line('GROUP BY table_name');
      dbms_output.put_line('HAVING sum(data_length) > 2000000;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables without PK or UK Column more than 1MB  ');
      dbms_output.put_line('Prompt Footnote Tables With No Primary Key or Unique Index and Column Lenght more than 1M');
      dbms_output.put_line('SELECT owner, table_name');
      dbms_output.put_line('  FROM all_tab_columns');
      dbms_output.put_line(' WHERE owner not in '||owner_blacklist); 
	  dbms_output.put_line(' group by owner, table_name');
      dbms_output.put_line(' HAVING sum(data_length) > 1000000');
      dbms_output.put_line('MINUS');
	  dbms_output.put_line('(');
      dbms_output.put_line('SELECT idx.owner, idx.table_name');
      dbms_output.put_line('  FROM all_indexes idx');
      dbms_output.put_line(' WHERE idx.owner not in '||owner_blacklist); 
	  dbms_output.put_line('   AND idx.uniqueness = '||''''||'UNIQUE'||''''||');');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Special Datatypes Columns');
      dbms_output.put_line('Prompt Footnote Tables With CLOB, BLOB, LONG, NCLOB or LONG RAW Columns in ALL Schemas');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE');
      dbms_output.put_line('FROM all_tab_columns');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist); 
	  dbms_output.put_line('AND data_type in ('||''''||'CLOB'||''''||', '||''''||'BLOB'||''''||', '||''''||'LONG'||''''||', '||''''||'LONG RAW'||''''||', '||''''||'NCLOB'||''''||');');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:ROWID Datatypes');
      dbms_output.put_line('Prompt Footnote Tables With ROWID Data_Type');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE');
      dbms_output.put_line('FROM all_tab_columns WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('AND data_type='||''''||'ROWID'||''''||';');
 END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Unsupported Datatypes');
      dbms_output.put_line('Prompt Footnote Tables With Columns of UNSUPPORTED Datatypes in ALL Schemas');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE');
      dbms_output.put_line('FROM all_tab_columns');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('AND (data_type in ('||''''||'ORDDICOM'||''''||', '||''''||'BFILE'||''''||', '||''''||'TIMEZONE_REGION'||''''||', '||''''||'BINARY_INTEGER'||''''||', '||''''||'PLS_INTEGER'||''''||', '||''''||'UROWID'||''''||', '||''''||'URITYPE'||''''||', '||''''||'MLSLABEL'||''''||', '||''''||'TIMEZONE_ABBR'||''''||', '||''''||'ANYDATA'||''''||', '||''''||'ANYDATASET'||''''||', '||''''||'ANYTYPE'||''''||')');
      dbms_output.put_line('or data_type like '||''''||'INTERVAL%'||''''||');');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:All Unsupported');
      dbms_output.put_line('Prompt Footnote Cluster, or Object Tables - ALL UNSUPPORTED - in ALL Schemas');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, CLUSTER_NAME, TABLE_TYPE ');
      dbms_output.put_line('FROM all_all_tables');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('AND (cluster_name is NOT NULL or TABLE_TYPE is NOT NULL);');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Compressed Tables and Table Partitions');
      dbms_output.put_line('Prompt Footnote All tables that have compression enabled (which we do not currently support):');
      dbms_output.put_line('select owner TABLE_OWNER, table_name, COMPRESSION');
      dbms_output.put_line('from DBA_TABLES');
      dbms_output.put_line('where COMPRESSION = '||''''||'ENABLED'||''''||'');
      dbms_output.put_line('UNION ');
      dbms_output.put_line('SELECT TABLE_OWNER, TABLE_NAME, COMPRESSION');
      dbms_output.put_line(' FROM ALL_TAB_PARTITIONS ');
      dbms_output.put_line('WHERE COMPRESSION = '||''''||'ENABLED'||''''||';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:IOT Tables ');
      dbms_output.put_line('Prompt Footnote IOT_TYPE may have values IOT,IOT_OVERFLOW,IOT_MAPPING or NULL');
      dbms_output.put_line('Prompt Footnote IOT (Fully support for Oracle 10GR2 (with or without overflows) using GGS 10.4 and higher) - in All Schemas:');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, IOT_TYPE, TABLE_TYPE ');
      dbms_output.put_line('FROM all_all_tables');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('AND (IOT_TYPE is not null or TABLE_TYPE is NOT NULL);');
   END IF;

   IF ( gv_slab in ('8i','9i','10g','11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Domain Indexes');
      dbms_output.put_line('Prompt Footnote Tables with Domain or Context Indexes'||''''||' ');
      dbms_output.put_line('SELECT OWNER, TABLE_NAME, index_name, index_type ');
      dbms_output.put_line('FROM dba_indexes ');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('and index_type = '||''''||'DOMAIN'||''''||';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Constraints and Tables');
      dbms_output.put_line('Prompt Footnote Types of Constraints on the Tables in ALL Schemas');
      dbms_output.put_line('SELECT DECODE(constraint_type,'||''''||'P'||''''||','||''''||'PRIMARY KEY'||''''||','||''''||'U'||''''||','||''''||'UNIQUE'||''''||', '||''''||'C'||''''||', '||''''||'CHECK'||''''||', '||''''||'R'||''''||', ');
      dbms_output.put_line(''||''''||'REFERENTIAL'||''''||','||''''||'Other Constraints'||''''||') constraint_type_desc, count(*) total');
      dbms_output.put_line('FROM all_constraints');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('GROUP BY constraint_type;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Cascading Deletes');
      dbms_output.put_line('Prompt Footnote Cascading Deletes on the Tables in ALL Schemas');
      dbms_output.put_line('SELECT owner, table_name, constraint_name');
      dbms_output.put_line('FROM all_constraints');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('	and constraint_type = '||''''||'R'||''''||' and delete_rule = '||''''||'CASCADE'||''''||';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Triggers');
      dbms_output.put_line('Prompt Footnote Tables Defined with Triggers in ALL Schema:');
      dbms_output.put_line('SELECT owner, table_name, COUNT(*) trigger_count');
      dbms_output.put_line('FROM all_triggers');
      dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('GROUP BY owner, table_name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Reverse Key Indexes');
      dbms_output.put_line('Prompt Footnote Performance issues - Reverse Key Indexes Defined in ALL Schema:');
      dbms_output.put_line('select ');
      dbms_output.put_line('	OWNER,      ');
      dbms_output.put_line('	INDEX_NAME,');
      dbms_output.put_line('	INDEX_TYPE, ');
      dbms_output.put_line('	TABLE_OWNER,');
      dbms_output.put_line('	TABLE_NAME, ');
      dbms_output.put_line('	TABLE_TYPE, ');
      dbms_output.put_line('	UNIQUENESS,');
      dbms_output.put_line('	CLUSTERING_FACTOR,');
      dbms_output.put_line('	NUM_ROWS,');
      dbms_output.put_line('	LAST_ANALYZED,');
      dbms_output.put_line('	BUFFER_POOL');
      dbms_output.put_line('from dba_indexes');
      dbms_output.put_line('where index_type = '||''''||'NORMAL/REV'||''''||'');
      dbms_output.put_line('      And OWNER not in '||owner_blacklist);
	  dbms_output.put_line(';');
 END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Sequence Information');
      dbms_output.put_line('Prompt Footnote Sequence numbers - Sequences could be a issue for HA configurations');
      dbms_output.put_line('SELECT SEQUENCE_OWNER,');
      dbms_output.put_line(' 	 SEQUENCE_NAME,');
      dbms_output.put_line(' 	 MIN_VALUE,');
      dbms_output.put_line(' 	 MAX_VALUE,');
      dbms_output.put_line(' 	 INCREMENT_BY INCR,');
      dbms_output.put_line(' 	 CYCLE_FLAG CYCLE,');
      dbms_output.put_line(' 	 ORDER_FLAG "ORDER",');
      dbms_output.put_line(' 	 CACHE_SIZE,');
      dbms_output.put_line(' 	 LAST_NUMBER');
      dbms_output.put_line('  FROM DBA_SEQUENCES');
      dbms_output.put_line(' WHERE SEQUENCE_OWNER not in '||owner_blacklist);
	  dbms_output.put_line(';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Archivelog Volume per Day');
      dbms_output.put_line('Prompt Footnote Summary of log volume processed by day for last 7 days:');
      dbms_output.put_line('select to_char(first_time, '||''''||'mm/dd'||''''||') ArchiveDate,');
      dbms_output.put_line('       round((sum(BLOCKS*BLOCK_SIZE/1024/1024)),2) LOG_in_MB');
      dbms_output.put_line('from sys.v_$archived_log');
      dbms_output.put_line('where first_time > sysdate - 7');
      dbms_output.put_line('group by to_char(first_time, '||''''||'mm/dd'||''''||')');
      dbms_output.put_line('order by to_char(first_time, '||''''||'mm/dd'||''''||');');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Redo Log Information');
      dbms_output.put_line('select group#, THREAD#, SEQUENCE#, BYTES/1024/1024, MEMBERS, ARCHIVED, STATUS, FIRST_CHANGE#, to_char(FIRST_TIME, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') First_time  from sys.v_$log order by group#;');
      dbms_output.put_line('select group#, status, member, type from sys.v_$logfile order by group#;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Materialized View List');
      dbms_output.put_line('Prompt Footnote List will be used to Exclude the MView from the Replication:');
      dbms_output.put_line('select owner, object_name, object_type, status ');
      dbms_output.put_line('from dba_objects ');
      dbms_output.put_line('where object_type='||''''||'MATERIALIZED VIEW'||''''||'');
      dbms_output.put_line('and owner not in '||owner_blacklist);
	  dbms_output.put_line('order by owner, object_name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Transportable Platform ');
      dbms_output.put_line('COLUMN PLATFORM_NAME FORMAT A32');
      dbms_output.put_line('SELECT * FROM sys.v_$transportable_platform;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Transport Violations');
      dbms_output.put_line('select * from sys.transport_set_violations;');
   END IF;
   
   --IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      --dbms_output.put_line('Prompt Heading U_I_GG DB:Database Home');
      --dbms_output.put_line('var Oracle_Home varchar2(100);');
      --dbms_output.put_line('begin');
      --dbms_output.put_line('sys.dbms_system.get_env('||''''||'ORACLE_HOME'||''''||', :Oracle_Home);');
      --dbms_output.put_line('end;');
      --dbms_output.put_line('/');
      --dbms_output.put_line('Print :Oracle_home');
   --END IF;

   IF ( gv_slab in ('12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Home');
      dbms_output.put_line('select SYS_CONTEXT (''USERENV'',''ORACLE_HOME'') ORACLE_HOME from dual;');
   END IF;   
   
   DECLARE
      avl varchar2(1);
      str varchar2(500);
      str_bundle_clause varchar2(30);
      cursor c1 is select column_name,column_id from dba_tab_columns
     where table_name='REGISTRY$HISTORY' and OWNER='SYS' order by column_id;
   BEGIN
	  IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
         dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_1');
         dbms_output.put_line('SELECT * FROM sys.v_$version;');
      end if;
      BEGIN
         for i in c1 loop
           avl:='y';
           if(i.column_id<2) then
              str:='SELECT '||i.column_name;
           else
              str:=str||','||i.column_name;
           end if;
           if(i.column_name='BOUNDLE_SERIES') THEN
            str_bundle_clause :=' and BUNDLE_SERIES=''PSU''';
           end if;
         end loop;
         if(avl='y') then
            str:=str|| ' FROM sys.REGISTRY$HISTORY where action=''APPLY''';
            str:=str|| str_bundle_clause||';';
         end if;
         if( length(ltrim(str)) > 5 ) then 
            dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_2');
            dbms_output.put_line(str);
         end if;
      END;
   END;  

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('col comp_id for a20');
      dbms_output.put_line('col status  for a30');
      dbms_output.put_line('col value   for a30');
      dbms_output.put_line('Prompt Heading U_I_GG DB:Auditing Check');
      dbms_output.put_line('show parameter audit');
      dbms_output.put_line('Prompt Heading U_I_GG DB:Cluster Check');
      dbms_output.put_line('show parameter cluster_database');
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Components ');
      dbms_output.put_line('select COMP_ID,COMP_NAME,VERSION,STATUS,MODIFIED from dba_registry;');

   END IF;
   
    IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Options and Features');
      dbms_output.put_line('select * from sys.v_$option');
      dbms_output.put_line('where VALUE = '||''''||'TRUE'||''''||';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Feature Usage');
      dbms_output.put_line('SELECT u1.name,');
      dbms_output.put_line('u1.detected_usages');
      dbms_output.put_line('FROM   dba_feature_usage_statistics u1');
      dbms_output.put_line('WHERE  u1.version = (SELECT MAX(u2.version)');
      dbms_output.put_line('FROM   dba_feature_usage_statistics u2');
      dbms_output.put_line('WHERE  u2.name = u1.name)');
      dbms_output.put_line('AND u1.detected_usages <> 0');
      dbms_output.put_line('ORDER BY u1.name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Parameters');
      dbms_output.put_line('select name, value from sys.v_$parameter');
      dbms_output.put_line('where isdefault='||''''||'FALSE'||''''||'');
      dbms_output.put_line('order by name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Properties');
      dbms_output.put_line('select * from database_properties;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Size ');
      dbms_output.put_line('select * from (select database_size, dbs_data_size,Archive_logs_size, rollback_segs_size,temp_ts_size,free_space_size ,size_units');
      dbms_output.put_line('from ');
      dbms_output.put_line('(select round(a.Database_Size_GB,2) database_size');
      dbms_output.put_line(',case when round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2)<0 then 1 else round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2) end dbs_data_size');
      dbms_output.put_line(',round(b.Archive_logs_GB,2)  Archive_logs_size,round(c.rollback_segs_GB,2) rollback_segs_size,round(d.TEMP_TS_GB,2)  temp_ts_size,round(e.free_space_GB,2) free_space_size,''all units are in GB'' size_units');
      dbms_output.put_line('from');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) Database_Size_GB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) Archive_logs_GB from sys.v_$log) b,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) rollback_segs_GB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) TEMP_TS_GB from dba_temp_files) d,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) free_space_GB from dba_free_space) e');
      dbms_output.put_line('union');
      dbms_output.put_line('select round(a.Database_Size_MB,2) database_size');
      dbms_output.put_line(',case when round(( a.Database_Size_MB - (b.Archive_logs_MB + c.rollback_segs_MB + d.TEMP_TS_MB + e.free_space_MB)),2)<0 then 1 else round(( a.Database_Size_MB - (b.Archive_logs_MB + c.rollback_segs_MB + d.TEMP_TS_MB + e.free_space_MB)),2) end  dbs_data_size');
      dbms_output.put_line(',round(b.Archive_logs_MB,2)  Archive_logs_size,round(c.rollback_segs_MB,2) rollback_segs_size,round(d.TEMP_TS_MB,2) temp_ts_size,round(e.free_space_MB,2) free_space_size,''all units are MB'' size_units');
      dbms_output.put_line('from');
      dbms_output.put_line('(select sum(bytes/1024/1024) Database_Size_MB from ( select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
      dbms_output.put_line('(select sum(bytes/1024/1024) Archive_logs_MB from sys.v_$log) b,');
      dbms_output.put_line('(select sum(bytes/1024/1024) rollback_segs_MB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
      dbms_output.put_line('(select sum(bytes/1024/1024) TEMP_TS_MB from dba_temp_files) d,');
      dbms_output.put_line('(select sum(bytes/1024/1024) free_space_MB from dba_free_space)e');
      dbms_output.put_line('union');
      dbms_output.put_line('select round(a.Database_Size_KB,2) database_size');
      dbms_output.put_line(',round(( a.Database_Size_KB- b.Archive_logs_KB-c.rollback_segs_KB-d.TEMP_TS_KB-e.free_space_KB),2) dbs_data_size');
      dbms_output.put_line(',round(b.Archive_logs_KB,2)  Archive_logs_size,round(c.rollback_segs_KB,2) rollback_segs_size,round(d.TEMP_TS_KB,2) temp_ts_size,round(e.free_space_KB,2) free_space_size,''all units are in KB'' size_units');
      dbms_output.put_line('from   ');
      dbms_output.put_line('(select sum(bytes/1024) Database_Size_KB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
      dbms_output.put_line('(select sum(bytes/1024) Archive_logs_KB from sys.v_$log) b,');
      dbms_output.put_line('(select sum(bytes/1024) rollback_segs_KB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM''))) c,');
      dbms_output.put_line('(select sum(bytes/1024) TEMP_TS_KB from dba_temp_files) d,');
      dbms_output.put_line('(select sum(bytes/1024) free_space_KB from dba_free_space) e)');
      dbms_output.put_line('where 0 not in (dbs_data_size,Archive_logs_size,rollback_segs_size,temp_ts_size,free_space_size)');
      dbms_output.put_line('order by database_size');
      dbms_output.put_line(') where rownum < 3;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Tablespace Details');
      dbms_output.put_line('set lines 200');
      dbms_output.put_line('select a.tablespace_name "Tablespace",');
      dbms_output.put_line(' a.total_size_mb   "Total_Size_MB",');
      dbms_output.put_line('------(a.total_size_mb - b.free_size_mb) Used_Size_MB,');
      dbms_output.put_line('------b.free_size_mb "Free_Size_MB",');
      dbms_output.put_line(' d.extent_management,');
      dbms_output.put_line(' d.segment_space_management,');
      dbms_output.put_line(' auto_extension,');
      dbms_output.put_line(' d.status,');
	  dbms_output.put_line(' d.BLOCK_SIZE,');
      dbms_output.put_line(' TO_CHAR(NVL((a.bytes - NVL(b.bytes, 0)) / a.maxbytes * 100, 0), '||''''||'990.00'||''''||')  "Used % (including Autoextend)"');
      dbms_output.put_line(' from   ( select tablespace_name, round(sum(bytes)/1024/1024, 2) total_size_mb,');
      dbms_output.put_line(' decode(sum(decode(autoextensible,'||''''||'YES'||''''||',1,0)),0,'||''''||'NO'||''''||','||''''||'YES'||''''||') auto_extension,sum(bytes) bytes,sum(decode(autoextensible,'||''''||'YES'||''''||',maxbytes,bytes)) maxbytes');
      dbms_output.put_line(' from   dba_data_files group  by tablespace_name ) a, ( select tablespace_name, round(sum(bytes)/1024/1024, 2) free_size_mb,');
      dbms_output.put_line(' round (max( bytes) / ( 1024 * 1024 ), 2 )max_free,sum(bytes) bytes from   dba_free_space');
      dbms_output.put_line(' group  by tablespace_name ) b, ( select tablespace_name, max(next_extent) / ( 1024 * 1024 ) max_next from   dba_segments');
      dbms_output.put_line(' group  by tablespace_name ) c, dba_tablespaces d');
      dbms_output.put_line('where  d.tablespace_name = a.tablespace_name(+)');
      dbms_output.put_line('and    d.tablespace_name = b.tablespace_name(+)');
      dbms_output.put_line('and    d.tablespace_name = c.tablespace_name(+)');
      dbms_output.put_line('and    a.tablespace_name is not null');
      dbms_output.put_line('order by a.tablespace_name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles ');
      dbms_output.put_line('select a.TABLESPACE_NAME,a.FILE_ID,a.FILE_NAME,a.BYTES/1024/1024 BYTES_in_MB,a.AUTOEXTENSIBLE,a.MAXBYTES/1024/1024/1024 MAX_BYTES_IN_GB,b.enabled,');
      dbms_output.put_line('to_char(b.CREATION_TIME,'||''''||'DD_Mon_YYYY HH24:MI:SS'||''''||') CREATION_TIME');
      dbms_output.put_line('from dba_data_files a,');
      dbms_output.put_line('sys.v_$datafile b');
      dbms_output.put_line('where a.file_name =b.name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles - Tempfiles ');
      dbms_output.put_line('select TABLESPACE_NAME,sum(bytes/1024/1024) TEMP_USED_MB,sum(MAXBYTES)/1024/1024/1024 Max_Size_GB from dba_temp_files group by tablespace_name;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Recovery file ');
      dbms_output.put_line('select FILE#, ONLINE_STATUS from sys.v_$recover_file order by 1;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles in Backup Mode');
      dbms_output.put_line('select a.file#,b.file_name, a.status, a.change#, ');
      dbms_output.put_line('       to_char(a.time, '||''''||'dd-Mon-YYYY HH24:Mi:SS'||''''||') time ');
      dbms_output.put_line('  from sys.v_$backup a,dba_data_files b');
      dbms_output.put_line(' where a.file#=b.file_id');
      dbms_output.put_line(' and a.status <> '||''''||'NOT ACTIVE'||''''||'');
      dbms_output.put_line(' order by a.file#;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Directories Information');
      dbms_output.put_line('select '||''''||''||''''||' owner,name directory_name, VALUE directory_path FROM sys.v_$parameter');
      dbms_output.put_line('WHERE NAME='||''''||'utl_file_dir'||''''||'');
      dbms_output.put_line('union all');
      dbms_output.put_line('SELECT owner, directory_name, directory_path FROM dba_directories;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_DBA_JOBS');
      dbms_output.put_line('SELECT JOB, SUBSTR(WHAT,1,35) "Description", NEXT_DATE, NEXT_SEC, BROKEN ');
      dbms_output.put_line('FROM DBA_JOBS;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_DBA_SCHEDULER_SCHEDULES');
      dbms_output.put_line('select owner, schedule_name,START_DATE from dba_scheduler_schedules');
      dbms_output.put_line('where owner not in '||owner_blacklist);
	  dbms_output.put_line(';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_DBA_SCHEDULER_JOBS');
      dbms_output.put_line('select owner,JOB_NAME,START_DATE,END_DATE,STATE,LAST_START_DATE,LAST_RUN_DURATION,NEXT_RUN_DATE from dba_scheduler_jobs');
      dbms_output.put_line('where owner not in '||owner_blacklist);
	  dbms_output.put_line(';');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Users ');
      dbms_output.put_line('select * from (');
      dbms_output.put_line('select '||''''||'Regular'||''''||' USER_TYPE,USERNAME');
      dbms_output.put_line(',account_status');
      dbms_output.put_line(',to_char(created, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') CREATED');
      dbms_output.put_line(',to_char(EXPIRY_DATE, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') EXPIRY_DATE');
      dbms_output.put_line(',PROFILE ');
      dbms_output.put_line(',PASSWORD_VERSIONS PVERSION');
      dbms_output.put_line(',DEFAULT_TABLESPACE');
      dbms_output.put_line(',TEMPORARY_TABLESPACE TEMP_TABLESPACE');
      dbms_output.put_line('from dba_users where username not in '||owner_blacklist);
	  dbms_output.put_line('Union all');
      dbms_output.put_line('select '||''''||'Default'||''''||' USER_TYPE,USERNAME');
      dbms_output.put_line(',account_status');
      dbms_output.put_line(',to_char(created, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') CREATED');
      dbms_output.put_line(',to_char(EXPIRY_DATE, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') EXPIRY_DATE');
      dbms_output.put_line(',PROFILE ');
      dbms_output.put_line(',PASSWORD_VERSIONS PVERSION');
      dbms_output.put_line(',DEFAULT_TABLESPACE');
      dbms_output.put_line(',TEMPORARY_TABLESPACE TEMP_TABLESPACE');
      dbms_output.put_line('from dba_users where username in '||owner_blacklist);
	  dbms_output.put_line(') order by 1,3,7;');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Users having 10G Password Version');
      dbms_output.put_line('select * from (');
      dbms_output.put_line('select '||''''||'Regular'||''''||' USER_TYPE,USERNAME');
      dbms_output.put_line(',account_status');
      dbms_output.put_line(',to_char(created, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') CREATED');
      dbms_output.put_line(',to_char(EXPIRY_DATE, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') EXPIRY_DATE');
      dbms_output.put_line(',PROFILE ');
      dbms_output.put_line(',PASSWORD_VERSIONS PVERSION');
      dbms_output.put_line(',DEFAULT_TABLESPACE');
      dbms_output.put_line(',TEMPORARY_TABLESPACE TEMP_TABLESPACE');
      dbms_output.put_line('from dba_users where username not in '||owner_blacklist);
	  dbms_output.put_line('Union all');
      dbms_output.put_line('select '||''''||'Default'||''''||' USER_TYPE,USERNAME');
      dbms_output.put_line(',account_status');
      dbms_output.put_line(',to_char(created, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') CREATED');
      dbms_output.put_line(',to_char(EXPIRY_DATE, '||''''||'DD-Mon-YYYY HH24:Mi:SS'||''''||') EXPIRY_DATE');
      dbms_output.put_line(',PROFILE ');
      dbms_output.put_line(',PASSWORD_VERSIONS PVERSION');
      dbms_output.put_line(',DEFAULT_TABLESPACE');
      dbms_output.put_line(',TEMPORARY_TABLESPACE TEMP_TABLESPACE');
      dbms_output.put_line('from dba_users where username in '||owner_blacklist);
	  dbms_output.put_line(') WHERE TRIM(PVERSION) =''10G''');
	  dbms_output.put_line('order by 1,3,7;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Index Organised Tables');
      dbms_output.put_line('SELECT OWNER,table_name, iot_type, iot_name FROM dba_tables ');
      dbms_output.put_line('where owner not in '||owner_blacklist);
	  dbms_output.put_line('ORDER BY 1;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Invalid Objects');
      dbms_output.put_line('select owner||'||''''||'.'||''''||'||object_name Object_name,object_type,status from dba_objects');
      dbms_output.put_line('where status<>'||''''||'VALID'||''''||'');
      dbms_output.put_line('and owner not in'||owner_blacklist);
	  dbms_output.put_line(';');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:DB link Info');
      dbms_output.put_line('SELECT owner,db_link,username,host,created FROM dba_db_links ORDER BY owner;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:List of Policy Functions / Objects');
      dbms_output.put_line('PROMPT Footnote Identify all policy functions, the policy function owner , associated object with owner');
      dbms_output.put_line('SELECT pf_owner function_owner, function, policy_name, object_owner policy_owner, object_name, package, policy_group ');
      dbms_output.put_line('  FROM dba_policies where pf_owner <> '||''''||'XDB'||''''||'');
      dbms_output.put_line(' ORDER BY pf_owner, function, policy_name, object_owner, object_name, package, policy_group ;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Owner wise COUNT of Policy Functions');
      dbms_output.put_line('PROMPT Footnote Identify all the policy function owners and the number of policy functions they own in the database.  ');
      dbms_output.put_line('SELECT pf_owner vpd_owner_name, count(1) Number_of_VPD_Owners FROM dba_policies group by pf_owner;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Policy Contexts ');
      dbms_output.put_line('PROMPT Footnote Identify all policy contexts');
      dbms_output.put_line('SELECT object_owner, object_name, namespace, attribute ');
      dbms_output.put_line('  FROM DBA_POLICY_CONTEXTS');
      dbms_output.put_line('ORDER BY object_owner, object_name, namespace, attribute;');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Policy Groups');
      dbms_output.put_line('PROMPT Footnote Identify all the policy Groups in the database');
      dbms_output.put_line('SELECT object_owner, object_name, policy_group FROM dba_policy_groups;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Security Relevant Columns');
      dbms_output.put_line('PROMPT Footnote Identify security Relevant columns of all VPD policies in the database');
      dbms_output.put_line('SELECT object_owner, object_name, policy_group, policy_name, sec_rel_column, column_option ');
      dbms_output.put_line('  FROM DBA_SEC_RELEVANT_COLs');
      dbms_output.put_line(' ORDER BY object_owner, object_name, policy_group, policy_name, sec_rel_column, column_option ;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:DB Users with Exempt Access Policy');
      dbms_output.put_line('select grantee,privilege from dba_sys_privs ');
      dbms_output.put_line('where privilege='||''''||'EXEMPT ACCESS POLICY'||''''||';');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Advanced_Queue_Info');
      dbms_output.put_line('select q.owner||'||''''||'.'||''''||'||q.name QUEUE_NAME,q.queue_type,q.enqueue_enabled, q.dequeue_enabled,q.retention,');
      dbms_output.put_line(' q.network_name, s.waiting,s.ready,s.expired,s.total_wait,s.average_wait');
      dbms_output.put_line('from dba_queues q,sys.v_$aq s where s.qid=q.qid and owner not in '||owner_blacklist);
      dbms_output.put_line('order by owner, name ;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database Advanced_Queue_Tables_Info');
      dbms_output.put_line('select q.owner||'||''''||'.'||''''||'||q.queue_table queue_table_name, num_rows, blocks,');
      dbms_output.put_line(' last_analyzed, chain_cnt from all_queue_tables q, all_tables t');
      dbms_output.put_line('where q.owner = t.owner and q.queue_table = t.table_name and q.owner not in '||owner_blacklist);
	  dbms_output.put_line('order by q.owner, q.queue_table;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_Views_Info');
      dbms_output.put_line('select owner, mview_name, container_name, updatable, last_refresh_date');
      dbms_output.put_line(', compile_state, refresh_mode, master_link from dba_mviews ');
      dbms_output.put_line('where owner not in '||owner_blacklist);
	  dbms_output.put_line('order by owner, mview_name;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      for j in ( select 1 from dual where not exists (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) ) loop
         dbms_output.put_line('PROMPT Heading U_I_GG DB:XML_Types');
         dbms_output.put_line('Prompt Footnote Oracle XML Database not Installed');
      end loop;
      for j in ( select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) loop
         dbms_output.put_line('PROMPT Heading U_I_GG DB:XML_Types');
         dbms_output.put_line('select distinct p.tablespace_name from dba_tablespaces p,');
         dbms_output.put_line(' dba_xml_tables x, dba_users u, all_all_tables t where');
         dbms_output.put_line(' t.table_name=x.table_name and t.tablespace_name=p.tablespace_name');
         dbms_output.put_line(' and x.owner=u.username;');
      end loop;
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      for j in ( select 1 from dual where not exists (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Tables');
         dbms_output.put_line('Prompt Footnote Oracle XML Database not Installed');
      end loop;
      for j in ( select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Tables');
         dbms_output.put_line('select owner||'||''''||'.'||''''||'||table_name table_name, xmlschema, element_name, storage_type');
         dbms_output.put_line('from dba_xml_tables where owner not in '||owner_blacklist);
		 dbms_output.put_line('order by owner, table_name ;');
      end loop;
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      for j in ( select 1 from dual where not exists (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Columns');
         dbms_output.put_line('Prompt Footnote Oracle XML Database not Installed');
      end loop;
      for j in ( select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Columns');
         dbms_output.put_line('select owner||'||''''||'.'||''''||'|| table_name table_name, column_name, xmlschema, element_name, storage_type');
         dbms_output.put_line('from dba_xml_tab_cols where owner not in '||owner_blacklist);
		 dbms_output.put_line('order by owner, table_name, column_name ;');
      end loop;
   end if;

   if ( gv_slab in ('11g1') ) THEN
      for j in ( select 1 from dual where not exists (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Indexes');
         dbms_output.put_line('Prompt Footnote Oracle XML Database not Installed');
      end loop;
      for j in (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Indexes');
         dbms_output.put_line('select index_owner, table_name, index_name, type, async, stale');
         dbms_output.put_line('from dba_xml_indexes where index_owner not in '||owner_blacklist);
		 dbms_output.put_line('order by index_owner, table_name, index_name ;');
      end loop;
   elsif ( gv_slab in ('11g2','12c','13','18','19') ) THEN
      for j in ( select 1 from dual where not exists (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Indexes');
         dbms_output.put_line('Prompt Footnote Oracle XML Database not Installed');
         dbms_output.put_line('Prompt Footversion Tested on 11.2.0.3');
      end loop;
      for j in (select 1 from sys.dba_registry where lower(comp_name) like lower('%Oracle XML Database%') ) loop
         dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Indexes');
         dbms_output.put_line('select index_owner, table_name, index_name, type, index_type, async, stale');
         dbms_output.put_line('from dba_xml_indexes where index_owner not in '||owner_blacklist);
		 dbms_output.put_line('order by index_owner, table_name, index_name ;');
      end loop;
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Info');
      dbms_output.put_line('select l.log_owner||'||''''||'.'||''''||'||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows');
      dbms_output.put_line('from dba_mview_logs l, all_tables t');
      dbms_output.put_line('where (t.last_analyzed is null or t.blocks > 1000 or t.num_rows > 5000)');
      dbms_output.put_line('and l.log_table = t.table_name');
      dbms_output.put_line('order by l.master, l.log_table;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs without statistics');
      dbms_output.put_line('select l.log_owner, count(*)');
      dbms_output.put_line('from dba_mview_logs l, all_tables t');
      dbms_output.put_line('where      t.last_analyzed is null');
      dbms_output.put_line('and l.log_table = t.table_name');
      dbms_output.put_line('group by l.log_owner');
      dbms_output.put_line('order by l.log_owner;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs_indexes without statistics');
      dbms_output.put_line('select l.log_owner, count(*)');
      dbms_output.put_line('from dba_mview_logs l, all_tables t');
      dbms_output.put_line('where      t.last_analyzed is null');
      dbms_output.put_line('and l.log_table = t.table_name');
      dbms_output.put_line('and (l.log_owner, l.master) in (select table_owner, table_name from all_indexes)');
      dbms_output.put_line('group by l.log_owner');
      dbms_output.put_line('order by l.log_owner;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs bigger logs only');
      dbms_output.put_line('select l.log_owner||'||''''||'.'||''''||'||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows');
      dbms_output.put_line('from dba_mview_logs l, all_tables t');
      dbms_output.put_line('where      t.num_rows > 100000');
      dbms_output.put_line('and l.master = t.table_name');
      dbms_output.put_line('order by t.num_rows desc;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:Database Trigger count');
      dbms_output.put_line('select count(*) "Trigger Count",trigger_type from dba_triggers group by trigger_type;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:Database NLS Parameters');
      dbms_output.put_line('select a.parameter NLS_PARAMETER,a.value DATABASE_VALUE');
      dbms_output.put_line(',b.value CURRENT_VALUE');
      dbms_output.put_line(' from NLS_DATABASE_PARAMETERS a, sys.v_$parameter b');
      dbms_output.put_line('where lower(a.parameter)=b.name(+) order by 1;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('PROMPT Heading U_I_GG DB:Database Archive Log Volume');
      dbms_output.put_line('SELECT ROUND(SUM(blocks*block_size)/1024/1024/1024) arc_size,');
      dbms_output.put_line('    TRUNC(first_time) arc_date');
      dbms_output.put_line('    FROM sys.v_$archived_log');
      dbms_output.put_line('    WHERE dest_id=10');
      dbms_output.put_line('    GROUP BY TRUNC(first_time)');
      dbms_output.put_line('    ORDER BY 2 DESC;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Tablespace wise count of Partition Tables');
      dbms_output.put_line('select TABLESPACE_NAME,'||''''||'tables'||''''||' Object_type, count(1) count_of_tables ');
      dbms_output.put_line('FROM DBA_TAB_PARTITIONS');
      dbms_output.put_line('where table_owner not in '||owner_blacklist);
	  dbms_output.put_line('group by  TABLESPACE_NAME;');
   end if;

   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:Tables having Partitions');
      dbms_output.put_line('select  TABLESPACE_NAME,table_owner,table_name,count(partition_name)');
      dbms_output.put_line('from dba_tab_partitions');
      dbms_output.put_line('where table_owner not in '||owner_blacklist);
      dbms_output.put_line('group by TABLESPACE_NAME,table_owner,table_name');
	  dbms_output.put_line(';');
   END IF;
   
   if ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading U_I_GG DB:External Table Details');
      dbms_output.put_line('select * from DBA_EXTERNAL_TABLES');
	  dbms_output.put_line(';');
   END IF;

	DECLARE
	   r1_log_owner   varchar2(60);
	   r1_log_table   varchar2(60);
	   r1_master      varchar2(60);
	   v_has_rows     varchar2(1);
	   TYPE mlog_Type IS REF CURSOR;
	   mlog_cv        mlog_Type;
	   v_sub_str      varchar2(400);
	   l_mview        varchar2(256);
	   l_last_refresh date;
	   l_rows         number;
	   l_min_seq      number;
	   l_max_seq      number;
	   l_min_time     date;
	   l_max_time     date;
   BEGIN
		IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) then
			v_sub_str :='select log_owner,log_table,master from dba_mview_logs';
			dbms_output.put_line('PROMPT Heading U_I_GG DB:Database MV_log data accumulation info');
			--   dbms_output.put_line(v_sub_str);
			v_has_rows:='n';
			OPEN mlog_cv FOR  v_sub_str;
			LOOP
				FETCH mlog_cv INTO r1_log_owner,r1_log_table,r1_master;
				EXIT WHEN mlog_cv%NOTFOUND;
				BEGIN
				 execute immediate 'select (select owner||''.''||name||''@''||mview_site '||' from DBA_REGISTERED_MVIEWS where mview_id = mv.snapid) MV,'||' mv.snaptime last_refreshed, count(*),'||' min(mlog.snaptime$$), max(mlog.snaptime$$)'||' from '||r1_log_owner||'.'||r1_log_table||' mlog, SYS.SLOG$ mv'||' where mlog.snaptime$$ > mv.snaptime'||' and mv.master = '''||r1_master||''''||' group by mv.snapid, mv.snaptime' into l_mview,l_last_refresh,l_rows,l_min_time,l_max_time;
				 if(v_has_rows='y') then
					dbms_output.put_line('UNION ALL');
				 end if;
				 v_sub_str := 'SELECT ';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ''''||r1_log_owner||''''||' LOG_OWNER';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ','||''''||r1_log_table||''''||' LOG_TABLE_NAME';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ','||''''||to_char(l_last_refresh,'yyyy-mm-dd hh24:mi:ss') ||''''||' LAST_REFRESH';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ','||''''||l_mview||''''||' MVIEW_NAME ';
				 dbms_output.put_line(v_sub_str);    
				 v_sub_str := ','||''''||l_rows||''''||' ACCUM_ROWS ';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ','||''''||to_char(l_min_time,'yyyy-mm-dd hh24:mi:ss') ||''''||' MIN_TIME';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ','||''''||to_char(l_max_time,'yyyy-mm-dd hh24:mi:ss') ||''''||' MAX_TIME';
				 dbms_output.put_line(v_sub_str);
				 v_sub_str := ' from dual';
				 dbms_output.put_line(v_sub_str);
				 v_has_rows:='y';    
				EXCEPTION WHEN OTHERS THEN NULL;
				END;
			END LOOP;
			IF(v_has_rows='y') THEN
				dbms_output.put_line(';');
			END IF;
			CLOSE mlog_cv;
		END IF;
	END;
   
   IF ( gv_slab IN ('11g1','11g2','12c','13','18','19') ) THEN
	  dbms_output.put_line('alter session set nls_date_format = ''DD-Mon-YYYY'';');
      dbms_output.put_line('Prompt Heading U_I_GG OGG:Redo Log Switch History');
      dbms_output.put_line('SELECT  to_char(trunc(first_time),''DD-Mon-YY'') "Date",to_char(first_time, ''Dy'') "Day",count(1) Total,');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''00'',1,0)) "h0",SUM(decode(to_char(first_time, ''hh24''),''01'',1,0)) "h1",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''02'',1,0)) "h2",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''03'',1,0)) "h3",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''04'',1,0)) "h4",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''05'',1,0)) "h5",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''06'',1,0)) "h6",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''07'',1,0)) "h7",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''08'',1,0)) "h8",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''09'',1,0)) "h9",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''10'',1,0)) "h10",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''11'',1,0)) "h11",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''12'',1,0)) "h12",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''13'',1,0)) "h13",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''14'',1,0)) "h14",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''15'',1,0)) "h15",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''16'',1,0)) "h16",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''17'',1,0)) "h17",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''18'',1,0)) "h18",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''19'',1,0)) "h19",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''20'',1,0)) "h20",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''21'',1,0)) "h21",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''22'',1,0)) "h22",');
      dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''23'',1,0)) "h23"');
      dbms_output.put_line('from v$log_history ');
      dbms_output.put_line('where first_time > sysdate - 30');
      dbms_output.put_line('group by trunc(first_time), to_char(first_time, ''Dy'')');
      dbms_output.put_line('order by trunc(first_time);');
   END IF;

-- Query added on 21/06/2021  
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Synonyms for Remote Objects');
      dbms_output.put_line('select OWNER,SYNONYM_NAME,TABLE_OWNER,TABLE_NAME,DB_LINK ');
	  dbms_output.put_line('from dba_synonyms ');
	  dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
	  dbms_output.put_line('and DB_LINK IS NOT NULL ');
	  dbms_output.put_line('order by 1,2; ');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Corrupt Blocks');
      dbms_output.put_line('select count(*) "Corrupt Database Blocks" ');
	  dbms_output.put_line('from v$database_block_corruption; ');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Encrypted - Tablespace');
      dbms_output.put_line('SELECT B.NAME, ENCRYPTIONALG, ENCRYPTEDTS  ');
	  dbms_output.put_line('from sys.V_$ENCRYPTED_TABLESPACES A, sys.V_$TABLESPACE  B ');
	  dbms_output.put_line('WHERE A.TS# = B.TS#;');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Encrypted - Columns');
      dbms_output.put_line('select OWNER,TABLE_NAME,COLUMN_NAME,ENCRYPTION_ALG,SALT');
      dbms_output.put_line('from dba_encrypted_columns');
	  dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
      dbms_output.put_line('order by 1,2,3;');
   END IF;
   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
	  dbms_output.put_line('Prompt Heading DB:Database Encrypted - Database Wallet Details');
      dbms_output.put_line('SELECT * from V_$ENCRYPTION_WALLET;  ');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Proxy Connections');
      dbms_output.put_line('select * ');
	  dbms_output.put_line('from dba_proxies ');
	  dbms_output.put_line('order by 1,2; ');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database RMAN Configuration');
      dbms_output.put_line('SELECT name, value ');
	  dbms_output.put_line('from sys.v_$rman_configuration ');
	  dbms_output.put_line('order by 1; ');
   END IF;

   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Custom Schema Size');
      dbms_output.put_line('select owner,sum(bytes)/1024/1024/1024 as "size in GB" ');
	  dbms_output.put_line('from dba_segments ');
	  dbms_output.put_line('WHERE owner not in '||owner_blacklist);
	  dbms_output.put_line('group by owner ');
	  dbms_output.put_line('order by 2 asc; ');
   END IF;

-- Query added on 16/08/2021 
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:DNFS Status Details');
      dbms_output.put_line('select * from gv$dnfs_servers;');
   END IF;
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database ASM Disk Group Details');
      dbms_output.put_line('SELECT o.name group_name, o.sector_size sector_size, o.block_size block_size, o.allocation_unit_size allocation_unit_size, o.state state, o.type type, o.total_mb total_mb, (total_mb - free_mb) used_mb, ROUND((1- (free_mb / decode(total_mb,0,1)))*100, 2)  pct_used ');
	  dbms_output.put_line('FROM v$asm_diskgroup o ;');
   END IF;
   --IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      --dbms_output.put_line('Prompt Heading DB:ACL Details');
      --dbms_output.put_line('select * from dba_network_acls;');
   --END IF;
   --IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      --dbms_output.put_line('Prompt Heading DB:ACL Privileges');
      --dbms_output.put_line('select * from dba_network_acl_privileges;');
   --END IF;
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:LOB Segment Details');
	  dbms_output.put_line('SELECT * FROM (SELECT l.owner,l.table_name,l.column_name,l.segment_name,l.tablespace_name,index_name,ENCRYPT,COMPRESSION,SECUREFILE,ROUND(s.bytes/1024/1024/1024,2) size_GB ');
	  dbms_output.put_line('FROM   dba_lobs l JOIN dba_segments s ON s.owner = l.owner AND s.segment_name = l.segment_name ');
	  dbms_output.put_line('where l.owner not in '||owner_blacklist);
	  dbms_output.put_line('order by 10 DESC);');	  
   END IF;
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Restricted Session Username');
      dbms_output.put_line('select username Restricted_Session_username from (select u.username from dba_role_privs rp,dba_users u where u.username=rp.grantee and ');
	  dbms_output.put_line('rp.granted_role in (select grantee from dba_sys_privs where privilege=''RESTRICTED_SESSION'' and grantee in (select role from dba_roles)) union ');
	  dbms_output.put_line('select grantee from dba_sys_privs where privilege=''RESTRICTED_SESSION'' and grantee not in (select role from dba_roles));');
   END IF;   
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database Global Names value details');
      dbms_output.put_line('select ''Show parameter global_names'' GLOBAL_NAME_DETAILS,(select value from v$parameter where name=''global_names'') VALUE from dual union select ''select GLOBAL_NAME from GLOBAL_NAME;'' Command,(select GLOBAL_NAME from GLOBAL_NAME) VALUE from dual;');
   END IF;    
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading DB:Database users having SUPERUSER privileges');
      dbms_output.put_line('col USERNAME for a30');
      dbms_output.put_line('col SYSDBA for a10');
      dbms_output.put_line('col SYSOPER for a10');
      dbms_output.put_line('col SYSASM for a10');
      dbms_output.put_line('select * from v$pwfile_users;');
   END IF;    
   IF ( gv_slab in ('11g1','11g2','12c','13','18','19') ) THEN
      dbms_output.put_line('Prompt Heading 00:Discovery Summary');
      dbms_output.put_line('WITH SERVER_INFO AS (');
      dbms_output.put_line('SELECT (select name from v$database) DB_NAME,');
      dbms_output.put_line('(select version from v$instance) DB_VERSION,');
      dbms_output.put_line('(select count(1) from dba_users where username=''SYSADM'') SYSADM_USER,');	  
      dbms_output.put_line('(select HOST_NAME from v$instance) HOST_NAME,');
      dbms_output.put_line('(select decode(count(*),3,''1/8th OR Quarter RAC'',7,''Half RAC'',14,''Full RAC'',''Non-Exadata'') from (select distinct cell_name from gv$cell_state)) Exadata_Option,');
      dbms_output.put_line('(select Platform_name from v$database) OS_PLATFORM,');
      dbms_output.put_line('(select upper(ENDIAN_FORMAT) ENDIANNESS from v$transportable_platform tp, v$database db where tp.platform_id=db.platform_id) ENDIANNESS,');
      dbms_output.put_line('(select value from v$parameter where name =''cluster_database'') CLUSTER_DATABASE,');
      dbms_output.put_line('(SELECT max(round(s.bytes/1024/1024/1024,2)) Lob_max_size FROM   dba_lobs l JOIN dba_segments s ON s.owner = l.owner AND s.segment_name = l.segment_name');
      dbms_output.put_line('where l.owner not in '||owner_blacklist||') LOB_MAX,');
      dbms_output.put_line('(select count(1) from dba_scheduler_schedules where owner not in '||owner_blacklist||') DB_JOBS,');
      dbms_output.put_line('(select count(partition_name) from dba_tab_partitions');
      dbms_output.put_line('where table_owner not in '||owner_blacklist||') TAB_PART,');
      dbms_output.put_line('(select VERSION from V$TIMEZONE_FILE) TIME_ZONE,');
      dbms_output.put_line('(select COUNT(1) from dba_mviews where owner not in '||owner_blacklist||') MVIEWS,');
      dbms_output.put_line('(select LOG_MODE  from v$database) LOG_MODE,');
      dbms_output.put_line('(SELECT COUNT(1) from (select username from dba_users where trim(PASSWORD_VERSIONS) = ''10G'' and username not in '||owner_blacklist||')) PASSWORD_VERSIONS,');
      dbms_output.put_line('(SELECT COUNT(BLOCK_SIZE) FROM (SELECT DISTINCT BLOCK_SIZE FROM dba_tablespaces)) MULTI_BL_TBS,');
      dbms_output.put_line('(SELECT COUNT(PROFILE) FROM (SELECT DISTINCT PROFILE FROM dba_users where PROFILE<>''DEFAULT'')) CUSTOM_PROFILE,');
      dbms_output.put_line('(SELECT count(1) from V$ENCRYPTION_WALLET where status <> ''CLOSED'') ENC_WALLET,');
      dbms_output.put_line('(select count(1) from dba_objects where status<>''VALID'' and owner not in '||owner_blacklist||') INVALID_OBJECT,');
      dbms_output.put_line('(select TO_CHAR(COUNT(NVL(OWNER,0))) from DBA_RECYCLEBIN) RECYCLE_BIN,');
      dbms_output.put_line('(select COUNT(1) from dba_registry WHERE STATUS<>''VALID'') INVALID_COMP,');
      dbms_output.put_line('(select comp_id||'' Exists'' from dba_registry where comp_id=''APEX'') APEX_COMP,');
      dbms_output.put_line('(SELECT count(1) FROM dba_directories) DB_DIRECTORIES,');
      dbms_output.put_line('(SELECT count(1) from V$ENCRYPTED_TABLESPACES A, sys.V_$TABLESPACE  B WHERE A.TS# = B.TS#) TDE,');
      dbms_output.put_line('(SELECT count(1) FROM dba_db_links) DB_LINK,');
      dbms_output.put_line('(select count(1) FROM v$parameter WHERE NAME=''utl_file_dir'' and VALUE is not null) UTL_FILE_DIR,');
      dbms_output.put_line('(select value/1024||'' KB''  from V$PARAMETER where name=''db_block_size'') DB_BLOCK_SIZE,');
      dbms_output.put_line('(select length(addr)*4 || ''-bits'' word_length from v$process where rownum=1) DB_WORD_SIZE,');
      dbms_output.put_line('(select SWITCHOVER_STATUS from v$database) STANDBY_PARAMETER_NAME,');
      dbms_output.put_line('(select count(1) from DBA_EXTERNAL_TABLES) EXT_TAB,');
      dbms_output.put_line('(select value from (select ''STANDARD'' value from dual union select value from V$PARAMETER where name=''max_string_size'' order by 1) where rownum <=1) MAX_STRING_SIZE');
      dbms_output.put_line('from dual');
      dbms_output.put_line('),');
      dbms_output.put_line('DB_SIZE AS (');
      dbms_output.put_line('select round(a.Database_Size_GB,4)||'' GB'' database_size,case when round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2)<0 then 1 else round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2) end ||'' GB'' dbs_data_size');
      dbms_output.put_line(',round(b.Archive_logs_GB,2)  Archive_logs_size,round(c.rollback_segs_GB,2) rollback_segs_size');
      dbms_output.put_line(',round(d.TEMP_TS_GB,2)  temp_ts_size,round(e.free_space_GB,2) free_space_size,''all units are in GB'' size_units');
      dbms_output.put_line('from');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) Database_Size_GB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) Archive_logs_GB from sys.v_$log )b,');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) rollback_segs_GB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) TEMP_TS_GB from dba_temp_files) d,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) free_space_GB from dba_free_space) e');
      dbms_output.put_line('),');
      dbms_output.put_line('CHAR_SET as (');
      dbms_output.put_line('select a.parameter NLS_PARAMETER,a.value DATABASE_VALUE,b.value CURRENT_VALUE from NLS_DATABASE_PARAMETERS a, sys.v_$parameter b');
      dbms_output.put_line('where lower(a.parameter)=b.name(+)');
      dbms_output.put_line('and upper(a.parameter) in (''NLS_CHARACTERSET'',''NLS_NCHAR_CHARACTERSET'')');
      dbms_output.put_line(')');
	  dbms_output.put_line('SELECT ''Discovery Utility Version'' KEY_POINTS,'''||&gv_script_version||''' KEY_VALUE, ''Discovery script version to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Name'' KEY_POINTS,DB_NAME KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Version'' KEY_POINTS,DB_VERSION KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''SYSADM user status'' KEY_POINTS,to_char(nvl(SYSADM_USER,0))||'' Exists'' KEY_VALUE, case when nvl(SYSADM_USER,0)=0 then ''No Action required'' else ''May need to reset password.Please check password version in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''Database Server'' KEY_POINTS,HOST_NAME KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Source Operation System'' KEY_POINTS,OS_PLATFORM KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Endianness'' KEY_POINTS,ENDIANNESS KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Timezone Version'' KEY_POINTS,to_char(TIME_ZONE) KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Block Size'' KEY_POINTS,DB_BLOCK_SIZE KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Word Size'' KEY_POINTS,DB_WORD_SIZE KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''utl_file_dir'' KEY_POINTS,to_char(nvl(UTL_FILE_DIR,0)) KEY_VALUE, case when nvl(UTL_FILE_DIR,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Directories'' KEY_POINTS,to_char(nvl(DB_DIRECTORIES,0)) KEY_VALUE, case when nvl(DB_DIRECTORIES,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database JOBs'' KEY_POINTS,to_char(nvl(DB_JOBS,0)) KEY_VALUE, case when nvl(DB_JOBS,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''DB Link'' KEY_POINTS,to_char(nvl(DB_LINK,0)) KEY_VALUE, case when nvl(DB_LINK,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Invalid objects'' KEY_POINTS,to_char(nvl(INVALID_OBJECT,0)) KEY_VALUE, case when nvl(INVALID_OBJECT,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Standby available'' KEY_POINTS,nvl(STANDBY_PARAMETER_NAME,''NOT AVAILABLE'') KEY_VALUE, ''Needs to be highlighted.Please check details in the report..'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Recycle Bin'' KEY_POINTS,to_char(NVL(RECYCLE_BIN,0)) KEY_VALUE,case when NVL(RECYCLE_BIN,0)=0 then ''No Action required'' else ''Needs to be highlighted.'' end  OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''max_string_size'' KEY_POINTS,MAX_STRING_SIZE KEY_VALUE, case when MAX_STRING_SIZE=''EXTENDED'' THEN ''Need to change this parameter at Target'' ELSE ''No Action required'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Archive Log Mode'' KEY_POINTS,LOG_MODE KEY_VALUE, case when LOG_MODE=''ARCHIVELOG'' THEN ''This database is in ARCHIVELOG mode'' else ''This database is in NOARCHIVELOG mode'' end FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Exadata_Option'' KEY_POINTS,EXADATA_OPTION KEY_VALUE, case when EXADATA_OPTION=''Non-Exadata'' THEN ''This database is Non-Exadata'' else ''This database is in Exadata. Please check the value'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Encrypted - Tablespace'' KEY_POINTS,to_char(nvl(TDE,0)) KEY_VALUE, case when nvl(TDE,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Encrypted - Database Wallet'' KEY_POINTS,to_char(nvl(ENC_WALLET,0)) KEY_VALUE, case when nvl(ENC_WALLET,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Cluster Check'' KEY_POINTS,CLUSTER_DATABASE KEY_VALUE, case when CLUSTER_DATABASE=''FALSE'' THEN ''This database is not cluster enabled'' else ''This database is cluster enabled'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Total Database_size'' KEY_POINTS,database_size KEY_VALUE, ''Total Database Size [Datafiles + Log files + Temp files]'' OBSERVATION FROM  DB_SIZE union all');
      dbms_output.put_line('SELECT ''Actual Database_size'' KEY_POINTS,dbs_data_size KEY_VALUE, ''Actual Data Size'' OBSERVATION FROM  DB_SIZE  union all');
      dbms_output.put_line('SELECT ''NLS_CHARACTERSET'' KEY_POINTS,case when CURRENT_VALUE is not null then CURRENT_VALUE else DATABASE_VALUE end  KEY_VALUE, ''Please check this value at target database belore migration.'' OBSERVATION FROM  CHAR_SET WHERE NLS_PARAMETER =''NLS_CHARACTERSET'' union all ');
      dbms_output.put_line('SELECT ''NLS_NCHAR_CHARACTERSET'' KEY_POINTS,case when CURRENT_VALUE is not null then CURRENT_VALUE else DATABASE_VALUE end  KEY_VALUE, ''Please check this value at target database belore migration.'' OBSERVATION FROM  CHAR_SET WHERE NLS_PARAMETER =''NLS_NCHAR_CHARACTERSET'' union all');
      dbms_output.put_line('SELECT ''LOB Max Size'' KEY_POINTS,to_char(nvl(LOB_MAX,0))||'' GB'' KEY_VALUE, case when nvl(LOB_MAX,0)<30 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Partition Count'' KEY_POINTS,to_char(nvl(TAB_PART,0)) KEY_VALUE, case when nvl(TAB_PART,0)<1000 then ''No Action required'' else ''Partions are on higher side.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Materialized View'' KEY_POINTS,to_char(nvl(MVIEWS,0)) KEY_VALUE, case when nvl(MVIEWS,0)=0 then ''No Action required'' else ''Needs to be highlighted..Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Invalid Components'' KEY_POINTS,to_char(nvl(INVALID_COMP,0)) KEY_VALUE, case when nvl(INVALID_COMP,0)=0 then ''No Action required'' else ''Needs to be highlighted..Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''APEX Components'' KEY_POINTS,nvl(APEX_COMP,''NA'') KEY_VALUE, case when nvl(APEX_COMP,''NA'')=''NA'' then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''External Table'' KEY_POINTS,to_char(nvl(EXT_TAB,0))||'' Exists'' KEY_VALUE, case when nvl(EXT_TAB,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''Multiblock Tablespaces'' KEY_POINTS,case when nvl(MULTI_BL_TBS,0)<=1 then ''Not Available'' else ''Multiblock Exists'' end KEY_VALUE, case when nvl(MULTI_BL_TBS,0)<=1 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Non-Default User Profile'' KEY_POINTS,to_char(nvl(CUSTOM_PROFILE,0))||'' Exists'' KEY_VALUE, case when nvl(CUSTOM_PROFILE,0)<=1 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''10g Password Version'' KEY_POINTS,PASSWORD_VERSIONS||'' Exists'' KEY_VALUE, case when nvl(PASSWORD_VERSIONS,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO;');
   END IF; 
   
END IF;   ---End of Non-CDB Block

IF :gv_multi = 1 THEN

		--dbms_output.put_line('ALTER SESSION SET CONTAINER = cdb$root;');
		dbms_output.put_line('SET MARKUP HTML ON;');
		dbms_output.put_line('set linesize 200;');
		dbms_output.put_line('set trimspool on;');
		dbms_output.put_line('set termout on;');
-------------------------------------------------------
--Prompt Heading U_I_GG DB:CPU Memory Details         |
-------------------------------------------------------		
		dbms_output.put_line('Prompt Heading U_I_GG DB:CPU Memory Details');
		dbms_output.put_line('select STAT_NAME,to_char(VALUE) as VALUE,COMMENTS from v$osstat where stat_name  IN (''NUM_CPUS'',''NUM_CPU_CORES'',''NUM_CPU_SOCKETS'') union');
		dbms_output.put_line('select STAT_NAME,VALUE/1024/1024/1024 || '' GB'',COMMENTS from v$osstat where stat_name  IN (''PHYSICAL_MEMORY_BYTES'');');
------------------------------------------------
--Prompt Heading U_I_GG OGG:Supplemental Logging|
------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Supplemental Logging');	
		dbms_output.put_line('SELECT name DB_NAME, log_mode "LogMode",supplemental_log_data_min "SupLog: Min", supplemental_log_data_pk "PK",supplemental_log_data_ui "UI", force_logging "Forced",supplemental_log_data_fk "FK", supplemental_log_data_all "All",to_char(created, ''MM-DD-YYYY HH24:MI:SS'') "Created" from sys.v_$database;');

----------------------------------------------
--Prompt Heading U_I_GG OGG:Compressed Objects|
----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Compressed Objects from CDB/PDB');
		dbms_output.put_line('SELECT b.name CDB_Name,a.TABLESPACE_NAME,a.DEF_TAB_COMPRESSION from CDB_TABLESPACES a inner join V$CONTAINERS b using (con_id) where con_id =1 and DEF_TAB_COMPRESSION <> ''DISABLED'';');
		dbms_output.put_line('SELECT b.name PDB_Name,a.TABLESPACE_NAME,a.DEF_TAB_COMPRESSION from CDB_TABLESPACES a inner join V$CONTAINERS b using (con_id) where con_id ='||&v_pdbconid||' and DEF_TAB_COMPRESSION <> ''DISABLED'';');
--------------------------------------------------------
--Prompt Heading U_I_GG DB:Database Standby availibility|
--------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Standby availibility');
		dbms_output.put_line('SELECT * from (SELECT name standby_parameter_name,value from sys.v_$parameter where (name like ''log_archive_dest_%'' or name in (''fal_server'',''db_file_name_convert'',''log_file_name_convert'')) and name not like ''%state%'' and value is not null');
		dbms_output.put_line('union');
		dbms_output.put_line('SELECT ''SWITCHOVER_STATUS'' standby_parameter_name, SWITCHOVER_STATUS value from sys.v_$database);');
------------------------------------------------------------------------------
--Prompt Heading U_I_GG DB:Schema Wise Object Count from CDB/PDB (Custom User)|
------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Schema Wise Object Count from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,object_type, count(1) object_count from CDB_OBJECTS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 and owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('group by C.NAME ,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,object_type order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,object_type, count(1) object_count from CDB_OBJECTS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' and owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('group by C.NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,object_type order by 1,2,3,4;');
--------------------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Distinct Column Data Type from CDB/PDB (Custom User)|
--------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Distinct Column Data Type from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Distinct Column Data Types and their Count in the Schema: of individual container');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,data_type, count(*) total FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id =1 and OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,data_type ORDER BY 1,2,3,4;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,data_type, count(*) total FROM  cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id = '||&v_pdbconid||' and OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,data_type ORDER BY 1,2,3,4;');
-----------------------------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables having more than 32 Columns from CDB/PDB (Custom User)|
-----------------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables having more than 32 Columns from CDB/PDB');
		dbms_output.put_line('SELECT distinct C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id =1 and OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND column_id > 32 order by 1,2,3;');
		dbms_output.put_line('SELECT distinct C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id = '||&v_pdbconid||' and OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND column_id > 32 order by 1,2,3;');
------------------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables Without Primary or Unique Key from CDB/PDB|
------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables Without Primary or Unique Key from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables With No Primary Key or Unique Index by Schema of individual container');
		dbms_output.put_line('SELECT C.NAME CDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name from CDB_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where not exists (select 1  from CDB_constraints ac');
		dbms_output.put_line('where ac.owner = O.owner and ac.table_name = O.table_name and ac.constraint_type IN (''P'',''U'')) And c.con_id =1 and O.OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name from CDB_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where not exists (select 1  from CDB_constraints ac');
		dbms_output.put_line('where ac.owner = O.owner and ac.table_name = O.table_name and ac.constraint_type IN (''P'',''U'')) And c.con_id = '||&v_pdbconid||' and O.OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3;');
------------------------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables with Nologging setting from CDB/PDB (Custom User)|
------------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Nologging setting from CDB/PDB');
		dbms_output.put_line('WITH custom_owner AS (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, '' '' Partition_Info, logging from CDB_TABLES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id =1 and OWNER in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, partitioning_type, decode(DEF_LOGGING,''NONE'',''NO'') "LOGGING" from CDB_part_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where DEF_LOGGING != ''YES'' and c.con_id =1 and OWNER in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner, table_name, PARTITION_NAME, logging from CDB_TAB_PARTITIONS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id =1 and table_owner in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner, table_name, PARTITION_NAME, logging from CDB_TAB_SUBPARTITIONS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id =1 and table_owner in (select username from custom_owner)');
		dbms_output.put_line('ORDER BY 1,2,3,4;');
		dbms_output.put_line('WITH custom_owner AS (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, '' '' Partition_Info, logging from CDB_TABLES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id =1 and OWNER in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, partitioning_type, decode(DEF_LOGGING,''NONE'',''NO'') "LOGGING" from CDB_part_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where DEF_LOGGING != ''YES'' and c.con_id = '||&v_pdbconid||' and OWNER in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner, table_name, PARTITION_NAME, logging from CDB_TAB_PARTITIONS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id = '||&v_pdbconid||' and table_owner in (select username from custom_owner)');
		dbms_output.put_line('UNION');
		dbms_output.put_line('select C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner, table_name, PARTITION_NAME, logging from CDB_TAB_SUBPARTITIONS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where logging <> ''YES'' and c.con_id = '||&v_pdbconid||' and table_owner in (select username from custom_owner)');
		dbms_output.put_line('ORDER BY 1,2,3,4;');
-----------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Deferred Indexes from CDB/PDB (Custom User)|
-----------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Deferred Indexes from CDB/PDB');
		dbms_output.put_line('SELECT distinct v.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner,c.TABLE_NAME,c.CONSTRAINT_NAME,c.CONSTRAINT_TYPE,c.DEFERRABLE,c.DEFERRED,c.VALIDATED,c.STATUS,i.INDEX_TYPE,i.INDEX_NAME,i.owner INDEX_OWNER FROM cdb_constraints c,cdb_indexes i,V$CONTAINERS  v ');
		dbms_output.put_line('WHERE i.TABLE_NAME   = c.TABLE_NAME and c.CON_ID=v.CON_ID AND c.con_id =1 AND i.OWNER = c.OWNER AND  c.DEFERRED = ''DEFERRED'' And i.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT distinct v.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",table_owner,c.TABLE_NAME,c.CONSTRAINT_NAME,c.CONSTRAINT_TYPE,c.DEFERRABLE,c.DEFERRED,c.VALIDATED,c.STATUS,i.INDEX_TYPE,i.INDEX_NAME,i.owner INDEX_OWNER FROM cdb_constraints c,cdb_indexes i,V$CONTAINERS  v ');
		dbms_output.put_line('WHERE i.TABLE_NAME   = c.TABLE_NAME and c.CON_ID=v.CON_ID AND c.con_id ='||&v_pdbconid||' AND i.OWNER = c.OWNER AND  c.DEFERRED = ''DEFERRED'' And i.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5;');
------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Big RowSize Tables from CDB/PDB|
------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Big RowSize Tables from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables Defined with Rowsize greater than 2MB in all Schemas');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name, sum(data_length) row_length_over_2MB FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,table_name HAVING sum(data_length) > 2000000 order by 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,table_name, sum(data_length) row_length_over_2MB FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),owner,table_name HAVING sum(data_length) > 2000000 order by 1,2,3;');
--------------------------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables without PK or UK Column more than 1MB from CDB/PDB|
--------------------------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables without PK or UK Column more than 1MB from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables With No Primary Key or Unique Index and Column Lenght more than 1M');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE not exists (select 1  from CDB_constraints ac  where ac.owner = O.owner and ac.table_name = O.table_name and ac.constraint_type IN (''P'',''U'')) and c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,owner,table_name HAVING sum(data_length) > 1000000 order by 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE not exists (select 1  from CDB_constraints ac  where ac.owner = O.owner and ac.table_name = O.table_name and ac.constraint_type IN (''P'',''U'')) and c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,owner,table_name HAVING sum(data_length) > 1000000 order by 1,2,3;');
-----------------------------------------------------
--Prompt Heading U_I_GG OGG:Special Datatypes Columns|
-----------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Special Datatypes Columns from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables With CLOB, BLOB, LONG, NCLOB or LONG RAW Columns in Custom Schemas');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') order by 1,2,3,4,5;');
-------------------------------------------
--Prompt Heading U_I_GG OGG:ROWID Datatypes|
-------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:ROWID Datatypes from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables With ROWID Data_Type');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') AND data_type=''ROWID'';');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') AND data_type in (''CLOB'', ''BLOB'', ''LONG'', ''LONG RAW'', ''NCLOB'') AND data_type=''ROWID'';');
-------------------------------------------------
--Prompt Heading U_I_GG OGG:Unsupported Datatypes|
-------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Unsupported Datatypes from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables With Columns of UNSUPPORTED Datatypes in ALL Schemas of individual container ');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (data_type in (''ORDDICOM'', ''BFILE'', ''TIMEZONE_REGION'', ''BINARY_INTEGER'', ''PLS_INTEGER'', ''UROWID'', ''URITYPE'', ''MLSLABEL'', ''TIMEZONE_ABBR'', ''ANYDATA'', ''ANYDATASET'', ''ANYTYPE'') or data_type like ''INTERVAL%'') order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM cdb_tab_columns O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (data_type in (''ORDDICOM'', ''BFILE'', ''TIMEZONE_REGION'', ''BINARY_INTEGER'', ''PLS_INTEGER'', ''UROWID'', ''URITYPE'', ''MLSLABEL'', ''TIMEZONE_ABBR'', ''ANYDATA'', ''ANYDATASET'', ''ANYTYPE'') or data_type like ''INTERVAL%'') order by 1,2,3,4,5;');
-------------------------------------------
--Prompt Heading U_I_GG OGG:All Unsupported|
-------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:All Unsupported from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Cluster, or Object Tables - ALL UNSUPPORTED - in ALL Schemas of individual container ');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, CLUSTER_NAME, TABLE_TYPE FROM cdb_all_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID'); 
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (cluster_name is NOT NULL or TABLE_TYPE is NOT NULL) order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, CLUSTER_NAME, TABLE_TYPE FROM cdb_all_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (cluster_name is NOT NULL or TABLE_TYPE is NOT NULL) order by 1,2,3,4,5;');
------------------------------------------------------------------
--Prompt Heading U_I_GG OGG:Compressed Tables and Table Partitions|
------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Compressed Tables and Table Partitions from CDB/PDB');
		dbms_output.put_line('Prompt Footnote All tables that have compression enabled (which we do not currently support):');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner TABLE_OWNER, table_name, COMPRESSION from cdb_TABLES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where COMPRESSION = ''ENABLED'' and c.con_id =1 '); 
		dbms_output.put_line('UNION');
		dbms_output.put_line('SELECT C.NAME CONTAINER_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",TABLE_OWNER, TABLE_NAME, COMPRESSION FROM cdb_TAB_PARTITIONS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE COMPRESSION = ''ENABLED'' and c.con_id =1 order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner TABLE_OWNER, table_name, COMPRESSION from cdb_TABLES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where COMPRESSION = ''ENABLED'' and c.con_id ='||&v_pdbconid||' UNION');
		dbms_output.put_line('SELECT C.NAME CONTAINER_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",TABLE_OWNER, TABLE_NAME, COMPRESSION FROM cdb_TAB_PARTITIONS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE COMPRESSION = ''ENABLED'' and c.con_id ='||&v_pdbconid||' order by 1,2,3,4;');
--------------------------------------
--Prompt Heading U_I_GG OGG:IOT Tables|
--------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:IOT Tables from CDB/PDB');
		dbms_output.put_line('Prompt Footnote IOT_TYPE may have values IOT,IOT_OVERFLOW,IOT_MAPPING or NULL');
		dbms_output.put_line('Prompt Footnote IOT (Fully support for Oracle 10GR2 (with or without overflows) using GGS 10.4 and higher) - in All Schemas:');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, IOT_TYPE, TABLE_TYPE FROM cdb_all_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (IOT_TYPE is not null or TABLE_TYPE is NOT NULL) order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, IOT_TYPE, TABLE_TYPE FROM cdb_all_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') AND (IOT_TYPE is not null or TABLE_TYPE is NOT NULL) order by 1,2,3,4,5;');
------------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables with Domain Indexes|
------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Domain Indexes from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables with Domain or Context Indexes');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, index_name, index_type FROM cdb_indexes O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and index_type = ''DOMAIN'' order by 1,2,3,4,5;');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER, TABLE_NAME, index_name, index_type FROM cdb_indexes O JOIN v$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and index_type = ''DOMAIN'' order by 1,2,3,4,5;');
--------------------------------------------------
--Prompt Heading U_I_GG OGG:Constraints and Tables|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Constraints and Tables from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Types of Constraints on the Tables in ALL Schemas of individual container ');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,DECODE(constraint_type,''P'',''PRIMARY KEY'',''U'',''UNIQUE'', ''C'', ''CHECK'', ''R'',''REFERENTIAL'',''Other Constraints'') constraint_type_desc, count(*) total FROM cdb_constraints O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),OWNER,constraint_type order by 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,DECODE(constraint_type,''P'',''PRIMARY KEY'',''U'',''UNIQUE'', ''C'', ''CHECK'', ''R'',''REFERENTIAL'',''Other Constraints'') constraint_type_desc, count(*) total FROM cdb_constraints O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),OWNER,constraint_type order by 1,2,3;');
---------------------------------------------
--Prompt Heading U_I_GG OGG:Cascading Deletes|
---------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Cascading Deletes from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Cascading Deletes on the Tables in ALL Schemas of individual container ');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, constraint_name FROM cdb_constraints O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and constraint_type = ''R'' and delete_rule = ''CASCADE'' order by 1,2,3,4;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, constraint_name FROM cdb_constraints O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and constraint_type = ''R'' and delete_rule = ''CASCADE'' order by 1,2,3,4;');
------------------------------------------------
--Prompt Heading U_I_GG OGG:Tables with Triggers|
------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Tables with Triggers from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Tables Defined with Triggers in ALL Schema of individual container ');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, COUNT(*) trigger_count FROM cdb_triggers O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE  c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,owner, table_name order by 1,2,3,4;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, table_name, COUNT(*) trigger_count FROM cdb_triggers O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE  c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') GROUP BY C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,owner, table_name order by 1,2,3,4;');
-----------------------------------------------
--Prompt Heading U_I_GG OGG:Reverse Key Indexes|
-----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Reverse Key Indexes from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Performance issues - Reverse Key Indexes Defined in ALL Schema:');
		dbms_output.put_line('select	C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,INDEX_NAME,INDEX_TYPE,TABLE_OWNER,TABLE_NAME,	TABLE_TYPE,	UNIQUENESS,	CLUSTERING_FACTOR,	NUM_ROWS,LAST_ANALYZED,	BUFFER_POOL from cdb_indexes O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where index_type = ''NORMAL/REV'' And  c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5,6,7;');
		dbms_output.put_line('select	C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,INDEX_NAME,INDEX_TYPE,TABLE_OWNER,TABLE_NAME,	TABLE_TYPE,	UNIQUENESS,	CLUSTERING_FACTOR,	NUM_ROWS,LAST_ANALYZED,	BUFFER_POOL from cdb_indexes O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where index_type = ''NORMAL/REV'' And  c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5,6,7;');
------------------------------------------------
--Prompt Heading U_I_GG OGG:Sequence Information|
------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Sequence Information from CDB/PDB');
		dbms_output.put_line('Prompt Footnote Sequence numbers - Sequences could be a issue for HA configurations');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",SEQUENCE_OWNER, SEQUENCE_NAME,	 MIN_VALUE, MAX_VALUE, INCREMENT_BY INCR, CYCLE_FLAG CYCLE, ORDER_FLAG "ORDER", CACHE_SIZE, LAST_NUMBER FROM CDB_SEQUENCES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id =1 AND SEQUENCE_OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",SEQUENCE_OWNER, SEQUENCE_NAME,	 MIN_VALUE, MAX_VALUE, INCREMENT_BY INCR, CYCLE_FLAG CYCLE, ORDER_FLAG "ORDER", CACHE_SIZE, LAST_NUMBER FROM CDB_SEQUENCES O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('WHERE c.con_id ='||&v_pdbconid||' AND SEQUENCE_OWNER in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
-------------------------------------------------------
--Prompt Heading U_I_GG OGG:Archivelog Volume per Day|
-------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Archivelog Volume per Day');
		dbms_output.put_line('Prompt Footnote Summary of log volume processed by day for last 7 days:');
		dbms_output.put_line('select to_char(first_time, ''mm/dd'') ArchiveDate,round((sum(BLOCKS*BLOCK_SIZE/1024/1024)),2) LOG_in_MB from sys.v_$archived_log where first_time > sysdate - 7 group by to_char(first_time, ''mm/dd'') order by to_char(first_time, ''mm/dd'');');
--------------------------------------------------
--Prompt Heading U_I_GG OGG:Redo Log Information|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Redo Log Information');
		dbms_output.put_line('select group#, THREAD#, SEQUENCE#, BYTES/1024/1024, MEMBERS, ARCHIVED, STATUS, FIRST_CHANGE#, to_char(FIRST_TIME, ''DD-Mon-YYYY HH24:Mi:SS'') First_time  from sys.v_$log order by group#;');
		dbms_output.put_line('select group#, status, member, type from sys.v_$logfile order by group#;');
--------------------------------------------------
--Prompt Heading U_I_GG OGG:Materialized View List|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Materialized View List from CDB/PDB');
		dbms_output.put_line('Prompt Footnote List will be used to Exclude the MView from the Replication:');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, object_name, object_type, status from cdb_objects O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where object_type=''MATERIALIZED VIEW'' and c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, object_name, object_type, status from cdb_objects O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where object_type=''MATERIALIZED VIEW'' and c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
-------------------------------------------------
--Prompt Heading U_I_GG DB:Transportable Platform|
-------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Transportable Platform');
		dbms_output.put_line('COLUMN PLATFORM_NAME FORMAT A32');
		dbms_output.put_line('SELECT * FROM sys.v_$transportable_platform;');
-----------------------------------------------
--Prompt Heading U_I_GG DB:Transport Violations|
-----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Transport Violations');
		dbms_output.put_line('select * from sys.transport_set_violations;');
----------------------------------------
--Prompt Heading U_I_GG DB:Database Home|
----------------------------------------
		-- dbms_output.put_line('Prompt Heading U_I_GG DB:Database Home');
		-- dbms_output.put_line('var Oracle_Home varchar2(100);');
		-- dbms_output.put_line('begin');
		-- dbms_output.put_line('sys.dbms_system.get_env(''ORACLE_HOME'', :Oracle_Home);');
		-- dbms_output.put_line('end;');
		-- dbms_output.put_line('/');
		-- dbms_output.put_line('Print :Oracle_home');	
		
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Home');
		dbms_output.put_line('select SYS_CONTEXT (''USERENV'',''ORACLE_HOME'') from dual;');
		
----------------------------------------------------------
--Prompt Heading U_I_GG DB:Software Version and PSU Info_1|
----------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_1');
		dbms_output.put_line('SELECT * FROM sys.v_$version;');
----------------------------------------------------------
--Prompt Heading U_I_GG DB:Software Version and PSU Info_2|
----------------------------------------------------------
	IF ( gv_slab in ('12c','13') ) THEN
		dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_2 from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",ACTION_TIME,ACTION,PATCH_ID,DESCRIPTION FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where action=''APPLY'' and c.con_id =1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",ACTION_TIME,ACTION,PATCH_ID,DESCRIPTION FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where action=''APPLY'' and c.con_id ='||&v_pdbconid||';');
	ELSIF ( gv_slab in ('18','19') ) THEN
		dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_2 from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",ACTION_TIME,ACTION,TARGET_VERSION,PATCH_ID,PATCH_TYPE,DESCRIPTION FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where action=''APPLY'' and c.con_id =1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",ACTION_TIME,ACTION,TARGET_VERSION,PATCH_ID,PATCH_TYPE,DESCRIPTION FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where action=''APPLY'' and c.con_id ='||&v_pdbconid||';');
	END IF;	
----------------------------------------------------------
--Prompt Heading U_I_GG DB:Software Version and PSU Info_3|
----------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Software Version and PSU Info_3 from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",PATCH_ID,PATCH_UID,STATUS,LOGFILE FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where status=''SUCCESS'' and c.con_id =1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",PATCH_ID,PATCH_UID,STATUS,LOGFILE FROM CDB_REGISTRY_SQLPATCH O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where status=''SUCCESS'' and c.con_id ='||&v_pdbconid||';');
-----------------------------------------
--Prompt Heading U_I_GG DB:Auditing Check|
-----------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Auditing Check');
		dbms_output.put_line('show parameter audit');
-----------------------------------------
--Prompt Heading U_I_GG DB:Cluster Check|
-----------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Cluster Check');
		dbms_output.put_line('show parameter cluster_database');
----------------------------------------------
--Prompt Heading U_I_GG DB:Database Components|
----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Components from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",COMP_ID,COMP_NAME,VERSION,STATUS,MODIFIED from cdb_registry  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",COMP_ID,COMP_NAME,VERSION,STATUS,MODIFIED from cdb_registry  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' order by 1,2,3,4;');
--------------------------------------------------------
--Prompt Heading U_I_GG DB:Database Options and Features|
--------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Options and Features');
		dbms_output.put_line('select * from sys.v_$option');
		dbms_output.put_line('where VALUE = ''TRUE'';');
--------------------------------------------------
--Prompt Heading U_I_GG DB:Database Feature Usage|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Feature Usage from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",u1.name,u1.detected_usages FROM cdb_feature_usage_statistics u1 JOIN V$CONTAINERS  C ON u1.CON_ID=C.CON_ID WHERE  u1.version = (SELECT MAX(u2.version) FROM cdb_feature_usage_statistics u2 WHERE  u2.name = u1.name) AND u1.detected_usages <> 0 and c.con_id =1 ORDER BY 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",u1.name,u1.detected_usages FROM   cdb_feature_usage_statistics u1 JOIN V$CONTAINERS  C ON u1.CON_ID=C.CON_ID WHERE  u1.version = (SELECT MAX(u2.version) FROM cdb_feature_usage_statistics u2 WHERE  u2.name = u1.name) AND u1.detected_usages <> 0 and c.con_id ='||&v_pdbconid||' ORDER BY 1,2,3;');
--------------------------------------------------
--Prompt Heading U_I_GG DB:Database Wallet Details|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading DB:Database Encrypted - Database Wallet Details from CDB/PDB');
		dbms_output.put_line('SELECT decode(CON_ID,0,''CDB'',1,''CDB$ROOT'') CDB_NAME,decode(CON_ID,0,''CDB-''||CON_ID,1,''CDB-''||CON_ID) "TYPE-ID",WRL_TYPE,wrl_parameter,status,wallet_type,wallet_order,fully_backed_up from v$encryption_wallet where status=''OPEN'' and con_id <2 ORDER BY 1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",WRL_TYPE,wrl_parameter,status,wallet_type,wallet_order,fully_backed_up from v$encryption_wallet O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE  status=''OPEN'' and c.con_id ='||&v_pdbconid||' ORDER BY 1 ;');
----------------------------------------------
--Prompt Heading U_I_GG DB:Database Parameters|
----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Parameters');
		dbms_output.put_line('select name parameter_name,value from sys.v_$parameter where isdefault=''FALSE'' order by name;');
---------------------------------------------------------
--Prompt Heading U_I_GG DB:Database Modifiable Parameters|
---------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Modifiable Parameters from CDB/PDB');
		dbms_output.put_line('SELECT decode(CON_ID,0,''CDB'',1,''CDB$ROOT'') CDB_NAME,decode(CON_ID,0,''CDB-''||CON_ID,1,''CDB-''||CON_ID) "TYPE-ID",name parameter_name, value,DISPLAY_VALUE,DEFAULT_VALUE FROM v$system_parameter WHERE  ispdb_modifiable = ''TRUE'' and con_id <2 ORDER BY name;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",o.name parameter_name, value,DISPLAY_VALUE,DEFAULT_VALUE FROM v$system_parameter O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID WHERE  ispdb_modifiable = ''TRUE'' and c.con_id ='||&v_pdbconid||' ORDER BY 3 ;');
----------------------------------------------
--Prompt Heading U_I_GG DB:Database Properties|
----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Properties');
		dbms_output.put_line('select * from database_properties;');
----------------------------------------
--Prompt Heading U_I_GG DB:Database Size|
----------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Size ');
		dbms_output.put_line('select * from (select database_size, dbs_data_size,Archive_logs_size, rollback_segs_size,temp_ts_size,free_space_size ,size_units');
		dbms_output.put_line('from ');
		dbms_output.put_line('(select round(a.Database_Size_GB,2) database_size');
		dbms_output.put_line(',case when round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2)<0 then 1 else round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2) end dbs_data_size');
		dbms_output.put_line(',round(b.Archive_logs_GB,2)  Archive_logs_size,round(c.rollback_segs_GB,2) rollback_segs_size,round(d.TEMP_TS_GB,2)  temp_ts_size,round(e.free_space_GB,2) free_space_size,''all units are in GB'' size_units');
		dbms_output.put_line('from');
		dbms_output.put_line('(select sum(bytes/1024/1024/1024) Database_Size_GB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
		dbms_output.put_line('(select sum(bytes/1024/1024/1024) Archive_logs_GB from sys.v_$log) b,');
		dbms_output.put_line('(select sum(bytes/1024/1024/1024) rollback_segs_GB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
		dbms_output.put_line('(select sum(bytes/1024/1024/1024) TEMP_TS_GB from dba_temp_files) d,');
		dbms_output.put_line('(select sum(bytes/1024/1024/1024) free_space_GB from dba_free_space) e');
		dbms_output.put_line('union');
		dbms_output.put_line('select round(a.Database_Size_MB,2) database_size');
		dbms_output.put_line(',case when round(( a.Database_Size_MB - (b.Archive_logs_MB + c.rollback_segs_MB + d.TEMP_TS_MB + e.free_space_MB)),2)<0 then 1 else round(( a.Database_Size_MB - (b.Archive_logs_MB + c.rollback_segs_MB + d.TEMP_TS_MB + e.free_space_MB)),2) end  dbs_data_size');
		dbms_output.put_line(',round(b.Archive_logs_MB,2)  Archive_logs_size,round(c.rollback_segs_MB,2) rollback_segs_size,round(d.TEMP_TS_MB,2) temp_ts_size,round(e.free_space_MB,2) free_space_size,''all units are MB'' size_units');
		dbms_output.put_line('from');
		dbms_output.put_line('(select sum(bytes/1024/1024) Database_Size_MB from ( select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
		dbms_output.put_line('(select sum(bytes/1024/1024) Archive_logs_MB from sys.v_$log) b,');
		dbms_output.put_line('(select sum(bytes/1024/1024) rollback_segs_MB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
		dbms_output.put_line('(select sum(bytes/1024/1024) TEMP_TS_MB from dba_temp_files) d,');
		dbms_output.put_line('(select sum(bytes/1024/1024) free_space_MB from dba_free_space)e');
		dbms_output.put_line('union');
		dbms_output.put_line('select round(a.Database_Size_KB,2) database_size');
		dbms_output.put_line(',round(( a.Database_Size_KB- b.Archive_logs_KB-c.rollback_segs_KB-d.TEMP_TS_KB-e.free_space_KB),2) dbs_data_size');
		dbms_output.put_line(',round(b.Archive_logs_KB,2)  Archive_logs_size,round(c.rollback_segs_KB,2) rollback_segs_size,round(d.TEMP_TS_KB,2) temp_ts_size,round(e.free_space_KB,2) free_space_size,''all units are in KB'' size_units');
		dbms_output.put_line('from   ');
		dbms_output.put_line('(select sum(bytes/1024) Database_Size_KB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
		dbms_output.put_line('(select sum(bytes/1024) Archive_logs_KB from sys.v_$log) b,');
		dbms_output.put_line('(select sum(bytes/1024) rollback_segs_KB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM''))) c,');
		dbms_output.put_line('(select sum(bytes/1024) TEMP_TS_KB from dba_temp_files) d,');
		dbms_output.put_line('(select sum(bytes/1024) free_space_KB from dba_free_space) e)');
		dbms_output.put_line('where 0 not in (dbs_data_size,Archive_logs_size,rollback_segs_size,temp_ts_size,free_space_size)');
		dbms_output.put_line('order by database_size');
		dbms_output.put_line(') where rownum < 3;');
---------------------------------------------
--Prompt Heading U_I_GG DB:Tablespace Details|
---------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Tablespace Details from CDB/PDB');
		dbms_output.put_line('select c.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",df.tablespace_name "Tablespace",d.extent_management,d.segment_space_management,auto_extension,d.status,d.BLOCK_SIZE,');
		dbms_output.put_line('nvl(totalusedspace,0) "Used MB",(df.totalspace - nvl(tu.totalusedspace,0)) "Free MB",df.totalspace "Total MB",round(100 * ( (df.totalspace - nvl(tu.totalusedspace,0))/ df.totalspace),2) "Pct. Free",');
		dbms_output.put_line('nvl(fs.free_space,0) extendable_free_space, round(maxspace,2) maxspace');
		dbms_output.put_line('from (select con_id,tablespace_name,round(sum(bytes) / 1048576) TotalSpace, sum(maxbytes)/1024/1024 maxspace,decode(sum(decode(autoextensible,''YES'',1,0)),0,''NO'',''YES'') auto_extension from cdb_data_files group by con_id,tablespace_name) df,');
		dbms_output.put_line('(select con_id,tablespace_name,round(sum(bytes)/(1024*1024)) totalusedspace from cdb_segments group by con_id,tablespace_name) tu,');
		dbms_output.put_line('(select con_id,tablespace_name, round(sum(bytes)/1024/1024 ,2) as free_space from cdb_free_space group by con_id,tablespace_name) fs, cdb_tablespaces d, v$CONTAINERS  c');
		dbms_output.put_line('Where  (d.con_id=df.con_id and d.tablespace_name = df.tablespace_name(+))');
		dbms_output.put_line('and    (d.con_id=tu.con_id and d.tablespace_name = tu.tablespace_name(+))');
		dbms_output.put_line('and    (d.con_id=fs.con_id and d.tablespace_name = fs.tablespace_name(+))');
		dbms_output.put_line('and    d.CON_ID=c.CON_ID and c.con_id =1');
		dbms_output.put_line('and    df.tablespace_name is not null');
		dbms_output.put_line('ORDER BY "Pct. Free";');
		dbms_output.put_line('select c.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",df.tablespace_name "Tablespace",d.extent_management,d.segment_space_management,auto_extension,d.status,d.BLOCK_SIZE,');
		dbms_output.put_line('nvl(totalusedspace,0) "Used MB",(df.totalspace - nvl(tu.totalusedspace,0)) "Free MB",df.totalspace "Total MB",round(100 * ( (df.totalspace - nvl(tu.totalusedspace,0))/ df.totalspace),2) "Pct. Free",');
		dbms_output.put_line('nvl(fs.free_space,0) extendable_free_space, round(maxspace,2) maxspace');
		dbms_output.put_line('from (select con_id,tablespace_name,round(sum(bytes) / 1048576) TotalSpace, sum(maxbytes)/1024/1024 maxspace,decode(sum(decode(autoextensible,''YES'',1,0)),0,''NO'',''YES'') auto_extension from cdb_data_files group by con_id,tablespace_name) df,');
		dbms_output.put_line('(select con_id,tablespace_name,round(sum(bytes)/(1024*1024)) totalusedspace from cdb_segments group by con_id,tablespace_name) tu,');
		dbms_output.put_line('(select con_id,tablespace_name, round(sum(bytes)/1024/1024 ,2) as free_space from cdb_free_space group by con_id,tablespace_name) fs, cdb_tablespaces d, v$CONTAINERS  c');
		dbms_output.put_line('Where  (d.con_id=df.con_id and d.tablespace_name = df.tablespace_name(+))');
		dbms_output.put_line('and    (d.con_id=tu.con_id and d.tablespace_name = tu.tablespace_name(+))');
		dbms_output.put_line('and    (d.con_id=fs.con_id and d.tablespace_name = fs.tablespace_name(+))');
		dbms_output.put_line('and    d.CON_ID=c.CON_ID and c.con_id ='||&v_pdbconid||'');
		dbms_output.put_line('and    df.tablespace_name is not null');
		dbms_output.put_line('ORDER BY "Pct. Free";	');
------------------------------------
--Prompt Heading U_I_GG DB:Datafiles|
------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles from CDB/PDB');
		dbms_output.put_line('select  v.NAME CDB_NAME, decode(a.CON_ID,1,''CDB-''||a.CON_ID,''PDB-''||a.CON_ID) "TYPE-ID",a.TABLESPACE_NAME,a.FILE_ID,a.FILE_NAME,a.BYTES/1024/1024 BYTES_in_MB,a.AUTOEXTENSIBLE,a.MAXBYTES/1024/1024/1024 MAX_BYTES_IN_GB,b.enabled,to_char(b.CREATION_TIME,''DD_Mon_YYYY HH24:MI:SS'') CREATION_TIME ');
		dbms_output.put_line('from cdb_data_files a,sys.v_$datafile b,V$CONTAINERS  v where a.file_name =b.name and a.CON_ID=v.CON_ID and a.con_id =1 order by 1,2,3;');
		dbms_output.put_line('select  v.NAME PDB_NAME, decode(a.CON_ID,1,''CDB-''||a.CON_ID,''PDB-''||a.CON_ID) "TYPE-ID",a.TABLESPACE_NAME,a.FILE_ID,a.FILE_NAME,a.BYTES/1024/1024 BYTES_in_MB,a.AUTOEXTENSIBLE,a.MAXBYTES/1024/1024/1024 MAX_BYTES_IN_GB,b.enabled,to_char(b.CREATION_TIME,''DD_Mon_YYYY HH24:MI:SS'') CREATION_TIME');
		dbms_output.put_line('from cdb_data_files a,sys.v_$datafile b,V$CONTAINERS  v where a.file_name =b.name and a.CON_ID=v.CON_ID and a.con_id ='||&v_pdbconid||' order by 1,2,3;');
------------------------------------
--Prompt Heading U_I_GG DB:Tempfiles|
------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles - Tempfiles from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID", TABLESPACE_NAME,sum(bytes/1024/1024) TEMP_USED_MB,sum(MAXBYTES)/1024/1024/1024 Max_Size_GB from cdb_temp_files O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID Where c.con_id =1 group by C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) , TABLESPACE_NAME;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID", TABLESPACE_NAME,sum(bytes/1024/1024) TEMP_USED_MB,sum(MAXBYTES)/1024/1024/1024 Max_Size_GB from cdb_temp_files O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID Where c.con_id ='||&v_pdbconid||' group by C.NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) , TABLESPACE_NAME;');
----------------------------------------------------------
--Prompt Heading U_I_GG DB:Database ASM Disk Group Details|
----------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database ASM Disk Details from CDB/PDB');
		dbms_output.put_line('SELECT decode(CON_ID,0,''CDB'',1,''CDB$ROOT'') CDB_NAME,decode(CON_ID,0,''CDB-''||CON_ID,1,''CDB-''||CON_ID) "TYPE-ID",name group_name, sector_size sector_size, block_size block_size, allocation_unit_size allocation_unit_size, state state, type type, total_mb total_mb, (total_mb - free_mb) used_mb, ROUND((1- (free_mb / decode(total_mb,0,1)))*100, 2)  pct_used');
		dbms_output.put_line('FROM   v$asm_diskgroup where con_id <2 ORDER BY name;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME,decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",o.name group_name, o.sector_size sector_size, o.block_size block_size, o.allocation_unit_size allocation_unit_size, o.state state, o.type type, o.total_mb total_mb, (total_mb - free_mb) used_mb, ROUND((1- (free_mb / decode(total_mb,0,1)))*100, 2)  pct_used');
		dbms_output.put_line('FROM   v$asm_diskgroup o JOIN V$CONTAINERS  C ON o.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' ORDER BY C.NAME;');
----------------------------------------
--Prompt Heading U_I_GG DB:Recovery file|
----------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Recovery file');
		dbms_output.put_line('select FILE#, ONLINE_STATUS from sys.v_$recover_file order by 1;');
---------------------------------------------------
--Prompt Heading U_I_GG DB:Datafiles in Backup Mode|
---------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Datafiles in Backup Mode');
		dbms_output.put_line('select a.file#,b.file_name, a.status, a.change#,to_char(a.time, ''dd-Mon-YYYY HH24:Mi:SS'') time from sys.v_$backup a,cdb_data_files b where a.file#=b.file_id and a.status <> ''NOT ACTIVE'' order by a.file#;');
--------------------------------------------------
--Prompt Heading U_I_GG DB:Directories Information|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Directories Information from CDB/PDB');
		dbms_output.put_line('select '''' CDB_NAME,'''' "TYPE-ID", '''' owner,name directory_name, VALUE directory_path FROM sys.v_$parameter WHERE NAME=''utl_file_dir''');
		dbms_output.put_line('union all');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, directory_name, directory_path FROM cdb_directories  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 order by 1,2,3;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, directory_name, directory_path FROM cdb_directories  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' order by 1,2,3;');
-------------------------------------------------------
--Prompt Heading U_I_GG DB:Scheduled Jobs_From_CDB_JOBS|
-------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_CDB_JOBS (CDB/PDB)');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",JOB, SUBSTR(WHAT,1,35) "Description", NEXT_DATE, NEXT_SEC, BROKEN FROM cdb_JOBS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",JOB, SUBSTR(WHAT,1,35) "Description", NEXT_DATE, NEXT_SEC, BROKEN FROM cdb_JOBS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||';');
----------------------------------------------------------------------
--Prompt Heading U_I_GG DB:Scheduled Jobs_From_CDB_SCHEDULER_SCHEDULES|
----------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_CDB_SCHEDULER_SCHEDULES (CDB/PDB)');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, schedule_name,START_DATE from cdb_scheduler_schedules O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, schedule_name,START_DATE from cdb_scheduler_schedules O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
-----------------------------------------------------------------
--Prompt Heading U_I_GG DB:Scheduled Jobs_From_DBA_SCHEDULER_JOBS|
-----------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Scheduled Jobs_From_CDB_SCHEDULER_SCHEDULES (CDB/PDB)');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,JOB_NAME,START_DATE,END_DATE,STATE,LAST_START_DATE,LAST_RUN_DURATION,NEXT_RUN_DATE from cdb_DBA_SCHEDULER_JOBS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,JOB_NAME,START_DATE,END_DATE,STATE,LAST_START_DATE,LAST_RUN_DURATION,NEXT_RUN_DATE from cdb_DBA_SCHEDULER_JOBS O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3;');
-----------------------------------------');
--Prompt Heading U_I_GG DB:Database Users|')'
-----------------------------------------');
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Users from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",''Regular'' USER_TYPE,USERNAME SEEDED_USER,account_status,to_char(created, ''DD-Mon-YYYY HH24:Mi:SS'') CREATED,to_char(EXPIRY_DATE, ''DD-Mon-YYYY HH24:Mi:SS'') EXPIRY_DATE,PROFILE,PASSWORD_VERSIONS PVERSION,DEFAULT_TABLESPACE,TEMPORARY_TABLESPACE from cdb_users  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('Where c.con_id =1 and username in (select username from cdb_users where oracle_maintained=''N'');');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",''Regular'' USER_TYPE,USERNAME CUSTOM_USER,account_status,to_char(created, ''DD-Mon-YYYY HH24:Mi:SS'') CREATED,to_char(EXPIRY_DATE, ''DD-Mon-YYYY HH24:Mi:SS'') EXPIRY_DATE,PROFILE,PASSWORD_VERSIONS PVERSION,DEFAULT_TABLESPACE,TEMPORARY_TABLESPACE from cdb_users  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('Where c.con_id ='||&v_pdbconid||' and username in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||');');
-------------------------------------------------
--Prompt Heading U_I_GG DB:Index Organised Tables|
-------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Index Organised Tables from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,table_name, iot_type, iot_name FROM cdb_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and IOT_NAME IS NOT NULL ORDER BY 1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,table_name, iot_type, iot_name FROM cdb_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') and IOT_NAME IS NOT NULL ORDER BY 1;');
--------------------------------------------
--Prompt Heading U_I_GG DB: External Tables|
--------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:External Tables from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,table_name, type_owner,type_name,default_directory_name FROM cdb_external_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('ORDER BY 1;');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,table_name, type_owner,type_name,default_directory_name FROM cdb_external_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||')');
		dbms_output.put_line('ORDER BY 1;');
------------------------------------------
--Prompt Heading U_I_GG DB:Invalid Objects|
------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Invalid Objects from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''||object_name Object_name,object_type,status from CDB_objects O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where status<>''VALID'' and c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||');');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''||object_name Object_name,object_type,status from CDB_objects O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where status<>''VALID'' and c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||');');
---------------------------------------
--Prompt Heading U_I_GG DB:DB link Info|
---------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:DB link Info from CDB/PDB');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,db_link,username,host,created FROM CDB_db_links O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 ORDER BY 1,2,3,4;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner,db_link,username,host,created FROM CDB_db_links O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' ORDER BY 1,2,3,4;');
-----------------------------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:List of Policy Functions / Objects|
-----------------------------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:List of Policy Functions / Objects from CDB/PDB');
		dbms_output.put_line('PROMPT Footnote Identify all policy functions, the policy function owner , associated object with owner');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",pf_owner function_owner, function, policy_name, object_owner policy_owner, object_name, package, policy_group');
		dbms_output.put_line('FROM CDB_policies  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where pf_owner <> ''XDB'' and c.con_id =1 ORDER BY 1, 2,3, 4, 5, 6, 7, 8, 9 ;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",pf_owner function_owner, function, policy_name, object_owner policy_owner, object_name, package, policy_group');
		dbms_output.put_line('FROM CDB_policies  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where pf_owner <> ''XDB'' and c.con_id ='||&v_pdbconid||' ORDER BY 1, 2,3, 4, 5, 6, 7, 8, 9 ;');
-------------------------------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:Owner wise COUNT of Policy Functions|
-------------------------------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Owner wise COUNT of Policy Functions from CDB/PDB');
		dbms_output.put_line('PROMPT Footnote Identify all the policy function owners and the number of policy functions they own in the database.');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",pf_owner vpd_owner_name, count(1) Number_of_VPD_Owners FROM CDB_policies  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,pf_owner;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",pf_owner vpd_owner_name, count(1) Number_of_VPD_Owners FROM CDB_policies  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) ,pf_owner;');
----------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:Policy Contexts|
----------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Policy Contexts from CDB/PDB');
		dbms_output.put_line('PROMPT Footnote Identify all policy contexts');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, namespace, attribute FROM CDB_POLICY_CONTEXTS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 ORDER BY 1,2,3, 4, 5, 6;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, namespace, attribute FROM CDB_POLICY_CONTEXTS  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' ORDER BY 1,2,3, 4, 5, 6;');
--------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:Policy Groups|
--------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Policy Groups from CDB/PDB');
		dbms_output.put_line('PROMPT Footnote Identify all the policy Groups in the database');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, policy_group FROM CDB_policy_groups  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, policy_group FROM CDB_policy_groups  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||';');
---------------------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:Security Relevant Columns|
---------------------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:Security Relevant Columns from CDB/PDB');
		dbms_output.put_line('PROMPT Footnote Identify security Relevant columns of all VPD policies in the database');
		dbms_output.put_line('SELECT C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, policy_group, policy_name, sec_rel_column, column_option FROM CDB_SEC_RELEVANT_COLs  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id =1 ORDER BY 1,2,3, 4, 5, 6, 7, 8 ;');
		dbms_output.put_line('SELECT C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",object_owner, object_name, policy_group, policy_name, sec_rel_column, column_option FROM CDB_SEC_RELEVANT_COLs  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where c.con_id ='||&v_pdbconid||' ORDER BY 1,2,3, 4, 5, 6, 7, 8 ;');
------------------------------------------------------------------
--PROMPT Heading U_I_GG DB:VPD:DB Users with Exempt Access Policy|
------------------------------------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:VPD:DB Users with Exempt Access Policy from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",grantee,privilege from CDB_sys_privs  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where privilege=''EXEMPT ACCESS POLICY'' and c.con_id =1;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",grantee,privilege from CDB_sys_privs  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID where privilege=''EXEMPT ACCESS POLICY'' and c.con_id ='||&v_pdbconid||';');
-------------------------------------------------------
--Prompt Heading U_I_GG DB:Database Advanced_Queue_Info|
-------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Advanced_Queue_Info from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",q.owner||''.''||q.name QUEUE_NAME,q.queue_type,q.enqueue_enabled, q.dequeue_enabled,q.retention,q.network_name, s.waiting,s.ready,s.expired,s.total_wait,s.average_wait from CDB_queues q,sys.v_$aq s ,V$CONTAINERS  C ');
		dbms_output.put_line('where s.qid=q.qid AND q.CON_ID=C.CON_ID and c.con_id =1 AND q.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4 ;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",q.owner||''.''||q.name QUEUE_NAME,q.queue_type,q.retention,q.network_name, s.waiting,s.ready,s.expired,s.total_wait,s.average_wait from CDB_queues q,sys.v_$aq s ,V$CONTAINERS  C ');
		dbms_output.put_line('where s.qid=q.qid AND q.CON_ID=C.CON_ID and c.con_id ='||&v_pdbconid||' AND q.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4 ;');
---------------------------------------------------------------
--Prompt Heading U_I_GG DB:Database Advanced_Queue_Tables_Info|
---------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database Advanced_Queue_Tables_Info from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",q.owner||''.''||q.queue_table queue_table_name, num_rows, blocks,last_analyzed, chain_cnt from cdb_queue_tables q, cdb_tables t ,V$CONTAINERS  C');
		dbms_output.put_line('where c.con_id =1 AND q.owner = t.owner and q.con_id=c.con_id and q.queue_table = t.table_name and q.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",q.owner||''.''||q.queue_table queue_table_name, num_rows, blocks,last_analyzed, chain_cnt from cdb_queue_tables q, cdb_tables t ,V$CONTAINERS  C');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND q.owner = t.owner and q.con_id=c.con_id and q.queue_table = t.table_name and q.owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
--------------------------------------------------
--Prompt Heading U_I_GG DB:Database MV_Views_Info|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_Views_Info from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, mview_name, container_name, updatable, last_refresh_date, compile_state, refresh_mode, master_link from cdb_mviews  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner, mview_name, container_name, updatable, last_refresh_date , compile_state, refresh_mode, master_link from cdb_mviews  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4;');
-------------------------------------
--PROMPT Heading U_I_GG DB:XML_Types|
-------------------------------------
		dbms_output.put_line('PROMPT Heading U_I_GG DB:XML_Types from CDB/PDB');
		dbms_output.put_line('select distinct C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",p.tablespace_name from cdb_tablespaces p,dba_xml_tables x, cdb_users u, cdb_all_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where p.CON_ID=c.CON_ID and c.con_id =1 and t.table_name=x.table_name and t.tablespace_name=p.tablespace_name and x.owner=u.username;');
		dbms_output.put_line('select distinct C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",p.tablespace_name from cdb_tablespaces p,dba_xml_tables x, cdb_users u, cdb_all_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where p.CON_ID=c.CON_ID and c.con_id ='||&v_pdbconid||' and t.table_name=x.table_name and t.tablespace_name=p.tablespace_name and x.owner=u.username;');
-----------------------------------------------
--Prompt Heading U_I_GG DB:Database XML_Tables|
-----------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Tables from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''||table_name table_name, xmlschema, element_name, storage_type from cdb_xml_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3 ;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''||table_name table_name, xmlschema, element_name, storage_type from cdb_xml_tables O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3 ;');
-----------------------------------------------------
--Prompt Heading U_I_GG DB:Database XML_Table_Columns|
-----------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Columns from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''|| table_name table_name, column_name, xmlschema, element_name, storage_type from cdb_xml_tab_cols  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4 ;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",owner||''.''|| table_name table_name, column_name, xmlschema, element_name, storage_type from cdb_xml_tab_cols  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4 ;');
-----------------------------------------------------
--Prompt Heading U_I_GG DB:Database XML_Table_Indexes|
-----------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Indexes from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",index_owner, table_name, index_name, type, index_type, async, stale from cdb_xml_indexes  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id =1 AND index_owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5 ;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",index_owner, table_name, index_name, type, index_type, async, stale from cdb_xml_indexes  O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND index_owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5 ;');
--------------------------------------------------
--Prompt Heading U_I_GG DB:Database XML_Table_Info|
--------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database XML_Table_Info from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner||''.''||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where (t.last_analyzed is null or t.blocks > 1000 or t.num_rows > 5000) and l.CON_ID=C.CON_ID and c.con_id =1 and l.log_table = t.table_name order by 1,2,3;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner||''.''||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where (t.last_analyzed is null or t.blocks > 1000 or t.num_rows > 5000) and l.CON_ID=C.CON_ID and c.con_id ='||&v_pdbconid||' and l.log_table = t.table_name order by 1,2,3;');
---------------------------------------------------------------
--Prompt Heading U_I_GG DB:Database MV_logs without statistics|
---------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs without statistics from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner, count(*) from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where t.last_analyzed is null and c.con_id =1 and l.CON_ID=C.CON_ID and l.log_table = t.table_name group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),l.log_owner order by 1,2,3;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner, count(*) from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where t.last_analyzed is null and c.con_id ='||&v_pdbconid||' and l.CON_ID=C.CON_ID and l.log_table = t.table_name group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),l.log_owner order by 1,2,3;');
----------------------------------------------------------------------
--Prompt Heading U_I_GG DB:Database MV_logs_indexes without statistics|
----------------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs_indexes without statistics from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner, count(*) Count from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c');
		dbms_output.put_line('where t.last_analyzed is null and c.con_id =1 and l.log_table = t.table_name and l.CON_ID=C.CON_ID and (l.log_owner, l.master) in (select table_owner, table_name from all_indexes)');
		dbms_output.put_line('group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),l.log_owner order by 1,2,3;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner, count(*) Count from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c');
		dbms_output.put_line('where t.last_analyzed is null and c.con_id ='||&v_pdbconid||' and l.log_table = t.table_name and l.CON_ID=C.CON_ID and (l.log_owner, l.master) in (select table_owner, table_name from all_indexes)');
		dbms_output.put_line('group by C.NAME , decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID),l.log_owner order by 1,2,3;');
------------------------------------------------------------
--Prompt Heading U_I_GG DB:Database MV_logs bigger logs only|
------------------------------------------------------------
		dbms_output.put_line('Prompt Heading U_I_GG DB:Database MV_logs bigger logs only from CDB/PDB');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner||''.''||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c ');
		dbms_output.put_line('where      t.num_rows > 100000 and c.con_id =1 and l.CON_ID=C.CON_ID and l.master = t.table_name order by t.num_rows desc;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",l.log_owner||''.''||l.master name, l.log_table, t.last_analyzed, t.blocks, t.num_rows from cdb_mview_logs l, cdb_tables t,V$CONTAINERS c');
		dbms_output.put_line('where      t.num_rows > 100000 and c.con_id ='||&v_pdbconid||' and l.CON_ID=C.CON_ID and l.master = t.table_name order by t.num_rows desc;');
--PROMPT Heading U_I_GG DB:Database MV_log data accumulation info
--alter session set nls_date_format = 'DD-Mon-YYYY';
-----------------------------------------------------
--Prompt Heading U_I_GG OGG:Redo Log Switch History|
-----------------------------------------------------
		dbms_output.put_line('alter session set nls_date_format = ''DD-Mon-YYYY'';');
		dbms_output.put_line('Prompt Heading U_I_GG OGG:Redo Log Switch History');
		dbms_output.put_line('Prompt Footnote Average is given in last line');
        dbms_output.put_line('SELECT  to_char(trunc(first_time),''DD-Mon-YY'') "Date",to_char(first_time, ''Dy'') "Day",count(1) Total,');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''00'',1,0)) "h0",SUM(decode(to_char(first_time, ''hh24''),''01'',1,0)) "h1",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''02'',1,0)) "h2",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''03'',1,0)) "h3",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''04'',1,0)) "h4",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''05'',1,0)) "h5",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''06'',1,0)) "h6",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''07'',1,0)) "h7",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''08'',1,0)) "h8",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''09'',1,0)) "h9",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''10'',1,0)) "h10",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''11'',1,0)) "h11",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''12'',1,0)) "h12",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''13'',1,0)) "h13",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''14'',1,0)) "h14",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''15'',1,0)) "h15",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''16'',1,0)) "h16",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''17'',1,0)) "h17",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''18'',1,0)) "h18",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''19'',1,0)) "h19",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''20'',1,0)) "h20",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''21'',1,0)) "h21",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''22'',1,0)) "h22",');
        dbms_output.put_line('SUM(decode(to_char(first_time, ''hh24''),''23'',1,0)) "h23"');
        dbms_output.put_line('from v$log_history ');
        dbms_output.put_line('where first_time > sysdate - 30');
        dbms_output.put_line('group by trunc(first_time), to_char(first_time, ''Dy'')');
        dbms_output.put_line('order by trunc(first_time);');

-- Query added on 21/06/2021 	
---------------------------------------------------------
--Prompt Heading DB:Database Synonyms for Remote Objects |
---------------------------------------------------------
		dbms_output.put_line('Prompt Heading DB:Database Synonyms for Remote Objects');
		dbms_output.put_line('Prompt Footnote Database Synonyms for Remote Objects Information ');
		dbms_output.put_line('select C.NAME CDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,SYNONYM_NAME,TABLE_OWNER,TABLE_NAME,DB_LINK from cdb_synonyms O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID');
		dbms_output.put_line('where c.con_id =1 AND owner in (select username from cdb_users where username not in '||owner_blacklist||') order by 1,2,3,4,5 ;');
		dbms_output.put_line('select C.NAME PDB_NAME, decode(C.CON_ID,1,''CDB-''||C.CON_ID,''PDB-''||C.CON_ID) "TYPE-ID",OWNER,SYNONYM_NAME,TABLE_OWNER,TABLE_NAME,DB_LINK from cdb_synonyms O JOIN V$CONTAINERS  C ON O.CON_ID=C.CON_ID ');
		dbms_output.put_line('where c.con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') order by 1,2,3,4,5 ;');	  

--------------------------------------------
--Prompt Heading DB:Database Corrupt Blocks |
--------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database Corrupt Blocks');
      dbms_output.put_line('select count(*) "Corrupt Database Blocks" ');
	  dbms_output.put_line('from v$database_block_corruption where con_id ='||&v_pdbconid||'; ');	
	  
-------------------------------------------------
--Prompt Heading DB:Database Encrypted - Tablespace |
-------------------------------------------------  
      dbms_output.put_line('Prompt Heading DB:Database Encrypted - Tablespace');
      dbms_output.put_line('SELECT B.NAME TABLESPACE_NAME, ENCRYPTIONALG, ENCRYPTEDTS  ');
	  dbms_output.put_line('from sys.V_$ENCRYPTED_TABLESPACES A, sys.V_$TABLESPACE  B ');
	  dbms_output.put_line('WHERE A.TS# = B.TS# AND B.con_id ='||&v_pdbconid||'; ');	
-----------------------------------------------
--Prompt Heading DB:Database Encrypted Columns |
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database Encrypted - Columns');
      dbms_output.put_line('select OWNER,TABLE_NAME,COLUMN_NAME,ENCRYPTION_ALG,SALT');
      dbms_output.put_line('from dba_encrypted_columns');
	  dbms_output.put_line('WHERE OWNER not in '||owner_blacklist);
      dbms_output.put_line('order by 1,2,3;');
	  
-----------------------------------------------
--Prompt Heading DB:Database Proxy Connections |
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database Proxy Connections');
      dbms_output.put_line('select * ');
	  dbms_output.put_line('from dba_proxies ');
	  dbms_output.put_line('order by 1,2; ');

-----------------------------------------------
--Prompt Heading DB:Database RMAN Configuration|
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database RMAN Configuration');
      dbms_output.put_line('SELECT name, value ');
	  dbms_output.put_line('from sys.v_$rman_configuration ');
	  dbms_output.put_line('WHERE con_id ='||&v_pdbconid);
	  dbms_output.put_line('order by 1; ');

--------------------------------------------
--Prompt Heading DB:Database RMAN Configuration|
--------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database RMAN Configuration');
      dbms_output.put_line('select owner,sum(bytes)/1024/1024/1024 as "size in GB" ');
	  dbms_output.put_line('from dba_segments ');
	  dbms_output.put_line('WHERE owner not in '||owner_blacklist);
	  dbms_output.put_line('group by owner ');
	  dbms_output.put_line('order by 2 asc; ');
	  
------------------------------------------------
--Prompt Heading DB:Database Custom Schema Size |
------------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database Custom Schema Size');	  
	  dbms_output.put_line('select owner,sum(bytes)/1024/1024/1024 as "size in GB" from cdb_segments');
	  dbms_output.put_line('where con_id ='||&v_pdbconid||' AND owner in (select username from cdb_users where oracle_maintained=''N'' and username not in '||owner_blacklist||') ');	  
	  dbms_output.put_line('group by owner ');
	  dbms_output.put_line('order by 2 asc; ');
-------------------------------------------
--Prompt Heading DB:External Table Details |
-------------------------------------------
      dbms_output.put_line('Prompt Heading DB:External Table Details');
      dbms_output.put_line('select * from DBA_EXTERNAL_TABLES;');

-- Query added on 16/08/2021 
----------------------------------------
--Prompt Heading DB:DNFS Status Details |
----------------------------------------
      dbms_output.put_line('Prompt Heading DB:DNFS Status Details');
      dbms_output.put_line('select * from gv$dnfs_servers where con_id ='||&v_pdbconid||';');
-------------------------------
--Prompt Heading DB:ACL Details|
-------------------------------
      --dbms_output.put_line('Prompt Heading DB:ACL Details');
      --dbms_output.put_line('select * from dba_network_acls;');
----------------------------------
--Prompt Heading DB:ACL Privileges|
---------------------------------- 
      --dbms_output.put_line('Prompt Heading DB:ACL Privileges');
      --dbms_output.put_line('select * from dba_network_acl_privileges;');
---------------------------------------
--Prompt Heading DB:LOB Segment Details|
---------------------------------------
      dbms_output.put_line('Prompt Heading DB:LOB Segment Details');
      --dbms_output.put_line('select owner,table_name,column_name,segment_name,tablespace_name,index_name,ENCRYPT,COMPRESSION,SECUREFILE ');
	  --dbms_output.put_line('from dba_lobs where owner not in '||owner_blacklist);
	  --dbms_output.put_line('order by 1,2;');
	  dbms_output.put_line('SELECT * FROM (SELECT l.owner,l.table_name,l.column_name,l.segment_name,l.tablespace_name,index_name,ENCRYPT,COMPRESSION,SECUREFILE,ROUND(s.bytes/1024/1024/1024,2) size_GB ');
	  dbms_output.put_line('FROM   dba_lobs l JOIN dba_segments s ON s.owner = l.owner AND s.segment_name = l.segment_name ');
	  dbms_output.put_line('where l.owner not in '||owner_blacklist);
	  dbms_output.put_line('order by 10 DESC);');	
-----------------------------------------------
--Prompt Heading DB:Restricted Session Username|
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Restricted Session Username');
      dbms_output.put_line('select username Restricted_Session_username from (select u.username from dba_role_privs rp,dba_users u where u.username=rp.grantee and ');
	  dbms_output.put_line('rp.granted_role in (select grantee from dba_sys_privs where privilege=''RESTRICTED_SESSION'' and grantee in (select role from dba_roles)) union ');
	  dbms_output.put_line('select grantee from dba_sys_privs where privilege=''RESTRICTED_SESSION'' and grantee not in (select role from dba_roles));');
-----------------------------------------------
--Prompt Heading DB:Database Global Names value details|
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database Global Names value details');
      dbms_output.put_line('select ''Show parameter global_names'' GLOBAL_NAME_DETAILS,(select value from v$parameter where name=''global_names'') VALUE from dual union select ''select GLOBAL_NAME from GLOBAL_NAME;'' Command,(select GLOBAL_NAME from GLOBAL_NAME) VALUE from dual;');
-----------------------------------------------
--Prompt Heading DB:Database users having SUPERUSER privileges|
-----------------------------------------------
      dbms_output.put_line('Prompt Heading DB:Database users having SUPERUSER privileges');
      dbms_output.put_line('col USERNAME for a30');
      dbms_output.put_line('col SYSDBA for a10');
      dbms_output.put_line('col SYSOPER for a10');
      dbms_output.put_line('col SYSASM for a10');
      dbms_output.put_line('select * from v$pwfile_users;');
-----------------------------------------------
--Prompt Heading 00:Discovery Summary          |
-----------------------------------------------
      dbms_output.put_line('Prompt Heading 00:Discovery Summary');
      dbms_output.put_line('WITH SERVER_INFO AS (');
      dbms_output.put_line('SELECT (select name from v$database) DB_NAME,');
	  dbms_output.put_line('(select PDB_NAME from DBA_PDBS where PDB_NAME in (SELECT name from v$pdbs where con_id='||&v_pdbconid||')) PDB_NAME,');
      dbms_output.put_line('(select version from v$instance) DB_VERSION,');
      dbms_output.put_line('(select count(1) from dba_users where username=''SYSADM'') SYSADM_USER,');	
      dbms_output.put_line('(select HOST_NAME from v$instance) HOST_NAME,');
      dbms_output.put_line('(select decode(count(*),3,''1/8th OR Quarter RAC'',7,''Half RAC'',14,''Full RAC'',''Non-Exadata'') from (select distinct cell_name from gv$cell_state)) Exadata_Option,');
      dbms_output.put_line('(select Platform_name from v$database) OS_PLATFORM,');
      dbms_output.put_line('(select upper(ENDIAN_FORMAT) ENDIANNESS from v$transportable_platform tp, v$database db where tp.platform_id=db.platform_id) ENDIANNESS,');
      dbms_output.put_line('(select value from v$parameter where name =''cluster_database'') CLUSTER_DATABASE,');
      dbms_output.put_line('(SELECT max(round(s.bytes/1024/1024/1024,2)) Lob_max_size FROM   dba_lobs l JOIN dba_segments s ON s.owner = l.owner AND s.segment_name = l.segment_name');
      dbms_output.put_line('where l.owner not in '||owner_blacklist||') LOB_MAX,');
      dbms_output.put_line('(select count(1) from dba_scheduler_schedules where owner not in '||owner_blacklist||') DB_JOBS,');
      dbms_output.put_line('(select count(partition_name) from dba_tab_partitions');
      dbms_output.put_line('where table_owner not in '||owner_blacklist||') TAB_PART,');
      dbms_output.put_line('(select VERSION from V$TIMEZONE_FILE) TIME_ZONE,');
      dbms_output.put_line('(select COUNT(1) from dba_mviews where owner not in '||owner_blacklist||') MVIEWS,');
      dbms_output.put_line('(select LOG_MODE  from v$database) LOG_MODE,');
      dbms_output.put_line('(SELECT COUNT(1) from (select username from dba_users where trim(PASSWORD_VERSIONS) = ''10G'' and username not in '||owner_blacklist||')) PASSWORD_VERSIONS,');
      dbms_output.put_line('(SELECT COUNT(BLOCK_SIZE) FROM (SELECT DISTINCT BLOCK_SIZE FROM dba_tablespaces)) MULTI_BL_TBS,');
      dbms_output.put_line('(SELECT COUNT(PROFILE) FROM (SELECT DISTINCT PROFILE FROM dba_users where PROFILE<>''DEFAULT'')) CUSTOM_PROFILE,');
      dbms_output.put_line('(SELECT count(1) from V$ENCRYPTION_WALLET where status <> ''CLOSED'') ENC_WALLET,');
      dbms_output.put_line('(select count(1) from dba_objects where status<>''VALID'' and owner not in '||owner_blacklist||') INVALID_OBJECT,');
      dbms_output.put_line('(select TO_CHAR(COUNT(NVL(OWNER,0))) from DBA_RECYCLEBIN) RECYCLE_BIN,');
      dbms_output.put_line('(select COUNT(1) from dba_registry WHERE STATUS<>''VALID'') INVALID_COMP,');
      dbms_output.put_line('(select comp_id||'' Exists'' from dba_registry where comp_id=''APEX'') APEX_COMP,');
      dbms_output.put_line('(SELECT count(1) FROM dba_directories) DB_DIRECTORIES,');
      dbms_output.put_line('(SELECT count(1) from V$ENCRYPTED_TABLESPACES A, sys.V_$TABLESPACE  B WHERE A.TS# = B.TS#) TDE,');
      dbms_output.put_line('(SELECT count(1) FROM dba_db_links) DB_LINK,');
      dbms_output.put_line('(select count(1) FROM v$parameter WHERE NAME=''utl_file_dir'' and VALUE is not null) UTL_FILE_DIR,');
      dbms_output.put_line('(select value/1024||'' KB''  from V$PARAMETER where name=''db_block_size'') DB_BLOCK_SIZE,');
      dbms_output.put_line('(select length(addr)*4 || ''-bits'' word_length from v$process where rownum=1) DB_WORD_SIZE,');
      dbms_output.put_line('(select SWITCHOVER_STATUS from v$database) STANDBY_PARAMETER_NAME,');
      dbms_output.put_line('(select count(1) from DBA_EXTERNAL_TABLES) EXT_TAB,');
      dbms_output.put_line('(select value from (select ''STANDARD'' value from dual union select value from V$PARAMETER where name=''max_string_size'' order by 1) where rownum <=1) MAX_STRING_SIZE');
      dbms_output.put_line('from dual');
      dbms_output.put_line('),');
      dbms_output.put_line('DB_SIZE AS (');
      dbms_output.put_line('select round(a.Database_Size_GB,4)||'' GB'' database_size,case when round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2)<0 then 1 else round(( a.Database_Size_GB - (b.Archive_logs_GB + c.rollback_segs_GB + d.TEMP_TS_GB + e.free_space_GB)),2) end ||'' GB'' dbs_data_size');
      dbms_output.put_line(',round(b.Archive_logs_GB,2)  Archive_logs_size,round(c.rollback_segs_GB,2) rollback_segs_size');
      dbms_output.put_line(',round(d.TEMP_TS_GB,2)  temp_ts_size,round(e.free_space_GB,2) free_space_size,''all units are in GB'' size_units');
      dbms_output.put_line('from');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) Database_Size_GB from (select sum(bytes) bytes from dba_data_files union all select sum(bytes) bytes from sys.v_$log union all select sum(bytes) bytes from dba_temp_files)) a,');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) Archive_logs_GB from sys.v_$log )b,');
      dbms_output.put_line('( select sum(bytes/1024/1024/1024) rollback_segs_GB from dba_data_files where tablespace_name in ( select distinct tablespace_name from dba_rollback_segs where tablespace_name not in (''SYSTEM'') ))c,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) TEMP_TS_GB from dba_temp_files) d,');
      dbms_output.put_line('(select sum(bytes/1024/1024/1024) free_space_GB from dba_free_space) e');
      dbms_output.put_line('),');
      dbms_output.put_line('CHAR_SET as (');
      dbms_output.put_line('select a.parameter NLS_PARAMETER,a.value DATABASE_VALUE,b.value CURRENT_VALUE from NLS_DATABASE_PARAMETERS a, sys.v_$parameter b');
      dbms_output.put_line('where lower(a.parameter)=b.name(+)');
      dbms_output.put_line('and upper(a.parameter) in (''NLS_CHARACTERSET'',''NLS_NCHAR_CHARACTERSET'')');
      dbms_output.put_line(')');
	  dbms_output.put_line('SELECT ''Discovery Utility Version'' KEY_POINTS,'''||&gv_script_version||''' KEY_VALUE, ''Discovery script version to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''CDB Name'' KEY_POINTS,DB_NAME KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''PDB Name'' KEY_POINTS,PDB_NAME KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Version'' KEY_POINTS,DB_VERSION KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''SYSADM user status'' KEY_POINTS,to_char(nvl(SYSADM_USER,0))||'' Exists'' KEY_VALUE, case when nvl(SYSADM_USER,0)=0 then ''No Action required'' else ''May need to reset password.Please password version in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''Database Server'' KEY_POINTS,HOST_NAME KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Source Operation System'' KEY_POINTS,OS_PLATFORM KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Endianness'' KEY_POINTS,ENDIANNESS KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Timezone Version'' KEY_POINTS,to_char(TIME_ZONE) KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Block Size'' KEY_POINTS,DB_BLOCK_SIZE KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Word Size'' KEY_POINTS,DB_WORD_SIZE KEY_VALUE, ''Information to be noted!'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''utl_file_dir'' KEY_POINTS,to_char(nvl(UTL_FILE_DIR,0)) KEY_VALUE, case when nvl(UTL_FILE_DIR,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database Directories'' KEY_POINTS,to_char(nvl(DB_DIRECTORIES,0)) KEY_VALUE, case when nvl(DB_DIRECTORIES,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Database JOBs'' KEY_POINTS,to_char(nvl(DB_JOBS,0)) KEY_VALUE, case when nvl(DB_JOBS,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''DB Link'' KEY_POINTS,to_char(nvl(DB_LINK,0)) KEY_VALUE, case when nvl(DB_LINK,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Invalid objects'' KEY_POINTS,to_char(nvl(INVALID_OBJECT,0)) KEY_VALUE, case when nvl(INVALID_OBJECT,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Standby available'' KEY_POINTS,nvl(STANDBY_PARAMETER_NAME,''NOT AVAILABLE'') KEY_VALUE, ''Needs to be highlighted.Please check details in the report..'' OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Recycle Bin'' KEY_POINTS,to_char(NVL(RECYCLE_BIN,0)) KEY_VALUE,case when NVL(RECYCLE_BIN,0)=0 then ''No Action required'' else ''Needs to be highlighted.'' end  OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''max_string_size'' KEY_POINTS,MAX_STRING_SIZE KEY_VALUE, case when MAX_STRING_SIZE=''EXTENDED'' THEN ''Need to change this parameter at Target'' ELSE ''No Action required'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Archive Log Mode'' KEY_POINTS,LOG_MODE KEY_VALUE, case when LOG_MODE=''ARCHIVELOG'' THEN ''This database is in ARCHIVELOG mode'' else ''This database is in NOARCHIVELOG mode'' end FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Exadata_Option'' KEY_POINTS,EXADATA_OPTION KEY_VALUE, case when EXADATA_OPTION=''Non-Exadata'' THEN ''This database is Non-Exadata'' else ''This database is in Exadata. Please check the value'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Encrypted - Tablespace'' KEY_POINTS,to_char(nvl(TDE,0)) KEY_VALUE, case when nvl(TDE,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Encrypted - Database Wallet'' KEY_POINTS,to_char(nvl(ENC_WALLET,0)) KEY_VALUE, case when nvl(ENC_WALLET,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Cluster Check'' KEY_POINTS,CLUSTER_DATABASE KEY_VALUE, case when CLUSTER_DATABASE=''FALSE'' THEN ''This database is not cluster enabled'' else ''This database is cluster enabled'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Total Database_size'' KEY_POINTS,database_size KEY_VALUE, ''Total Database Size [Datafiles + Log files + Temp files]'' OBSERVATION FROM  DB_SIZE union all');
      dbms_output.put_line('SELECT ''Actual Database_size'' KEY_POINTS,dbs_data_size KEY_VALUE, ''Actual Data Size'' OBSERVATION FROM  DB_SIZE  union all');
      dbms_output.put_line('SELECT ''NLS_CHARACTERSET'' KEY_POINTS,case when CURRENT_VALUE is not null then CURRENT_VALUE else DATABASE_VALUE end  KEY_VALUE, ''Please check this value at target database belore migration.'' OBSERVATION FROM  CHAR_SET WHERE NLS_PARAMETER =''NLS_CHARACTERSET'' union all ');
      dbms_output.put_line('SELECT ''NLS_NCHAR_CHARACTERSET'' KEY_POINTS,case when CURRENT_VALUE is not null then CURRENT_VALUE else DATABASE_VALUE end  KEY_VALUE, ''Please check this value at target database belore migration.'' OBSERVATION FROM  CHAR_SET WHERE NLS_PARAMETER =''NLS_NCHAR_CHARACTERSET'' union all');
      dbms_output.put_line('SELECT ''LOB Max Size'' KEY_POINTS,to_char(nvl(LOB_MAX,0))||'' GB'' KEY_VALUE, case when nvl(LOB_MAX,0)<30 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Partition Count'' KEY_POINTS,to_char(nvl(TAB_PART,0)) KEY_VALUE, case when nvl(TAB_PART,0)<1000 then ''No Action required'' else ''Partions are on higher side.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Materialized View'' KEY_POINTS,to_char(nvl(MVIEWS,0)) KEY_VALUE, case when nvl(MVIEWS,0)=0 then ''No Action required'' else ''Needs to be highlighted..Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Invalid Components'' KEY_POINTS,to_char(nvl(INVALID_COMP,0)) KEY_VALUE, case when nvl(INVALID_COMP,0)=0 then ''No Action required'' else ''Needs to be highlighted..Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''APEX Components'' KEY_POINTS,nvl(APEX_COMP,''NA'') KEY_VALUE, case when nvl(APEX_COMP,''NA'')=''NA'' then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''External Table'' KEY_POINTS,to_char(nvl(EXT_TAB,0))||'' Exists'' KEY_VALUE, case when nvl(EXT_TAB,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO  union all');
      dbms_output.put_line('SELECT ''Multiblock Tablespaces'' KEY_POINTS,case when nvl(MULTI_BL_TBS,0)<=1 then ''Not Available'' else ''Multiblock Exists'' end KEY_VALUE, case when nvl(MULTI_BL_TBS,0)<=1 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''Non-Default User Profile'' KEY_POINTS,to_char(nvl(CUSTOM_PROFILE,0))||'' Exists'' KEY_VALUE, case when nvl(CUSTOM_PROFILE,0)<=1 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO union all');
      dbms_output.put_line('SELECT ''10g Password Version'' KEY_POINTS,PASSWORD_VERSIONS||'' Exists'' KEY_VALUE, case when nvl(PASSWORD_VERSIONS,0)=0 then ''No Action required'' else ''Needs to be highlighted.Please check details in the report..'' end OBSERVATION FROM  SERVER_INFO;');
	  
	  dbms_output.put_line('SET TERMOUT OFF ');

END IF;   ---End of CDB Block

END;
/

--#################################################################
--#################################################################
DECLARE
   -- Note: This should be the last block of discovery script.
   -- This is very importan block ;
   v_sub_str varchar2(300);
BEGIN
   dbms_output.put_line('PROMPT Heading U_I_GG OGG:Z Reporting End Time');
   v_sub_str:= 'select '||''''||'REPORT_END_TIME='||''''||'||'||'to_char(sysdate,'||''''||'DD-Mon-YYYY HH24:MI:SS';
   v_sub_str:= v_sub_str||''''||') REPORT_END_TIME from dual;';
   dbms_output.put_line(v_sub_str);
END;
/
set termout on;
Prompt spool off;;
spool off;

set termout on;
@&here_sql_file_name;
-------------------------------------------------------------------------
set heading off;
set echo off;
set verify off;
set termout off;
set markup html off;
set serveroutput on;
spool &here_sql_file_name;
define _editor=vi
set serveroutput on;
DECLARE

    PROCEDURE delsqlfile IS
	v_os_platform varchar2(200);
	BEGIN
	EXECUTE IMMEDIATE 'SELECT lower(PLATFORM_NAME) FROM sys.v_$database' INTO v_os_platform;
	IF(v_os_platform LIKE  '%window%') THEN
	dbms_output.put_line('host del /Q '||'&here_sql_file_name');
	END IF;
	IF( (v_os_platform LIKE  '%solaris%') OR (v_os_platform like  '%linux%') OR (v_os_platform like  '%aix%') OR (v_os_platform like  '%hp%') ) THEN
	dbms_output.put_line('host rm -rf '||'&here_sql_file_name');
	END IF;
	END;
BEGIN
delsqlfile;
END;
/
Prompt exit;;
spool off;
@&here_sql_file_name;
-------------------------------------------------------------------------------