-- This procedure applies a filter set to a capture in the current replay schedule.
-- The filter set must have been created by calling the CREATE_FILTER_SET Procedure.

execute DBMS_WORKLOAD_REPLAY.USE_FILTER_SET (filter_set => '&FILTERSET_NAME');

