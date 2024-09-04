REM  Script for 23c: 4-create-index-with-annotation.sql

-- create index on column loc with annotation

create index i_loc_dept on dept (loc) annotations (display 'Deptno Location Index');
