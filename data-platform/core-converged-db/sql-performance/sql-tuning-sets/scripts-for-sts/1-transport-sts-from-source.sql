REM Script: 1-transport-sts-from-source.sql
REM Create a staging table and add the statements to it (source system) 

-- don't use SYS user for this  
-- Use CREATE_STGTAB_SQLSET to create the staging table

execute dbms_sqltune.create_stgtab_sqlset(table_name => '&tablename', schema_name => '&owner');

-- Load the staging table with data from one or more STS with PACK_STGTAB_SQLSET

execute dbms_sqltune.pack_stgtab_sqlset(sqlset_name => '&stsname', -
                                        sqlset_owner => '&owner', -
                                        staging_table_name => '&stagingtab_name',- 
                                        staging_schema_owner=> '&stagingtab_owner');


-- use datapump to export the staging table and import it to the target system
