sqlplus / as sysdba
alter pluggable database all close;

show pdbs

drop pluggable database PDB1_SNAP2 including datafiles; 
drop pluggable database PDB1_SNAP1 including datafiles; 
drop pluggable database PDB1_REFRESH including datafiles; 
drop pluggable database PDB1_NOCOPY including datafiles; 
drop pluggable database PDB1_CLONE including datafiles; 
drop pluggable database PDB1 including datafiles;
alter pluggable database ORCLPDB1 open;

show pdbs