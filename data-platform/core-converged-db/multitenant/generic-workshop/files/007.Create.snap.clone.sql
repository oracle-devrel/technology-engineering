-- Create a snap clone on the refreshable PDB

-- On the PDB1_REFRESH PDB, used as a TEST MASTER, we create two sparse clones
-- Sparse techonoly 
-- Sparse datafiles clones are thin clones, that are sustained by the copy on write technology of the storage
-- Sparse clones creation is extremely fast, as pointers to the TEST MASTER are created, instead of physically cloning the TEST MASTER datafiles

sqlplus / as sysdba
show pdbs

create pluggable database PDB1_SNAP1 from PDB1_REFRESH snapshot copy; 
create pluggable database PDB1_SNAP2 from PDB1_REFRESH snapshot copy; 
alter pluggable database PDB1_SNAP1 open;
alter pluggable database PDB1_SNAP2 open;

show pdbs

-- Unlike their TEST MASTER, the snapshot copies are opened in read write, allowing users to create their own data.
-- Connect to PDB1_SNAP1, and run:

sqlplus TEST_REFRESH/Oracle_4U@myoracledb:1521/PDB1_SNAP1 
select * from tt;
insert into tt values (1000); 
commit;
select * from tt;

-- Now connect to PDB1_SNAP2 and check the TT table: 
sqlplus TEST_REFRESH/Oracle_4U@myoracledb:1521/PDB1_SNAP2 
select * from tt;

-- Only the data from the TEST MASTER is visible, not the data created in PDB1_SNAP1
delete tt;
insert into tt values (1001); 
commit;
select * from tt;

-- We can even modify (delete) the original data, without affecting the TEST MASTER: connect to the TEST MASTER and check:
sqlplus TEST_REFRESH/Oracle_4U@myoracledb:1521/PDB1_REFRESH 
select * from tt;

-- This illustrates the "copy on write" functionality
-- If we refresh the TEST MASTER, we will first drop the snapshot copies, and re-create them after the TEST MASTER refresh.