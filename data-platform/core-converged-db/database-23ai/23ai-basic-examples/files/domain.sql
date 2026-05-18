REM Script in 23c: domain.sql

drop domain yearbirth;

create domain yearbirth as number(4)
     constraint check ((trunc(yearbirth) = yearbirth) and (yearbirth >= 1900))
     display (case when yearbirth < 2000 then '19-' ELSE '20-' end)||mod(yearbirth, 100)
     order (yearbirth -1900)
     annotations (title 'yearformat');

drop table person;
create table person
     ( id number(5),
       name varchar2(50),
       salary number,
       person_birth number(4) DOMAIN yearbirth
      )
     annotations (display 'person_table'); 

desc person

insert into person values (1,'MARTIN',3000, 1988);

select DOMAIN_DISPLAY(person_birth) from person;

-- monitor domains
set linesize window
col object_name format a20
col object_type format a15
col column_name format a15
col annotation_value format a25
col annotation_name format a20
col domain_owner format a10
col domain_name format a15

select * from user_annotations_usage;

col owner format a10
col name format a15

select * from user_domains;
