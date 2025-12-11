drop table if exists employees cascade constraints;
drop table if exists departments cascade constraints;

create table departments( 
   department_id   number(4,0) constraint dept_id_pk primary key,
   department_name varchar2(30) constraint dept_name_nn not null, 
   manager_id      number(6,0), 
   location_id     number(4,0) 
);

create table employees(	
   employee_id    number(6,0), 
   first_name     varchar2(20 byte) collate using_nls_comp, 
   last_name      varchar2(25) constraint emp_last_name_nn not null enable, 
   email          varchar2(25) constraint emp_email_nn not null, 
   phone_number   varchar2(20), 
   hire_date      date         constraint emp_hire_date_nn not null, 
   job_id         varchar2(10) constraint emp_job_nn not null, 
   salary         number(8,2), 
   commission_pct number(2,2), 
   manager_id     number(6,0), 
   department_id  number(4,0), 
   bonus          varchar2(5), 
   constraint emp_salary_min check (salary > 0) enable, 
   constraint emp_id_pk      primary key (employee_id),
   constraint emp_email_uk   unique (email), 
   constraint emp_dept_fk    foreign key (department_id) references departments(department_id) disable,  
   constraint emp_manager_fk foreign key (manager_id) references employees (employee_id)
 ); 
