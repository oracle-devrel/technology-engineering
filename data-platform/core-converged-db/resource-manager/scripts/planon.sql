-- Activate a Resource Manager plan, or change the current top plan, using the DBMS_RESOURCE_MANAGER.SWITCH_PLAN package procedure or the ALTER SYSTEM statement.

begin
  dbms_resource_manager.switch_plan(plan_name =>'ORG_PLAN', sid => '*');
end;
/

-- monitor active plan
set pagesize 200
select * from v$rsrc_plan;
