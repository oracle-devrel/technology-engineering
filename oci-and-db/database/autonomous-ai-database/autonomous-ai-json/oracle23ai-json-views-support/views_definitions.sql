drop view empview;
drop view deptview;
drop table departments cascade constraints;
drop table employees cascade constraints;

create table departments
as
select *
from hr.departments;

create table employees
as
select *
from hr.employees;

alter table departments add primary key(department_id);
alter table employees add primary key(employee_id);

create or replace json collection view empview 
as
select json{'_id' : employee_id,
            last_name,
            hire_date,
            salary}
from employees;

select *
from user_json_collections;

create or replace json relational duality view deptview as
select json {'_id' : department_id,
             'dname'   : department_name,
             'location' : location_id}
from departments with insert update delete;

