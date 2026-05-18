-- Plug a PDB by cloning from an unplugged PDB (as clone method)

sqlplus / as sysdba

--- Create a clone of PDB1 using the manifest file generated during the unplug command (copy the original datafiles)
create pluggable database PDB1_clone as clone using '/home/oracle/PDB1.xml';

-- Plug the unplugged DB with nocopy method (reuse the datafiles)
create pluggable database PDB1_nocopy using '/home/oracle/PDB1.xml' NOCOPY TEMPFILE REUSE;

show pdbs

alter pluggable database PDB1_nocopy open read write;
alter pluggable database PDB1_CLONE open read write;

show pdbs

-- Now retrieve the datafiles names of PDB1_nocopy
alter session set container = PDB1_nocopy;

--- This query retrieves the PDB's datafile names
select file_name from dba_data_files;

--- Please write down these datafile names, as we will use them later on during the backup/restore lab.

--- Note that PDB GUID is used in the path to the datafiles
select GUID from v$pdbs;