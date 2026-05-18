REM Script in 23c: annotations.sql

drop table emp_annotated;

create table emp_annotated
( empno number annotations(identity, display 'person_identity', details 'person_info'),
  ename varchar2(50),
  salary number annotations (display 'person_salary', col_hidden))
  annotations (display 'employee_table')
/  

-- monitor annotations
col object_name format a20
col object_type format a15
col column_name format a15
col annotation_value format a25
col annotation_name format a20
col domain_owner format a10
col domain_name format a15

select object_name, object_type, column_name, annotation_name, annotation_value 
from user_annotations_usage;
