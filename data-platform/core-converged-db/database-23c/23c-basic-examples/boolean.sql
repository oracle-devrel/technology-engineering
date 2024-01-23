REM  Script in 23c: boolean.sql

drop table test_boolean;

create table TEST_BOOLEAN
( name VARCHAR2(100),
  IS_SLEEPING BOOLEAN);

alter table TEST_BOOLEAN modify (IS_SLEEPING boolean NOT NULL);

alter table TEST_BOOLEAN modify (IS_SLEEPING default FALSE);

insert into TEST_BOOLEAN (name) values ('Mick');
insert into TEST_BOOLEAN (name, is_sleeping) values ('Keith','NO');
insert into TEST_BOOLEAN (name, is_sleeping) values ('Ron',1);


select name from test_boolean where not is_sleeping;

col name  format a25
select * from test_boolean;

select dump(is_sleeping) from test_boolean where name = 'Ron';​
