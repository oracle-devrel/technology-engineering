-- Create a new PDB from an existing PDB

sqlplus / as sysdba
create pluggable database PDB1 from PDB1_nocopy;
alter pluggable database PDB1 open read write; 
show pdbs