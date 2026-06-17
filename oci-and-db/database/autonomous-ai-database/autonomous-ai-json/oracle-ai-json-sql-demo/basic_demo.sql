drop table if exists departments_col;
drop table if exists employees_col;

create json collection table departments_col;
create json collection table employees_col;
        
insert into departments_col
select json{*}
from departments;

insert into employees_col
select json{*}
from employees;

commit;

select d.data."DEPARTMENT_NAME"
from departments_col d;

select JSON{d.data."DEPARTMENT_NAME"}
from departments_col d;

select json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30)) department_name,
       json_value(e.data, '$.LAST_NAME' returning varchar2(30) ) last_name       
from employees_col e,
     departments_col d
where json_value(d.data, '$.DEPARTMENT_ID' returning number) = json_value(e.data, '$.DEPARTMENT_ID' returning number);

select json{ 'department' : json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30)),
             'no_of_emps' : count(*) }
from employees_col e,
     departments_col d
where json_value(d.data, '$.DEPARTMENT_ID' returning number) = json_value(e.data, '$.DEPARTMENT_ID' returning number)
group by json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30));

select json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30)) department_name,
       json_array_agg(json_value(e.data, '$.LAST_NAME')) employees
from employees_col e,
     departments_col d
where json_value(d.data, '$.DEPARTMENT_ID' returning number) = json_value(e.data, '$.DEPARTMENT_ID' returning number)
group by json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30));

create json collection view hr_data_v
as
select json{ 'department' : json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30)),
             'employees'  : json_array_agg(json_value(e.data, '$.LAST_NAME'))}
from employees_col e,
     departments_col d
where json_value(d.data, '$.DEPARTMENT_ID' returning number) = json_value(e.data, '$.DEPARTMENT_ID' returning number)
group by json_value(d.data, '$.DEPARTMENT_NAME' returning varchar2(30));

select *
from hr_data_v;

select v.data."employees"
from hr_data_v v;

select v.data."employees"[0 to 1]
from hr_data_v v;

select v.data."department",
       v.data."employees".size() no_of_employees,
       v.data."employees"[*].type() types
from hr_data_v v;

select t.data
from employees_col t
where json_exists(t.data ,'$?(@.LAST_NAME == "King")')

select t.data
from employees_col t
where json_exists(t.data ,'$?(@.SALARY >= 10000 && @.LAST_NAME != "King")')

