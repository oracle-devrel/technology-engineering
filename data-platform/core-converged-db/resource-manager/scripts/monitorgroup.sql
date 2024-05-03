-- Monitor user REDEF_USER and his consumer groups
 
select sid, serial#, username, resource_consumer_group, status 
from v$session where username='REDEF_USER';
