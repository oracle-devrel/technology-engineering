-- This procedure puts the database state in PREPARE FOR REPLAY mode.

/*	  
DBMS_WORKLOAD_REPLAY.PREPARE_REPLAY (
   synchronization           IN VARCHAR2  DEFAULT 'SCN',
   connect_time_scale        IN NUMBER    DEFAULT 100,
   think_time_scale          IN NUMBER    DEFAULT 100,
   think_time_auto_correct   IN BOOLEAN   DEFAULT TRUE,
   scale_up_multiplier       IN NUMBER    DEFAULT 1,
   capture_sts               IN BOOLEAN   DEFAULT FALSE,
   sts_cap_interval          IN NUMBER    DEFAULT 300),
   rac_mode                  IN NUMBER    DEFAULT GLOBAL_SYNC,
   query_only                IN BOOLEAN   DEFAULT FALSE);

synchronization mode values for replay: 
'TIME' — The synchronization will be based on the time the action took place during capture (clock-based time).
'SCN' — The synchronization will be based on the capture-time commits; the commit order will be preserved during replay. This is the default mode.
*/

-- Default synchronization mode in 19c is SCN 
execute dbms_workload_replay.prepare_replay();


