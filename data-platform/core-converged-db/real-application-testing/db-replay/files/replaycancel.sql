-- This procedure cancels workload replay in progress. All the external replay clients (WRC) will automatically be notified to stop issuing the captured workload and exit.

execute DBMS_WORKLOAD_REPLAY.CANCEL_REPLAY();