-- Create a new PDB in the container database (CDB)

sqlplus / as sysdba
create pluggable database PDB1 admin user pdbadmin identified by "Oracle_4U"; 

show pdbs

alter pluggable database PDB1 open read write;

show pdbs