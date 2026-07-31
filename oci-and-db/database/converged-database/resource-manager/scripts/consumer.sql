-- Create the consumer groups in a first step
-- A resource consumer group (consumer group) is a collection of user sessions that are grouped together based on their processing needs.
-- There are special consumer groups SYS_GROUP and OTHER_GROUPS that are always present in the data dictionary. They cannot be modified or deleted. SYS_GROUP
-- There can be no more than 28 resource consumer groups in any active plan.


-- delete existing groups if required
BEGIN
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();

dbms_resource_manager.delete_consumer_group(consumer_group => 'REDEF_GROUP');

dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/
BEGIN
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();

dbms_resource_manager.delete_consumer_group(consumer_group =>'LOWER_GROUP');

dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/
 
-- change priority of consumer groups if required
begin 
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();

  dbms_resource_manager.set_consumer_group_mapping_pri(
  explicit               => 1,
  service_module_action  => 2,
  service_module         => 3,
  module_name_action     => 4,
  module_name            => 5, 
  service_name           => 6,   
  oracle_user            => 7, 
  client_program         => 8, 
  client_os_user         => 9, 
  client_machine         => 10, 
  client_id		 => 11);

dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();
end;
/

-- Create consumer group REDEF_GROUP and LOWER_GROUP
BEGIN
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();
dbms_resource_manager.create_consumer_group(consumer_group => 'REDEF_GROUP', comment => 'Consumer group for redefinition');
dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/

-- Consumer group for lower usage
BEGIN
dbms_resource_manager.clear_pending_area();
dbms_resource_manager.create_pending_area();
dbms_resource_manager.create_consumer_group(consumer_group => 'LOWER_GROUP', comment => 'Consumer group for lower usage');
dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/

-- Grant user REDEF_USER the privilege to switch to group REDEF_GROUP and map user REDEF_USER to the REDEF_GROUP consumer group every time he logs in:
BEGIN
 dbms_resource_manager.clear_pending_area();
 dbms_resource_manager.create_pending_area();

DBMS_RESOURCE_MANAGER_PRIVS.GRANT_SWITCH_CONSUMER_GROUP(GRANTEE_NAME => 'REDEF_USER', CONSUMER_GROUP => 'REDEF_GROUP', GRANT_OPTION => TRUE);
DBMS_RESOURCE_MANAGER.set_consumer_group_mapping(attribute => dbms_resource_manager.oracle_user, value => 'REDEF_USER',consumer_group => 'REDEF_GROUP');

dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/

-- Grant user REDEF_USER the privilege to switch to group LOWER_GROUP 
BEGIN
 dbms_resource_manager.clear_pending_area();
 dbms_resource_manager.create_pending_area();

DBMS_RESOURCE_MANAGER_PRIVS.GRANT_SWITCH_CONSUMER_GROUP(GRANTEE_NAME => 'REDEF_USER', CONSUMER_GROUP => 'LOWER_GROUP', GRANT_OPTION => TRUE);

dbms_resource_manager.validate_pending_area();
dbms_resource_manager.submit_pending_area();
END;
/


-- Monitor consumer groups and the mappings
set linesize window
col value format a20
col consumer_group format a25
col attribute format a15
select attribute, value, consumer_group from DBA_RSRC_GROUP_MAPPINGS;

col comments format a60
col status format a10
select CONSUMER_GROUP, COMMENTS from DBA_RSRC_CONSUMER_GROUPS;
