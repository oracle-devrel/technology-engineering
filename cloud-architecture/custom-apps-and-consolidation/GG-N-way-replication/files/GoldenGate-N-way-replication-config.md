###### Copyright (c) 2023, Oracle and/or its affiliates.
###### Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
###### Purpose: Configuration files for GG N-way replication best practice.
###### @author: Saravanadurai Rajendran & Divya Batra


# Parameter files for GG in Region1:

###### EXTRACT EXT1 (Extract for bi-directional between Region1 DBCS and Region2 DBCS)

EXTRACT EXT1
USERIDALIAS cdbregion1 DOMAIN OracleGoldenGate
EXTTRAIL E1
-- Capture DDL operations for listed schema tables
ddl include mapped

-- Add step-by-step history
-- to the report file. Very useful when troubleshooting.
ddloptions report

-- Write capture stats per table to the report file daily.
report at 00:01

-- Rollover the report file weekly. Useful when IE runs
-- without being stopped/started for long periods of time to
-- keep the report files from becoming too large.
reportrollover at 00:01 on Sunday

-- Report total operations captured, and operations per second
-- every 10 minutes.
reportcount every 10 minutes, rate
tranlogoptions excludeuser REGION1_PDB1.ggadmin
-- Included schemas
TABLE REGION1_PDB1.<<Schema>>.*;


##### EXTRACT EXT2 (Extract for uni-directional replication between Region1 DBCS and Region1 ADW)


EXTRACT EXT2
USERIDALIAS cdbregion1 DOMAIN OracleGoldenGate
EXTTRAIL E2
reportcount every 15 minutes, rate
DDL INCLUDE MAPPED
ddloptions report
-- Included schemas
TABLE REGION1_PDB1.<<Schema>>.*;


##### REPLICAT REP1 (Replicat for bi-directional between Region1 DBCS and Region2 DBCS)


REPLICAT REP1
USERIDALIAS pdbregion2 DOMAIN OracleGoldenGate
reportcount every 15 minutes, rate
DBOPTIONS INTEGRATEDPARAMS(parallelism 2)
DDL INCLUDE MAPPED
MAP REGION1_PDB1.<<Schema>>.*,  TARGET REGION2_PDB1.<<Schema>>.*;


##### REPLICAT REP2 (Replicat for uni-directional replication between Region1 DBCS and Region1 ADW)

REPLICAT REP2
USERIDALIAS adwregion1 DOMAIN OracleGoldenGate
reportcount every 15 minutes, rate
DDL INCLUDE MAPPED
MAP REGION1_PDB1.<<Schema>>.*, TARGET .<<Schema>>.*;


# Parameter files for GG in Region2:

##### EXTRACT EXT3 (Extract for bi-directional between Region2 DBCS and Region1 DBCS)


EXTRACT EXT3
USERIDALIAS cdbregion2 DOMAIN OracleGoldenGate
EXTTRAIL E3
-- Capture DDL operations for listed schema tables
ddl include mapped

-- Add step-by-step history
-- to the report file. Very useful when troubleshooting.
ddloptions report

-- Write capture stats per table to the report file daily.
report at 00:01

-- Rollover the report file weekly. Useful when IE runs
-- without being stopped/started for long periods of time to
-- keep the report files from becoming too large.
reportrollover at 00:01 on Sunday

-- Report total operations captured, and operations per second
-- every 10 minutes.
reportcount every 10 minutes, rate
tranlogoptions excludeuser REGION2_PDB1.ggadmin
-- Included schemas
TABLE REGION2_PDB1.<<Schema>>.*;


##### EXTRACT EXT4 (Extract for uni-directional replication between Region2 DBCS and Region2 ADW)


EXTRACT EXT4
USERIDALIAS cdbregion2 DOMAIN OracleGoldenGate
EXTTRAIL E4
reportcount every 15 minutes, rate
DDL INCLUDE MAPPED
-- Included schemas
TABLE REGION2_PDB1.<<Schema>>.*;




##### REPLICAT REP3 (Replicat for bi-directional between Region2 DBCS and Region1 DBCS)

REPLICAT REP3
USERIDALIAS pdbregion1 DOMAIN OracleGoldenGate
reportcount every 15 minutes, rate
DBOPTIONS INTEGRATEDPARAMS(parallelism 2)
DDL INCLUDE MAPPED
MAP REGION2_PDB1.<<Schema>>.*, TARGET REGION1_PDB1.<<Schema>>.*;


##### REPLICAT REP4 (Replicat for uni-directional replication between Region2 DBCS and Region2 ADW)

REPLICAT REP4
USERIDALIAS adwregion2 DOMAIN OracleGoldenGate
reportcount every 15 minutes, rate
DDL INCLUDE MAPPED
MAP REGION2_PDB1.<<Schema.*, TARGET <<Schema>>.*;
