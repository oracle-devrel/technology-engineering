REM  Script for 23c: automatic-transaction-rollback-v$transaction.sql
REM  Check V$TRANSACTION with new columns TXN_PRIORITY and TXN_PRIORITY_WAIT_TARGET to mointor session settings for automatic rollback transaction

select txn_priority, txn_priority_wait_target from v$transaction;
