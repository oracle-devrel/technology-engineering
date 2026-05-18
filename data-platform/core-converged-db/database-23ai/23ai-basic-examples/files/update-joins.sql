REM Script in 23c: update-joins.sql

-- query column sal
select e.ename, e.sal from dept d, emp e where e.deptno=d.deptno 
and d.dname='RESEARCH';

-- update with join
update emp e set e.sal=e.sal*2
from dept d
where e.deptno=d.deptno
and d.dname='RESEARCH';  

-- query column sal
select e.ename, e.sal from dept d, emp e where e.deptno=d.deptno 
and d.dname='RESEARCH';

rollback;
