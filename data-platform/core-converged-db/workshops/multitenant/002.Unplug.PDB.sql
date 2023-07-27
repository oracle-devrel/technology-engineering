-- Unplug a PDB from its CDB

--- First we connect to the CDB. 

sqlplus / as sysdba

show pdbs

alter pluggable database PDB1 close immediate;
alter pluggable database PDB1 unplug into '/home/oracle/PDB1.xml';
drop pluggable database PDB1 keep datafiles; 

show pdbs