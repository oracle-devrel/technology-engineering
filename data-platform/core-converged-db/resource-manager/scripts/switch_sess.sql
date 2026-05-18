-- Causes the specified session to immediately be moved into the specified resource consumer group. 

select SID, SERIAL#, status, resource_consumer_group 
from v$session where username='REDEF_USER';

BEGIN
  DBMS_RESOURCE_MANAGER.SWITCH_CONSUMER_GROUP_FOR_SESS('&id', '&serial','&Group_name');
END;
/
