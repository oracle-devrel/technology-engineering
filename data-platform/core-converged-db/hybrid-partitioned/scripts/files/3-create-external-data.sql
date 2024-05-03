REM Script: 3-create-external-data.sql  
REM Create external helper table with ORACLE_DATAPUMP

-- enter directory name
-- create file salaryless3000.dmp
 
CREATE TABLE ext_help
ORGANIZATION EXTERNAL
 (
    TYPE oracle_datapump
     DEFAULT DIRECTORY &directoryname
     LOCATION ('salaryless3000.dmp')
    )
    REJECT LIMIT UNLIMITED
AS 
SELECT employee_id, salary, job_title 
FROM hr.employees_hybrid partition(SALARY_4000);
