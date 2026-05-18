REM Creation of tablespace, user and directory

-- connect as user sys to FREEPDB1

-- create tablespace

create bigfile tablespace TBS_VECTOR datafile size 256M autoextend on maxsize 2G;

-- create user with the new role DB_DEVELOPER_ROLE
DROP USER vector_user cascade;

create user vector_user identified by "Oracle_4U"
default tablespace TBS_VECTOR temporary tablespace TEMP
quota unlimited on TBS_VECTOR;

grant create mining model to vector_user;
grant DB_DEVELOPER_ROLE to vector_user;

-- create directory

CREATE OR REPLACE DIRECTORY dm_dump as '&directorypath';
GRANT all ON DIRECTORY dm_dump TO vector_user;