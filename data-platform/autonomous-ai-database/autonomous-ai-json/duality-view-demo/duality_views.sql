-- 1. creation of duality views used in the demo
--    a. dept_v based on departments table
--    b. emp_v based on employees table
--    c. dept_emp_v based on join of departments and employees tables

create or replace json duality view dept_v
as
select json { '_id'            : department_id,
              'departmentName' : department_name,
              'managerId'      : manager_id,
              'locationId'     : location_id }
from departments
with insert update delete;

create or replace json duality view emp_v
as
select json {'_id'          : employee_id,
             'lastName'     : last_name,
             'firstName'    : first_name,
             'email'        : email,
             'hireDate'     : hire_date,
             'jobId'        : job_id,
             'salary'       : salary,
             'departmentId' : department_id}
from employees with insert update delete;

create or replace json duality view dept_emp_v
as
select json { '_id'            : department_id,
              'departmentName' : department_name,
              'managerId'      : manager_id,
              'locationId'     : location_id,
              'employees'      : [select json {'employeeId' : employee_id,
                                               'lastName'   : last_name,
                                               'firstName'  : first_name,
                                               'email'      : email,
                                               'hireDate'   : hire_date,
                                               'jobId'      : job_id,
                                               'salary'     : salary}
                                  from employees e 
                                  with insert update delete
                                  where e.department_id = d.department_id]}
from departments d with insert update delete;

-- 2. displaying execution plans of some sample queries

set autotrace on explain

select *
from dept_v

select *
from dept_emp_v;

set autotrace off

-- 3. DML operations
--   a. on dept_v view
--   b. on dept_emp_v view (moving an employee to another department)
insert into dept_v
values ( json {'_id'            : 290,
               'departmentName' : 'RD',
               'managerId'      : 100,
               'locationId'     : 1700});

select *
from departments;

update dept_v
set data = json_transform(data,set '$.departmentName' = 'Research and Development')
where json_value(data,'$._id' returning number) = 290;

select *
from dept_emp_v;

insert into dept_emp_v
values (json { '_id'             : 300,
               'departmentName' : 'Human Resources',
               'managerId'       : 100,
               'locationId'      : 1700,
               'employees'       : [ {'employeeId'    : 207,
                                      'lastName'      : 'Davis',
                                      'firstName'     : 'Miles',
                                      'email'         : 'MDAVIS',
                                      'hireDate'      : sysdate,
                                      'jobId'         : 'ST_CLERK',
                                      'salary'        : 6500},
                                     {'employeeId'    : 208,
                                      'lastName'      : 'Shorter',
                                      'firstName'     : 'Wayne',
                                      'email'         : 'WSHORTER',
                                      'hireDate'      : sysdate,
                                      'jobId'         : 'ST_CLERK',
                                      'salary'        : 6350}
                                    ]});
                                    
select *
from dept_emp_v;   

update dept_emp_v
set data = ({'departmentId'   : 290,
             'departmentName' : 'Research and Development',
             'managerId'      : 100,
             'locationId'     : 1700,
             'employees'      : [ {'employeeId'    : 207,
                                      'lastName'      : 'Davis',
                                      'firstName'     : 'Miles',
                                      'email'         : 'MDAVIS',
                                      'hireDate'      : sysdate,
                                      'jobId'         : 'ST_CLERK',
                                      'salary'        : 6500}
                                ]});


update dept_emp_v v
set data = ('{"_id"   : 290,
              "departmentName" : "Research and Development",
              "managerId"      : 100,
              "locationId"     : 1700,
              "employees"      : [ {"employeeId" : 207,
                                    "lastName"   : "Davis",
                                    "firstName"  : "Miles",
                                    "email"      : "MDAVIS",
                                    "jobId"      : "ST_CLERK",
                                    "salary"     : 6500}
                                ]}')
where json_value(data,'$._id' returning number) = 290;
        
commit;

-- 4. sample SODA operations on duality views
soda list

soda get dept_v -f {"departmentName" : "Accounting"}

soda get emp_v -f {"salary" : {"$gt" : 6000}}

soda insert dept_v {"_id":295,"departmentName":"Legal Operations","managerId":100,"locationId":1700}

soda get dept_v -f {"departmentName":"Legal Operations"}

soda remove dept_v -f {"departmentName":"Legal Operations"}

commit;