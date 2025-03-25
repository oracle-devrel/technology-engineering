REM Script: 1-create-partitioned-table.sql
REM Use data from HR table EMPLOYEES

-- prereq EMPLOYEES table from HR schema 
-- HR schema available in https://github.com/oracle-samples/db-sample-schemas/blob/main/human_resources/hr_create.sql 


DROP TABLE hr.employees_hybrid;

CREATE TABLE hr.employees_hybrid
   (  EMPLOYEE_ID varchar2(10),
      SALARY      number,
      JOB_TITLE   varchar2 (35))
    PARTITION BY RANGE (salary)
    ( PARTITION salary_4000 VALUES less than (4000),   -- internal partition
      PARTITION salary_10000 VALUES less than (10000), -- internal partition
      PARTITION salary_30000 VALUES less than (30000), -- intern partition
      PARTITION salary_max values less than (MAXVALUE))
/

-- insert rows

INSERT INTO hr.employees_hybrid
SELECT e.employee_id, e.salary, j.job_title 
FROM hr.employees e JOIN hr.jobs j ON e.job_id=j.job_id;

COMMIT;
