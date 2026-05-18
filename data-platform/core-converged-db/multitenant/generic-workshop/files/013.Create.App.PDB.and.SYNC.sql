-- Create application PDBs and SYNC them with the application root

CREATE PLUGGABLE DATABASE north_app_pdb
ADMIN USER pdb_admin IDENTIFIED BY "Oracle_4U";

show pdbs

ALTER PLUGGABLE DATABASE north_app_pdb OPEN; 
show pdbs

conn sys/"Oracle_4U"@myoracledb:1521/north_app_pdb as sysdba 
set sqlprompt NORTH_APP_PDB>
desc sales_app_user.customers –- The table shoud not exist yet 
ALTER PLUGGABLE DATABASE APPLICATION sales_app SYNC;
SELECT con_id, name, open_mode, application_root app_root, application_pdb app_pdb, application_seed app_seed
from v$containers
order by con_id;
desc sales_app_user.customers –- Now the table should exist

conn sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba 
set sqlprompt SALES_APP_ROOT>
CREATE PLUGGABLE DATABASE east_app_pdb
ADMIN USER pdb_admin IDENTIFIED BY "Oracle_4U";
alter pluggable database east_app_pdb open; 
show pdbs

SELECT c.name, aps.con_uid, aps.app_name, aps.app_version, aps.app_status
FROM dba_app_pdb_status aps JOIN v$containers c
ON c.con_uid = aps.con_uid WHERE aps.app_name = 'SALES_APP';

-- We need to SYNC east_app_pdb
conn sys/"Oracle_4U"@myoracledb:1521/east_app_pdb as sysdba
set sqlprompt EAST_APP_PDB>

desc sales_app_user.customers
ERROR:
ORA-04043: object sales_app_user.customers does not exist

ALTER PLUGGABLE DATABASE APPLICATION sales_app SYNC;
desc sales_app_user.customers

-- Show the objects shared through the application root
select app.app_name, obj.owner, obj.object_name, obj.object_type, obj.sharing, obj.application
from dba_objects obj, dba_applications app where obj.owner in
(select username from dba_users where oracle_maintained = 'N')
and obj.application = 'Y'
and obj.created_appid = app.app_id;


