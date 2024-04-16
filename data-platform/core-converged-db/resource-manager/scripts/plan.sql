-- Create a resource plan ORG_PLAN with directives for SYS_GROUP, OTHER_GROUP, LOWER_GROUP and REDEF_GROUP 
-- REDEF_GROUP switches automatically any session in LOWER_GROUP if a session exceeds 30 seconds. 
-- The session is returned to its original group after the offending top call is complete.
-- Run planon.sql to activate the plan

begin
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();

DBMS_RESOURCE_MANAGER.create_plan(plan => 'ORG_PLAN', comment=>'Limit CPU for redefinition');
DBMS_RESOURCE_MANAGER.create_plan_directive(plan => 'ORG_PLAN', group_or_subplan => 'REDEF_GROUP', comment => 'For redefinition', cpu_p1 => 30, SWITCH_GROUP=>'LOWER_GROUP', SWITCH_TIME =>30, switch_for_call=>true);
DBMS_RESOURCE_MANAGER.create_plan_directive(plan => 'ORG_PLAN', group_or_subplan => 'OTHER_GROUPS', comment => 'Default', cpu_p1=> 30);
DBMS_RESOURCE_MANAGER.create_plan_directive(plan => 'ORG_PLAN', group_or_subplan => 'SYS_GROUP', comment => 'SYS', cpu_p1 => 30);
DBMS_RESOURCE_MANAGER.create_plan_directive(plan => 'ORG_PLAN', group_or_subplan => 'LOWER_GROUP', comment => 'LOWER GROUP', cpu_p1 =>10, utilization_limit=>10);

DBMS_RESOURCE_MANAGER.VALIDATE_PENDING_AREA();
DBMS_RESOURCE_MANAGER.SUBMIT_PENDING_AREA();
END;
/

-- Monitor the resource plan

set linesize window
select * from v$rsrc_plan;

select sequence# seq, name plan_name,
to_char(start_time, 'DD-mon HH24:mi') start_time,
to_char(end_time, 'dd-mon hh24:mi') end_time
from v$rsrc_plan_history;
