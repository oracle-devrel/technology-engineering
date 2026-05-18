REM Script: 2-transport-sts-to-target.sql
REM on the the source system create a staging table and add the statements to it 

-- first import the staging table
-- copy the SQL tuning sets from the staging table into the database

execute dbms_sqltune.unpack_stgtab_sqlset(sqlset_name => '&stsname', -
                                          sqlset_owner => '&owner', -
                                          replace => TRUE, -
                                          staging_schema_owner=>'&stagingtab_owner',- 
                                          staging_table_name => '&stagingtab_name');
