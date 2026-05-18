-- Create an application root

sqlplus / as sysdba 
set sqlprompt CDB$ROOT>
CDB$ROOT> set linesize 1000

col app_name format a30
col name format a20
SELECT con_id, name, open_mode, application_root app_root,
application_pdb app_pdb, application_seed app_seed from v$containers
         order by con_id;


--- Create an application container: this is a special PDB
CREATE PLUGGABLE DATABASE sales_app_root AS APPLICATION CONTAINER ADMIN USER appadmin IDENTIFIED BY "Oracle_4U";
SELECT con_id, name, open_mode, application_root app_root, application_pdb app_pdb, application_seed app_seed
         from v$containers
         order by con_id;

alter pluggable database sales_app_root open; 
show pdbs
