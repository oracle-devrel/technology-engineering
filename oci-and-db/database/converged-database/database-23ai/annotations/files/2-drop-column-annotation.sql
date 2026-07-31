REM  Script for 23c: 2-drop-column-annotation.sql

--- drop a column annotation with ALTER TABLE MODIFY
alter table emp_annotated modify ename annotations (drop display);
