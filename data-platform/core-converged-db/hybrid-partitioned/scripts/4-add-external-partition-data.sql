REM Script: 4-add-external-partition-data.sql  
REM Use EXCHANGE PARTITION 

-- swap data segments to add (external) data to the partition 
ALTER TABLE hr.employees_hybrid
EXCHANGE PARTITION(salary_4000) WITH TABLE ext_help;

-- you can drop the external helper table EXT_HELP now
