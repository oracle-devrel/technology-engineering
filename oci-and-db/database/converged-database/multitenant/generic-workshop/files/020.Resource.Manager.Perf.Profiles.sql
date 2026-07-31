-- Resource manager PDB performance profiles

--- Connect to the CDB and create a new plan
sqlplus / as sysdba

DECLARE
  l_plan VARCHAR2(30) := 'CDB_PDB_PROFILE';
BEGIN
  DBMS_RESOURCE_MANAGER.clear_pending_area;
  DBMS_RESOURCE_MANAGER.create_pending_area;

  DBMS_RESOURCE_MANAGER.create_cdb_plan(
    plan    => l_plan,
    comment => 'A test CDB resource plan using PDB profiles');

  DBMS_RESOURCE_MANAGER.create_cdb_profile_directive(
    plan                  => l_plan,
    profile               => 'GOLD',
    shares                => 3,
    utilization_limit     => 100,
    parallel_server_limit => 100);

  DBMS_RESOURCE_MANAGER.create_cdb_profile_directive(
    plan                  => l_plan,
    profile               => 'SILVER',
    shares                => 2,
    utilization_limit     => 50,
    parallel_server_limit => 50);

  DBMS_RESOURCE_MANAGER.validate_pending_area;
  DBMS_RESOURCE_MANAGER.submit_pending_area;
END;
/
--- Check the new plan

COLUMN plan FORMAT A30
COLUMN comments FORMAT A30
COLUMN status FORMAT A10
SET LINESIZE 100

SELECT plan_id,
       plan,
       comments,
       status,
       mandatory
FROM dba_cdb_rsrc_plans
WHERE plan = 'CDB_PDB_PROFILE';

COLUMN plan FORMAT A30
COLUMN pluggable_database FORMAT A25 
COLUMN profile FORMAT A25
SET LINESIZE 150 VERIFY OFF

SELECT plan, pluggable_database,
profile,
shares,
utilization_limit AS util, parallel_server_limit AS parallel
FROM dba_cdb_rsrc_plan_directives
WHERE plan = 'CDB_PDB_PROFILE'
ORDER BY plan, pluggable_database, profile;

-- Now we will add a new PDB profile, called BRONZE, to our plan

DECLARE
  l_plan VARCHAR2(30) := 'CDB_PDB_PROFILE';
BEGIN
  DBMS_RESOURCE_MANAGER.clear_pending_area;
  DBMS_RESOURCE_MANAGER.create_pending_area;

  DBMS_RESOURCE_MANAGER.create_cdb_profile_directive(
    plan                  => l_plan,
    profile               => 'BRONZE',
    shares                => 1,
    utilization_limit     => 25,
    parallel_server_limit => 25);

  DBMS_RESOURCE_MANAGER.validate_pending_area;
  DBMS_RESOURCE_MANAGER.submit_pending_area;
END;
/

--- Check your plan directives
COLUMN plan FORMAT A30
COLUMN pluggable_database FORMAT A25
COLUMN profile FORMAT A25
SET LINESIZE 150 VERIFY OFF

SELECT plan,
       pluggable_database,
       profile,
       shares,
       utilization_limit AS util,
       parallel_server_limit AS parallel
FROM   dba_cdb_rsrc_plan_directives
WHERE  plan = 'CDB_PDB_PROFILE'
ORDER BY plan, pluggable_database, profile;

DECLARE
  l_plan VARCHAR2(30) := 'CDB_PDB_PROFILE';
BEGIN
  DBMS_RESOURCE_MANAGER.clear_pending_area;
  DBMS_RESOURCE_MANAGER.create_pending_area;

  DBMS_RESOURCE_MANAGER.update_cdb_profile_directive(
    plan                      => l_plan,
    profile                   => 'bronze',
    new_shares                => 1,
    new_utilization_limit     => 20,
    new_parallel_server_limit => 20);

  DBMS_RESOURCE_MANAGER.validate_pending_area;
  DBMS_RESOURCE_MANAGER.submit_pending_area;
END;
/


--- Now we can assign a profile to a PDB
--- Connect to ORCLPDB1 and check its profile
alter session set container=ORCLPDB1;

show parameter DB_PERFORMANCE_PROFILE


--- This is NULL by default, meaning that ORA$DEFAULT_PDB_DIRECTIVE has been applied to that PDB. Change the PDB profile to GOLD:

ALTER SYSTEM SET DB_PERFORMANCE_PROFILE=gold SCOPE=SPFILE;
ALTER PLUGGABLE DATABASE CLOSE IMMEDIATE;
ALTER PLUGGABLE DATABASE OPEN;
SHOW PARAMETER DB_PERFORMANCE_PROFILE


--- Create a new PDB

connect / as sysdba
create pluggable database ORCLPDB2 from ORCLPDB1;
alter pluggable database ORCLPDB2 open;

show pdbs

-- Connect to ORCLPDB2 and check its profile

alter session set container = ORCLPDB2;
SHOW PARAMETER DB_PERFORMANCE_PROFILE

--- This was inherited from the source database, but might be changed:
ALTER SYSTEM SET DB_PERFORMANCE_PROFILE=bronze SCOPE=SPFILE;
ALTER PLUGGABLE DATABASE CLOSE IMMEDIATE;
ALTER PLUGGABLE DATABASE OPEN;


SHOW PARAMETER DB_PERFORMANCE_PROFILE

--- For the plan to be active, we need to enable it at CDB level

connect / as sysdba
ALTER SYSTEM SET RESOURCE_MANAGER_PLAN = 'CDB_PDB_PROFILE';

