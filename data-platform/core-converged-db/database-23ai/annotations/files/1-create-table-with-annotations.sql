REM  Script for 23c: 1-create-table-with-annotations.sql

-- optional drop table emp_annotated
drop table if exists emp_annotated; -- with new 23c "if exists" syntax 

-- create a table with two column annotations for ename and salary and a table annotation
create table emp_annotated
( empno number,
  ename varchar2(50) annotations (display 'lastname'),
  salary number      annotations (person_salary, column_hidden)
 )
annotations (display 'employees'); 
