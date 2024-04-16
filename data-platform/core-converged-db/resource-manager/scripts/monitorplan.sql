-- Display information about the resource plans

set echo on
set pause on
set pagesize 1000
set linesize window

select name, is_top_plan plan from v$rsrc_plan;

-- history of active plans
col plan_name format a15

select sequence# seq, name plan_name,
to_char(start_time, 'DD-mon HH24:mi') start_time,
to_char(end_time, 'dd-mon hh24:mi') end_time
from v$rsrc_plan_history;

-- display information about all resource consumer groups in the database.

col consumer_group format a25
col comments format a70
col status format a10

select consumer_group, comments, status
from dba_rsrc_consumer_groups;

-- displays information about all resource consumer groups and the users and roles assigned to them

col grantee format a25
col granted_group format a35
col status format a10
select * from dba_rsrc_consumer_group_privs;

-- displays the mapping between session attributes and consumer groups in the database

col value format a20
col consumer_group format a25
col attribute format a15

select attribute, value, consumer_group
from dba_rsrc_group_mappings;


-- List plan directives for ORG_PLAN

col plan format a15
col group_or_subplan format a15
col comments format a20
col switch_group format a15

select plan, group_or_subplan, type, cpu_p1, switch_group, switch_for_call, switch_time, status, comments, mandatory
from dba_rsrc_plan_directives
where plan='ORG_PLAN';

-- List user session and group of REDEF_USER

col username format a20
SELECT username, resource_consumer_group, status
FROM   v$session
WHERE  username = 'REDEF_USER';
