-- This procedure starts the workload replay.
-- The call to the PREPARE_REPLAY Procedure was already issued.
-- A sufficient number of external replay clients (WRC) that can faithfully replay the captured workload already started. 

execute dbms_workload_replay.start_replay();
