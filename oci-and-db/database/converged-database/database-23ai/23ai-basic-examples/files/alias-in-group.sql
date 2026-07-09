REM  Script in 23c: alias-in-group.sql

-- GROUP BY with alias

SELECT to_char(hiredate,'YYYY') "Year", count(*)
FROM emp
GROUP BY "Year";
