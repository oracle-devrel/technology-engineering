# Transactions & Concurrency — run order (v6.1)

1. Admin: open `transactions_concurrency_demo_config.sqlnb` in the target PDB. Capture original values; execute ALTER SYSTEM only if allowed and appropriate. On ADB Free, skip if rejected.
2. Sessions 1 and 2: run the opening session-ID queries and confirm different IDs. Session 1 then runs Setup and S1-A1.
3. Session 2: connect as the same schema **in an independent session** and run S2-A1 (expected rejected reservation).
4. Session 1: S1-A2 commit; Session 2: S2-A2 inspect.
5. Reconfirm session IDs at the start of section B in both notebooks. Session 1: S1-B1 then S1-B2 suspend; Session 2: S2-B1 resume then S2-B2 commit; Session 1: S1-B3 verify.
6. **Only if configured:** Set and display each session priority (Session 1 LOW, Session 2 HIGH), then Session 1 S1-C1 locks the row; Session 2 S2-C1 updates as HIGH (may wait); Session 2 S2-C2 commit; Session 1 S1-C2 observe rollback error, S1-C3 acknowledge with ROLLBACK.
7. Close active transactions. Run `transactions_concurrency_cleanup.sql` as demo schema. If ALTER SYSTEM was used, run `transactions_concurrency_admin_cleanup.sql` in the original PDB, entering the **captured original values**.

Do not mix Lock-Free Reservations with the priority lock conflict. Oracle documents Priority Transactions as a no-op for transactions consisting only of lock-free reservations.

The two-session transaction examples have been successfully exercised on the presenter's ADB Free instance (Lock-Free Reservations, Sessionless Transactions, Transaction Priorities). The GraphQL Duality View comparison has not yet been confirmed by a reported runtime test. Confirm the notebook extension preserves separate physical connections, does not autocommit DML, and supports the target release's GraphQL mapping syntax before presenting live.


**Priority rollback acknowledgment:** After Session 1 observes `ORA-63302`/`ORA-63300`, execute the final `ROLLBACK` in Session 1. Oracle has already undone the transaction; this acknowledges that outcome and clears the session state. No session-priority reset is required for the demonstration.
