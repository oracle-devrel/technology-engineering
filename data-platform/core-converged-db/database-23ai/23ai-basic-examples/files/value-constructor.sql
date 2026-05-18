REM Script in 23c: value-constructor.sql

-- use it in the FROM clause to generate rows
SELECT *
FROM (VALUES (1,'SCOTT'),
             (2,'SMITH'),
             (3,'JOHN')
) t1 (employee_id, first_name);

-- with clause
with CCCP (c1,c2) as (
  values (1, 'SCOTT'), (2, 'SMITH'), (3, 'JOHN'))
select * from cccp;


-- create a table and cast it to get the correct length of the column
drop table if exists cccp;

create table cccp
as
SELECT *
FROM (VALUES (1,'SCOTT'),
             (2,cast('SMITH' as VARCHAR2(30))),
             (3,'JOHN')
) t1 (employeed_id,first_name)
where 1=2;

desc cccp

- use it to add 3 rows 
insert into cccp (EMPLOYEED_ID, FIRST_NAME)
values (1,'SCOTT'),
        (2,'SMITH'),
        (3,'JOHN');
commit;

select * from cccp;
