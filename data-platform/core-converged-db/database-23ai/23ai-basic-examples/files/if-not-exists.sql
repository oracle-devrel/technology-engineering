REM Script in 23c: if-not-exists.sql

-- suppose table DEPT exists
desc dept

-- try several times, no error occurs
create table if not exists scott.dept (deptno number, dname varchar2(10), loc varchar2(15));

-- create a helper table
create table dept1 as select * from dept;

-- drop several times, no error occurs
drop table if exists dept1;
