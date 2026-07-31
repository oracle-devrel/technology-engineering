-- PDB Backup and restore

rman target=/

BACKUP PLUGGABLE DATABASE PDB1_NOCOPY;
exit

--- Remove a datafile from the operating system: change the file name by your file name !!!
--- You need to use the file name for tablespace SYSTEM, as returned previously in page 6 

rm /opt/oracle/oradata/ORCLCDB/CDADC32D998ECE2AE053E414010AA42A/datafile/o1_mf_sys tem_jotz78l7_.dbf

--- Connect to the PDB
sqlplus system/Oracle_4U@myoracledb:1521/PDB1_NOCOPY

-- This fails !!!

ORA-27041: unable to open
Linux-x86_64 Error: 2: No
Additional information: 3
ORA-00604: error occurred
ORA-01116: error in opening database file 19
ORA-01110: data file 19: '/opt/oracle/oradata/ORCLCDB/CDADC32D998ECE2AE053E414010AA42A/datafile/o1_mf_sy s
tem_jotz78l7_.dbf'
ORA-27041: unable to open file
Linux-x86_64 Error: 2: No such file or directory Additional information: 3

--- Ensure datafile ID (19) matches with your environment

rman target=/

RUN {
alter pluggable database PDB1_NOCOPY close immediate; 
RESTORE datafile 19;
RECOVER PLUGGABLE DATABASE PDB1_NOCOPY;
ALTER PLUGGABLE DATABASE PDB1_NOCOPY open;
}

--- Check that the PDB is now sucessufully opened and accessible
sqlplus / as sysdba
show pdbs

sqlplus system/Oracle_4U@myoracledb:1521/PDB1_NOCOPY