REM  Script for 23c: 3-create-view-with-annotations.sql

-- create a view with column annotations for emp_id, emp_name, and emp_dname and an annotation for the view itself

create or replace view empdept_ann
(emp_id    annotations (identity, display 'employee Id', category 'emp info'),
 emp_name  annotations (display 'employee name', category 'emp info'),
 emp_dname annotations (category 'emp info')
)
annotations (title 'employee view')
as select e.empno, e.ename, d.dname 
from emp e, dept d
where e.deptno=d.deptno and sal>1000;
