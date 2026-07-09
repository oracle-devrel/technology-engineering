REM Script: 2-add-external-attribute.sql
REM Use ALTER TABLE 

-- enter directory name
ALTER TABLE hr.employees_hybrid 
ADD EXTERNAL PARTITION ATTRIBUTES
   ( TYPE oracle_datapump 
     DEFAULT DIRECTORY &directoryname 
     REJECT LIMIT UNLIMITED );

