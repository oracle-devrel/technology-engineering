REM script for 23c: 6-using-builtin-domains.sql
REM Oracle provides built-in domains you can use directly on table columns.

-- query ALL_DOMAINS and filter on SYS
select name from all_domains where owner='SYS';

-- Let's investigate the domain EMAIL_D

set long 1000
set longc 1000
select dbms_metadata.get_ddl('SQL_DOMAIN', 'EMAIL_D','SYS') domain_ddl from dual;

-- Now let's re-create the table PERSON. 
-- Please keep in mind that we need to adjust the length of the column P_EMAIL to 4000 - otherwise you will receive the following error:ORA-11517: the column data type does not match the domain column

drop table person;

create table person     
( p_id number(5),
  p_name varchar2(50),
  p_sal number,
  p_email varchar2(4000) domain EMAIL_D
      )
annotations (display 'person_table');

--let's insert valid and invalid data

insert into person values (1,'Bold',3000,null);

insert into person values (1,'Schulte',1000, 'mschulte@gmx.net');

insert into person values (1,'Walter',1000,'twalter@t_online.de');
