-- Run as an ADB-D administrative user through SQLcl.
-- Usage: sql admin@<admin-service> @recreate_test_ctag.sql
-- This is destructive: it permanently drops TEST_CTAG and all objects it owns.
-- The prompted password cannot contain a double quote.
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode rollback

accept TEST_CTAG_PASSWORD char prompt 'Password for TEST_CTAG: ' hide

prompt Dropping TEST_CTAG if it exists...
begin
  execute immediate 'drop user TEST_CTAG cascade';
exception
  when others then
    if sqlcode != -1918 then raise; end if; -- ORA-01918: user does not exist
end;
/

prompt Creating TEST_CTAG...
create user TEST_CTAG identified by "&&TEST_CTAG_PASSWORD";

-- Object ownership and execution required by setup_workload.sql.
grant create session to TEST_CTAG;
grant create table to TEST_CTAG;
grant create procedure to TEST_CTAG;
grant create sequence to TEST_CTAG;
grant unlimited tablespace to TEST_CTAG;

-- Required by run_colocation_test.sh to compare RAC global-cache work before
-- and after each phase. Public GV$ synonyms resolve to these base views.
grant select on sys.gv_$system_event to TEST_CTAG;
grant select on sys.gv_$sysstat to TEST_CTAG;

-- Optional AWR add-on used only when AWR=y. AWR is Diagnostics Pack licensed.
grant execute on sys.dbms_workload_repository to TEST_CTAG;

prompt TEST_CTAG was recreated. Connect as TEST_CTAG and run setup_workload.sh.
undefine TEST_CTAG_PASSWORD
