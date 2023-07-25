REM script for 23c: 4-monitor-domains.sql

-- use USER_DOMAINS and USER_DOMAIN_CONSTRAINTS to get information about domains

col owner format a15
col name format a15 
select owner, name, data_display 
from user_domains;

col domain_owner format a15
col domain_name format a15 
select * from user_domain_constraints 
where domain_name='MYEMAIL_DOMAIN';
