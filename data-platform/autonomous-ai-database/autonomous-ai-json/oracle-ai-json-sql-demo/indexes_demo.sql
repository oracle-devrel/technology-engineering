create or replace function partial_value(data JSON) return number
deterministic
is
begin
	if json_value(data, '$.salary') < 8000 then
		return json_value(data, '$.salary' returning number error on error);
	end if;
	return null;
end;
/

drop table if exists departments_col;
drop table if exists employees_col;
drop table if exists hr_data_t;

create json collection table departments_col;
create json collection table employees_col;
        
insert into departments_col
select json{*}
from departments;

insert into employees_col
select json{*}
from employees;

commit;

create index employees_salary_idx on employees_col(partial_value(data));

set autotrace on

select c.data from employees_col c where partial_value(c.data)=4200

set autotrace off

create json collection table hr_data_t;

create or replace json collection view hr_data_v
as
select json { 'department' : department_name,
              'employees'  : json_array_agg(last_name) }
from departments d, employees e
where d.department_id = e.department_id
group by d.department_name;

insert into hr_data_t
select *
from hr_data_v;

commit;

select *
from hr_data_t;

drop index hr_data_emp_idx;

create multivalue index hr_data_emp_idx on hr_data_t t 
(json_table(t.data, '$.employees'
 error on error null on empty null on mismatch 
 columns (last_name varchar2(30) path '$.employees')))

create multivalue index hr_data_emp_idx on hr_data_t t
( t.data.employees.string() ) 

set autotrace on

select t.data
from hr_data_t t
where json_exists(t.data ,'$.employees?(@.string() == "King")')

set autotrace off


