-- Run as an ADB-D administrative user only when all test workers have stopped.
-- This permanently removes TEST_CTAG and every object it owns.
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode rollback
drop user TEST_CTAG cascade;
