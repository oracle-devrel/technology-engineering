## Database Replay Scripts

This folder provides SQL scripts for the usage of Database Replay (DB Replay). Please adapt and change the scripts to your conditions. 

## Scripts

You can find an example workflow, the executed scripts, and a detailed description in the posting [Testing with Oracle Database Replay](https://blogs.oracle.com/coretec/post/testing-with-oracle-database-replay).

Keep in mind that appropriate permissions are required to
- Create directory objects
- Use DBMS_WORKLOAD_CAPTURE and DBMS_WORKLOAD_REPLAY packages
- Act as a replay client user (e.g. wrc someuser/YOUR_PASSWORD or wrc USER=someuser PASSWORD=YOUR_PASSWORD) //PLEASE CHANGE YOUR_PASSWORD  TO A REAL PASSWORD!
 
In the documentation [DBMS_WORKLOAD_CAPTURE Security Model]( https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_WORKLOAD_CAPTURE.html#GUID-77C6507C-3DE6-4FB4-B180-530BEB840BE8) you will get the detailed information about it.

Before starting a workload capture, you should have a strategy in place to restore the database on the test system. Before a workload can be replayed, the logical state of the application data on the replay system should be similar to that of the capture system when replay begins.

In general, please follow the suggested script order.

### 1) Capture the Database Workload in the production environment 

Before starting, check the [Workload Capture restrictions](https://docs.oracle.com/en/database/oracle/oracle-database/19/ratug/capturing-a-database-workload.html#GUID-4A1995F1-78F9-4080-8DFC-1E3EBCB3F4B8).

- Provide an empty database directory 
- (optional) Use filters: capturefilter.sql 
- Start capture: capturestart.sql
- (optional) Stop capture: capturestop.sql
- Check capture results: capturemon.sql
- Export AWR: exportawr.sql
- Capture report: capturereport.sql

(Note: it may be useful to generate an additional AWR spanning the capture period.) 

### 2) Preprocess the (captured) Database Workload on the test environment  

- Preprocess: processcapture.sql
- (optional) Check duration: processmonitor.sql

### 3) Replay the Database Workload on the test environment

- (optional) Add filters: replayfilter.sql and replayfilterset.sql 
- Initialize the replay: replayinitialize.sql
- (optional) Map connections: remapping.sql
- (optional) Use filters: replayusefilterset.sql 
- Prepare the replay: replayprepare.sql

- Workload Replay clients: Number estimation and start

Estimate the number of Workload Replay Clients (WRCs) (e.g. $wrc mode=calibrate replaydir=../replay/..) 

Start WRCs in the background on the replay machine or a separate machine (e.g. $wrc username/password mode=replay replaydir=../replay/...)

- Start the replay: replaystart.sql
- Monitor the replay: replaymon.sql

### 4) Generate Reports
 
- (optional) Divergence reports: divergences.sql, divergence_detail.sql
- Replay report: replayreport.sql
- Import capture AWRs: importAWR.sql
- ComparePeriod report: comparereplayreport.sql 
(Note: it may be useful to generate an additional AWR spanning the replay period.) 

### 5) Debug Database Replay (optional, only in the case you discover slow replays)
- debug slow replay in dba_alert_history: debug_slow_replay_alert.sql
- debug WRC sessions with gv$workload_replay_thread and gv$session: debug_wrc_sessions.sql
- debug wrc waits with gv$workload_replay_thread: debug_wrc_wait.sql
- debug slow replay info report: debug_slow_replay_info.sql
- monitoring report using dbms_wrr_report (see also Database Replay monitor report (dbms_wrr_report) (Doc ID 2696765.1)): monitor_with_dbms_wrr_report.sql

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
