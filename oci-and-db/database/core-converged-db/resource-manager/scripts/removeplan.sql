-- Remove a resource plan

ALTER SYSTEM SET RESOURCE_MANAGER_PLAN = '';

BEGIN
DBMS_RESOURCE_MANAGER.clear_pending_area;
DBMS_RESOURCE_MANAGER.create_pending_area;

DBMS_RESOURCE_MANAGER.delete_plan_cascade(plan => '&plan_name');

DBMS_RESOURCE_MANAGER.validate_pending_area;
DBMS_RESOURCE_MANAGER.submit_pending_area;
END;
/
