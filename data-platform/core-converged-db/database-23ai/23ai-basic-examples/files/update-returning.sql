REM Script in 23c: update-returning.sql

SELECT ename, sal FROM emp
WHERE ename = 'KING';

-- create variables in SQL*Plus and Update with returning
VARIABLE old_salary NUMBER
VARIABLE new_salary NUMBER

UPDATE emp
     SET sal=sal+1000
     WHERE ename = 'KING'
     RETURNING OLD sal, NEW sal into :old_salary, :new_salary;

-- check the result
PRINT old_salary
PRINT new_salary

rollback;
