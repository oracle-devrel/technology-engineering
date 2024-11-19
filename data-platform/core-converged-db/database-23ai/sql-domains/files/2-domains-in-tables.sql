REM Script for 23c: 2-domains-in-tables.sql

-- optional drop the table person 
drop table if exists person;

-- create table person with domain myemail_domain
create table person
     ( p_id number(5),
       p_name varchar2(50),
       p_sal number,
       p_email varchar2(100) domain myemail_domain
      )
annotations (display 'person_table'); 

-- add some rows
insert into person values (1,'Bold',3000,null);
insert into person values (1,'Schulte',1000, 'mschulte@gmx.net');
insert into person values (1,'Walter',1000,'twalter@t_online.de');
insert into person values (1,'Schwinn',1000, 'Ulrike.Schwinn@oracle.com');
insert into person values (1,'King',1000, 'aking@aol.com');
commit;

-- try to add invalid data
insert into person values (1,'Schulte',3000, 'mschulte%gmx.net');

-- query the table person
desc person

select * from person;
