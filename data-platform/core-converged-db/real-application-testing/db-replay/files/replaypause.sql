-- This procedure pauses the in-progress workload replay.

/* All subsequent user calls from the replay clients will be stalled until either a call to the RESUME_REPLAY Procedure is issued or the replay is cancelled.
This option enables you to temporarily stop the replay to perform a change and observe its impact for the remainder of the replay.
*/
execute DBMS_WORKLOAD_REPLAY.PAUSE_REPLAY ();
