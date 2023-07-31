## scripts-spa
This folder provides SQL scripts for the usage of SQL Performance Analyzer (SPA). They can be used to test changes on the same system or to run tests on a remote server.

Before you start with SQL Performance Analyzer, you need to provide a SQL Tuning Set. 
For more information see also:   
- [Github scripts for SQL Tuning Sets](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/sql-performance/sql-tuning-sets/scripts-for-sts)

Please note all SQL Performnace Analyzer tasks require the privilege ADVISOR.

## SQL Performance Analyzer Scripts
Please follow the steps in the suggested order. In step 2 you can choose between two test scenarios - on the same system or on a remote system. The tuning of regressed statements with SQL Plan Baselines at the end is optional.

1. Create and monitor the tuning task and executions
- Create a SPA task     : create-spa-task.sql
- Drop SPA task         : drop-spa-task.sql
- Monitor SPA task      : monitor-task.sql
- Monitor SPA executions: monitor-executions.sql
 
Scenario A: 
2. Execute trials on the same system
- Execute first trial : trial-execute.sql 
Change the system
- Execute second trial: trial-execute.sql  

Scenario B: 
2. Import STS on the remote system and use execution statistics for the first trial 
- Use the executions statistics for the first trial: trial-use-stats.sql
- Execute the trial (more than once is recommended): trial-execute.sql 


3. Generate the comparison results
- Compare performance of two executions: compare-performance.sql

4. Generate reports
- Generate summary report in HTML : report-summary.sql 
- Generate detailed report in HTML: report-all-details.sql


Optional: 
Tune regressed statements with SQL Plan Baselines
1. Create STS for regressed statements: create-sts-regressed.sql
2. Load original plans                : loadplans-for-regressed.sql

# License
Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
