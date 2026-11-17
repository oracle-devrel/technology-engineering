-- Deliberately separate, explicit cleanup. Run only when no test worker is active.
drop package ct_colocation_workload;
drop sequence ct_colocation_seq;
drop table ct_colocation_insert_log purge;
